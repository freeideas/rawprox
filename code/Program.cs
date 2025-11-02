using System;
using System.Buffers;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Runtime.Loader;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    private static readonly ConcurrentDictionary<int, TcpListener> _listeners = new();
    private static readonly ConcurrentDictionary<string, LogDestination> _logDestinations = new();
    private static readonly ConcurrentQueue<string> _logQueue = new();
    private static readonly Random _random = new();
    private static TcpListener? _mcpListener;
    private static int _mcpPort;
    private static int _flushMillis = 2000;
    private static CancellationTokenSource _cts = new();
    private static bool _shutdownComplete = false;

    // P/Invoke for direct console I/O
    [System.Runtime.InteropServices.DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr GetStdHandle(int nStdHandle);

    [System.Runtime.InteropServices.DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool WriteFile(IntPtr hFile, byte[] lpBuffer, uint nNumberOfBytesToWrite, out uint lpNumberOfBytesWritten, IntPtr lpOverlapped);

    static async Task<int> Main(string[] args)
    {
        // $REQ_STDOUT_004: Ensure console output is not lost on termination
        Console.SetOut(new System.IO.StreamWriter(Console.OpenStandardOutput()) { AutoFlush = true });

        bool mcpMode = false;
        var portRules = new List<PortRule>();
        var logDirs = new List<string>();
        string filenameFormat = "rawprox_%Y-%m-%d-%H.ndjson";

        // Parse arguments
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--mcp")
            {
                mcpMode = true;
            }
            else if (args[i] == "--flush-millis" && i + 1 < args.Length)
            {
                _flushMillis = int.Parse(args[++i]);
            }
            else if (args[i] == "--filename-format" && i + 1 < args.Length)
            {
                filenameFormat = args[++i];
            }
            else if (args[i].StartsWith("@"))
            {
                logDirs.Add(args[i].Substring(1));
            }
            else if (TryParsePortRule(args[i], out var rule))
            {
                portRules.Add(rule);
            }
            else
            {
                // $REQ_ARGS_012: Validate port rule format and show error
                Console.Error.WriteLine($"Error: Invalid argument: {args[i]}");
                return 1;
            }
        }

        // $REQ_ARGS_001, $REQ_ARGS_007: Show usage and exit when no args and no --mcp
        // Do this BEFORE starting logging to avoid NDJSON output on STDOUT
        if (portRules.Count == 0 && !mcpMode)
        {
            Console.Error.WriteLine("Usage: rawprox [--mcp] [PORT_RULE...] [LOG_DESTINATION...]");
            return 1;
        }

        // $REQ_MCP_023, $REQ_MCP_026: Start logging BEFORE MCP server (so start-mcp event can be logged)
        bool hasPortRules = portRules.Count > 0;

        // $REQ_FILE_025, $REQ_MCP_023: Start logging - STDOUT is always active, directories are additional
        // Start directory destinations first (so start-logging events with filename_format appear first)
        foreach (var dir in logDirs)
        {
            StartLogging(dir, filenameFormat);
        }

        // Then start STDOUT destination (always active)
        StartLogging(null, null);

        // Flush start-logging events immediately
        FlushAllLogsSync();

        // Start flush task
        _ = Task.Run(FlushLoop);

        // $REQ_MCP_023, $REQ_MCP_026, $REQ_MCP_028: Start MCP server after logging starts
        if (mcpMode)
        {
            _mcpPort = GetRandomPort();
            _mcpListener = new TcpListener(IPAddress.Loopback, _mcpPort);
            _mcpListener.Start();

            // $REQ_MCP_004, $REQ_MCP_028: Emit start-mcp event through logging system
            LogEvent(new LogEventStartMcp { time = GetTimestamp(), port = _mcpPort });
            FlushAllLogsSync();

            _ = Task.Run(AcceptMcpConnections);
        }

        if (portRules.Count == 0 && mcpMode)
        {
            // $REQ_ARGS_002: Show usage but keep running when --mcp without port rules
            Console.Error.WriteLine("Usage: rawprox [--mcp] [PORT_RULE...] [LOG_DESTINATION...]");
            Console.Error.WriteLine("RawProx started in MCP mode. Use JSON-RPC to add port rules.");
        }

        foreach (var rule in portRules)
        {
            // $REQ_STARTUP_005: Exit with error if port binding fails
            if (!StartPortRule(rule))
            {
                return 1;
            }
        }

        // Wait for cancellation
        Console.CancelKeyPress += (s, e) =>
        {
            e.Cancel = true;
            _cts.Cancel();
        };

        // $REQ_SHUTDOWN_004, $REQ_SHUTDOWN_018: Handle process termination to emit stop-logging events
        // Use both AssemblyLoadContext.Unloading (more reliable with Native AOT) and ProcessExit
        var shutdownHandler = () =>
        {
            if (_shutdownComplete) return;  // Already handled in normal shutdown

            try
            {
                // $REQ_FILE_009: Write stop-logging events directly to files
                // Don't use queue - write immediately for best chance of success
                foreach (var dest in _logDestinations.Keys.ToList())
                {
                    var evt = new LogEventStopLogging { time = GetTimestamp(), directory = dest == "stdout" ? null : dest };
                    string json = JsonSerializer.Serialize(evt, JsonContext.Default.LogEventStopLogging) + "\n";

                    if (dest == "stdout")
                    {
                        // Write to stdout
                        try
                        {
                            var handle = GetStdHandle(-11); // STD_OUTPUT_HANDLE
                            if (handle != IntPtr.Zero)
                            {
                                var bytes = Encoding.UTF8.GetBytes(json);
                                WriteFile(handle, bytes, (uint)bytes.Length, out _, IntPtr.Zero);
                            }
                        }
                        catch { }
                    }
                    else
                    {
                        // Write to file
                        try
                        {
                            var filename = FormatFilename(_logDestinations[dest].FilenameFormat ?? "rawprox_%Y-%m-%d-%H.ndjson");
                            var path = Path.Combine(dest, filename);
                            File.AppendAllText(path, json);
                        }
                        catch { }
                    }
                }

                // Also flush any pending logs from the queue
                FlushAllLogsSync();
            }
            catch
            {
                // Ignore all errors - process is terminating
            }
        };

        // Register shutdown handler for both events
        AssemblyLoadContext.Default.Unloading += (ctx) => shutdownHandler();
        AppDomain.CurrentDomain.ProcessExit += (s, e) => shutdownHandler();

        try
        {
            await Task.Delay(-1, _cts.Token);
        }
        catch (TaskCanceledException) { }

        // Cleanup
        foreach (var listener in _listeners.Values)
        {
            listener.Stop();
        }

        // $REQ_SHUTDOWN_004: Emit stop-logging events before shutdown
        foreach (var dest in _logDestinations.Keys.ToList())
        {
            LogEvent(new LogEventStopLogging { time = GetTimestamp(), directory = dest == "stdout" ? null : dest });
        }

        await FlushAllLogs();

        // Also flush in ProcessExit handler in case we're terminated
        _shutdownComplete = true;

        return 0;
    }

    private static bool TryParsePortRule(string s, out PortRule rule)
    {
        rule = default;
        var parts = s.Split(':');
        if (parts.Length != 3) return false;
        if (!int.TryParse(parts[0], out int localPort)) return false;
        if (!int.TryParse(parts[2], out int targetPort)) return false;
        rule = new PortRule(localPort, parts[1], targetPort);
        return true;
    }

    private static bool StartPortRule(PortRule rule)
    {
        try
        {
            var listener = new TcpListener(IPAddress.Any, rule.LocalPort);
            listener.Start();
            _listeners[rule.LocalPort] = listener;
            _ = Task.Run(() => AcceptConnections(listener, rule));
            return true;
        }
        catch (Exception ex)
        {
            // $REQ_STARTUP_005: Show error indicating which port is occupied
            Console.Error.WriteLine($"Failed to start listener on port {rule.LocalPort}: {ex.Message}");
            return false;
        }
    }

    private static async Task AcceptConnections(TcpListener listener, PortRule rule)
    {
        while (!_cts.Token.IsCancellationRequested)
        {
            try
            {
                var client = await listener.AcceptTcpClientAsync();
                _ = Task.Run(() => HandleConnection(client, rule));
            }
            catch { break; }
        }
    }

    // $REQ_PROXY_001 $REQ_PROXY_002 $REQ_PROXY_003: Accept connections, connect to target, forward bidirectionally
    private static async Task HandleConnection(TcpClient client, PortRule rule)
    {
        string connId = GenerateConnId();
        TcpClient? target = null;

        try
        {
            // $REQ_PROXY_002: Connect to target
            target = new TcpClient();
            await target.ConnectAsync(rule.TargetHost, rule.TargetPort);

            var clientEp = client.Client.RemoteEndPoint?.ToString() ?? "unknown";
            var targetEp = $"{rule.TargetHost}:{rule.TargetPort}";

            // $REQ_PROXY_013: Serialize events to JSON and append to memory buffer
            var ts = GetTimestamp();
            LogEvent(new LogEventOpen { time = ts, timestamp = ts, ConnID = connId, from = clientEp, to = targetEp });

            var clientStream = client.GetStream();
            var targetStream = target.GetStream();

            // $REQ_PROXY_004 $REQ_PROXY_005 $REQ_PROXY_006 $REQ_PROXY_007: Zero-copy forwarding, never block network I/O
            var clientToTarget = Task.Run(async () =>
            {
                byte[] buffer = ArrayPool<byte>.Shared.Rent(65536);
                try
                {
                    int read;
                    while ((read = await clientStream.ReadAsync(buffer, 0, buffer.Length)) > 0)
                    {
                        // $REQ_PROXY_004: Zero-copy forwarding - write to network without copying
                        await targetStream.WriteAsync(buffer, 0, read);

                        // $REQ_PROXY_005 $REQ_PROXY_011 $REQ_PROXY_013: Logging never blocks
                        // Convert buffer slice to string immediately (unavoidable for JSON serialization)
                        // Fire-and-forget - no blocking in network path
                        LogTrafficAsync(connId, buffer.AsMemory(0, read), clientEp, targetEp);
                    }
                }
                catch (Exception)
                {
                    // Connection error in client->target direction
                }
                finally
                {
                    ArrayPool<byte>.Shared.Return(buffer);
                }
            });

            var targetToClient = Task.Run(async () =>
            {
                byte[] buffer = ArrayPool<byte>.Shared.Rent(65536);
                try
                {
                    int read;
                    while ((read = await targetStream.ReadAsync(buffer, 0, buffer.Length)) > 0)
                    {
                        // $REQ_PROXY_004: Zero-copy forwarding - write to network without copying
                        await clientStream.WriteAsync(buffer, 0, read);

                        // $REQ_PROXY_005 $REQ_PROXY_011 $REQ_PROXY_013: Logging never blocks
                        // Convert buffer slice to string immediately (unavoidable for JSON serialization)
                        // Fire-and-forget - no blocking in network path
                        LogTrafficAsync(connId, buffer.AsMemory(0, read), targetEp, clientEp);
                    }
                }
                catch (Exception)
                {
                    // Connection error in target->client direction
                }
                finally
                {
                    ArrayPool<byte>.Shared.Return(buffer);
                }
            });

            // $REQ_PROXY_003: Wait for one direction to complete
            var completed = await Task.WhenAny(clientToTarget, targetToClient);

            // Close the socket that finished to signal EOF to the other side
            if (completed == clientToTarget)
            {
                // Client closed - close target to signal EOF
                try { target.Client.Shutdown(SocketShutdown.Send); } catch { }
            }
            else
            {
                // Target closed - close client to signal EOF
                try { client.Client.Shutdown(SocketShutdown.Send); } catch { }
            }

            // Wait for the other direction to complete (with timeout)
            var remaining = completed == clientToTarget ? targetToClient : clientToTarget;
            await Task.WhenAny(remaining, Task.Delay(5000));

            var closeTs = GetTimestamp();
            LogEvent(new LogEventClose { time = closeTs, timestamp = closeTs, ConnID = connId, from = targetEp, to = clientEp });
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Connection error: {ex.Message}");
        }
        finally
        {
            client?.Close();
            target?.Close();
        }
    }

    // $REQ_PROXY_005 $REQ_PROXY_011: Non-blocking logging - fire and forget
    private static void LogTrafficAsync(string connId, ReadOnlyMemory<byte> buffer, string from, string to)
    {
        // $REQ_PROXY_004 $REQ_PROXY_005: Copy buffer to avoid holding reference to pooled array
        // ToArray() is O(n) memory copy but necessary since buffer will be reused
        byte[] copy = buffer.ToArray();

        // $REQ_PROXY_005 $REQ_PROXY_007: Fire-and-forget - ALL processing in background thread
        _ = Task.Run(() =>
        {
            // $REQ_PROXY_005 $REQ_PROXY_006 $REQ_PROXY_007: UTF-8 decode happens in background, not in network path
            var data = Encoding.UTF8.GetString(copy);
            // $REQ_PROXY_011 $REQ_PROXY_013: JSON serialization and memory buffering
            var dataTs = GetTimestamp();
            LogEvent(new LogEventData { time = dataTs, timestamp = dataTs, ConnID = connId, data = data, from = from, to = to });
        });
    }

    private static string GenerateConnId()
    {
        const string chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
        var sb = new StringBuilder(5);
        for (int i = 0; i < 5; i++)
        {
            sb.Append(chars[_random.Next(chars.Length)]);
        }
        return sb.ToString();
    }

    private static string GetTimestamp()
    {
        return DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ");
    }

    private static int GetRandomPort()
    {
        return _random.Next(10000, 65500);
    }

    // $REQ_PROXY_011 $REQ_PROXY_013: Events serialized to JSON and buffered in memory
    private static void LogEvent(object evt)
    {
        // $REQ_PROXY_013: Serialize to JSON
        string json = evt switch
        {
            LogEventStartMcp e => JsonSerializer.Serialize(e, JsonContext.Default.LogEventStartMcp),
            LogEventStartLogging e => JsonSerializer.Serialize(e, JsonContext.Default.LogEventStartLogging),
            LogEventStartLoggingStdout e => JsonSerializer.Serialize(e, JsonContext.Default.LogEventStartLoggingStdout),
            LogEventStopLogging e => JsonSerializer.Serialize(e, JsonContext.Default.LogEventStopLogging),
            LogEventOpen e => JsonSerializer.Serialize(e, JsonContext.Default.LogEventOpen),
            LogEventClose e => JsonSerializer.Serialize(e, JsonContext.Default.LogEventClose),
            LogEventData e => JsonSerializer.Serialize(e, JsonContext.Default.LogEventData),
            _ => throw new InvalidOperationException($"Unknown event type: {evt.GetType()}")
        };
        // $REQ_PROXY_011: Buffer in memory (unbounded queue - will OOM if full)
        // $REQ_PROXY_012: If buffer fills, C# runtime will throw OutOfMemoryException
        _logQueue.Enqueue(json);
    }

    private static void StartLogging(string? directory, string? filenameFormat)
    {
        var dest = new LogDestination { Directory = directory, FilenameFormat = filenameFormat };
        _logDestinations[directory ?? "stdout"] = dest;

        if (directory == null)
        {
            LogEvent(new LogEventStartLoggingStdout { time = GetTimestamp(), directory = null });
        }
        else
        {
            LogEvent(new LogEventStartLogging { time = GetTimestamp(), directory = directory, filename_format = filenameFormat ?? "" });
        }
    }

    private static void StopLogging(string? directory)
    {
        _logDestinations.TryRemove(directory ?? "stdout", out _);
        LogEvent(new LogEventStopLogging { time = GetTimestamp(), directory = directory });
    }

    // $REQ_PROXY_014: Buffer flush at configurable intervals
    private static async Task FlushLoop()
    {
        while (!_cts.Token.IsCancellationRequested)
        {
            // $REQ_PROXY_014: Flush at intervals (default 2000ms)
            await Task.Delay(_flushMillis);
            await FlushAllLogs();
        }
    }

    // $REQ_PROXY_014 $REQ_PROXY_015: Background disk writes, events appear only after flush
    private static async Task FlushAllLogs()
    {
        if (_logQueue.IsEmpty) return;

        // $REQ_PROXY_014: Drain memory buffer
        var entries = new List<string>();
        while (_logQueue.TryDequeue(out var entry))
        {
            entries.Add(entry);
        }

        var content = string.Join("\n", entries) + "\n";

        // $REQ_PROXY_015: Events appear in files only after flush
        foreach (var dest in _logDestinations.Values)
        {
            if (dest.Directory == null)
            {
                // $REQ_STDOUT_001: Write to STDOUT (content already has newlines)
                Console.Write(content);
            }
            else
            {
                var filename = FormatFilename(dest.FilenameFormat!);
                var path = Path.Combine(dest.Directory, filename);
                Directory.CreateDirectory(dest.Directory);
                // $REQ_PROXY_005: Disk writes happen in background, not in network I/O path
                await File.AppendAllTextAsync(path, content);
            }
        }
    }

    private static void FlushAllLogsSync()
    {
        if (_logQueue.IsEmpty) return;

        var entries = new List<string>();
        while (_logQueue.TryDequeue(out var entry))
        {
            entries.Add(entry);
        }

        var content = string.Join("\n", entries) + "\n";

        foreach (var dest in _logDestinations.Values)
        {
            if (dest.Directory == null)
            {
                // $REQ_STDOUT_001: Write to STDOUT (content already has newlines)
                Console.Write(content);
                Console.Out.Flush();  // $REQ_SHUTDOWN_004: Ensure output is flushed
            }
            else
            {
                var filename = FormatFilename(dest.FilenameFormat!);
                var path = Path.Combine(dest.Directory, filename);
                Directory.CreateDirectory(dest.Directory);
                File.AppendAllText(path, content);
            }
        }
    }

    // Flush a single event immediately to all destinations, bypassing the queue
    private static void FlushEventImmediate(string json)
    {
        var content = json + "\n";

        foreach (var dest in _logDestinations.Values)
        {
            if (dest.Directory == null)
            {
                Console.Write(content);
                Console.Out.Flush();
            }
            else
            {
                var filename = FormatFilename(dest.FilenameFormat!);
                var path = Path.Combine(dest.Directory, filename);
                Directory.CreateDirectory(dest.Directory);
                File.AppendAllText(path, content);
            }
        }
    }

    private static string FormatFilename(string format)
    {
        var now = DateTime.UtcNow;
        var result = format
            .Replace("%Y", now.Year.ToString("D4"))
            .Replace("%m", now.Month.ToString("D2"))
            .Replace("%d", now.Day.ToString("D2"))
            .Replace("%H", now.Hour.ToString("D2"))
            .Replace("%M", now.Minute.ToString("D2"))
            .Replace("%S", now.Second.ToString("D2"));

        // Also support {timestamp} format
        if (result.Contains("{timestamp}"))
        {
            var timestamp = now.ToString("yyyy-MM-ddTHHmmss");
            result = result.Replace("{timestamp}", timestamp);
        }

        return result;
    }

    private static async Task AcceptMcpConnections()
    {
        while (!_cts.Token.IsCancellationRequested)
        {
            try
            {
                var client = await _mcpListener!.AcceptTcpClientAsync();
                _ = Task.Run(() => HandleMcpConnection(client));
            }
            catch { break; }
        }
    }

    private static async Task HandleMcpConnection(TcpClient client)
    {
        using var stream = client.GetStream();
        using var reader = new StreamReader(stream, new UTF8Encoding(false));
        using var writer = new StreamWriter(stream, new UTF8Encoding(false)) { AutoFlush = true };

        while (!_cts.Token.IsCancellationRequested)
        {
            try
            {
                var line = await reader.ReadLineAsync();
                if (line == null) break;

                var request = JsonSerializer.Deserialize(line, JsonContext.Default.JsonRpcRequest);
                var response = HandleMcpRequest(request!);
                await writer.WriteLineAsync(JsonSerializer.Serialize(response, JsonContext.Default.JsonRpcResponse));
            }
            catch { break; }
        }
    }

    private static JsonRpcResponse HandleMcpRequest(JsonRpcRequest request)
    {
        try
        {
            // Get raw JSON string from params for checking empty object
            var paramsJson = request.Params.GetRawText();

            switch (request.Method)
            {
                case "start-logging":
                    var startParams = JsonSerializer.Deserialize(request.Params.GetRawText(), JsonContext.Default.StartLoggingParams);
                    // Add the new destination first
                    var logDest = new LogDestination { Directory = startParams!.Directory, FilenameFormat = startParams.FilenameFormat ?? "rawprox_%Y-%m-%d-%H.ndjson" };
                    _logDestinations[startParams.Directory ?? "stdout"] = logDest;
                    // Create and immediately flush the start-logging event (bypassing the queue to ensure it appears before any pending events)
                    string startLogJson;
                    if (startParams.Directory == null)
                    {
                        startLogJson = JsonSerializer.Serialize(new LogEventStartLoggingStdout { time = GetTimestamp(), directory = null }, JsonContext.Default.LogEventStartLoggingStdout);
                    }
                    else
                    {
                        startLogJson = JsonSerializer.Serialize(new LogEventStartLogging { time = GetTimestamp(), directory = startParams.Directory, filename_format = startParams.FilenameFormat ?? "rawprox_%Y-%m-%d-%H.ndjson" }, JsonContext.Default.LogEventStartLogging);
                    }
                    FlushEventImmediate(startLogJson); // Flush immediately to all destinations
                    return new JsonRpcResponse { Id = request.Id, Result = "success" };

                case "stop-logging":
                    // $REQ_MCP_009, $REQ_MCP_010, $REQ_MCP_011: Handle stop-logging with different parameter types
                    var stopParams = JsonSerializer.Deserialize(request.Params.GetRawText(), JsonContext.Default.StopLoggingParams);

                    // Check if params is empty object {} (stop ALL destinations)
                    if (paramsJson == "{}")
                    {
                        // $REQ_MCP_010: Stop all logging destinations
                        // First, collect all stop-logging events (before removing any destinations)
                        var stopEvents = new List<string>();
                        foreach (var dest in _logDestinations.Keys.ToList())
                        {
                            var dir = dest == "stdout" ? null : dest;
                            var stopLogJson = JsonSerializer.Serialize(new LogEventStopLogging { time = GetTimestamp(), directory = dir }, JsonContext.Default.LogEventStopLogging);
                            stopEvents.Add(stopLogJson);
                        }

                        // Then flush all events to all destinations (before removing any)
                        foreach (var stopLogJson in stopEvents)
                        {
                            FlushEventImmediate(stopLogJson);
                        }

                        // Finally, remove all destinations
                        foreach (var dest in _logDestinations.Keys.ToList())
                        {
                            _logDestinations.TryRemove(dest, out _);
                        }
                    }
                    else
                    {
                        // $REQ_MCP_011: Stop specific destination (null = STDOUT, or specific directory)
                        var stopLogJson = JsonSerializer.Serialize(new LogEventStopLogging { time = GetTimestamp(), directory = stopParams?.Directory }, JsonContext.Default.LogEventStopLogging);
                        FlushEventImmediate(stopLogJson); // Flush to all destinations INCLUDING the one being stopped
                        _logDestinations.TryRemove(stopParams?.Directory ?? "stdout", out _);
                    }
                    return new JsonRpcResponse { Id = request.Id, Result = "success" };

                case "add-port-rule":
                    var addParams = JsonSerializer.Deserialize(request.Params.GetRawText(), JsonContext.Default.AddPortRuleParams);
                    var rule = new PortRule(addParams!.LocalPort, addParams.TargetHost, addParams.TargetPort);
                    // $REQ_MCP_020, $REQ_MCP_024: Return error if port is already in use
                    if (!StartPortRule(rule))
                    {
                        return new JsonRpcResponse
                        {
                            Id = request.Id,
                            Error = new JsonRpcError
                            {
                                Code = -32000,
                                Message = $"Failed to start listener on port {addParams.LocalPort}: port is already in use"
                            }
                        };
                    }
                    return new JsonRpcResponse { Id = request.Id, Result = "success" };

                case "remove-port-rule":
                    var removeParams = JsonSerializer.Deserialize(request.Params.GetRawText(), JsonContext.Default.RemovePortRuleParams);
                    if (_listeners.TryRemove(removeParams!.LocalPort, out var listener))
                    {
                        listener.Stop();
                    }
                    return new JsonRpcResponse { Id = request.Id, Result = "success" };

                case "shutdown":
                    _cts.Cancel();
                    return new JsonRpcResponse { Id = request.Id, Result = "success" };

                default:
                    return new JsonRpcResponse { Id = request.Id, Error = new JsonRpcError { Code = -32601, Message = "Method not found" } };
            }
        }
        catch (Exception ex)
        {
            return new JsonRpcResponse { Id = request.Id, Error = new JsonRpcError { Code = -32602, Message = ex.Message } };
        }
    }
}

record PortRule(int LocalPort, string TargetHost, int TargetPort);

class LogDestination
{
    public string? Directory { get; set; }
    public string? FilenameFormat { get; set; }
}

class JsonRpcRequest
{
    [JsonPropertyName("jsonrpc")]
    public string JsonRpc { get; set; } = "";
    [JsonPropertyName("method")]
    public string Method { get; set; } = "";
    [JsonPropertyName("params")]
    public JsonElement Params { get; set; }
    [JsonPropertyName("id")]
    public int Id { get; set; }
}

class JsonRpcResponse
{
    [JsonPropertyName("jsonrpc")]
    public string JsonRpc { get; set; } = "2.0";
    [JsonPropertyName("result")]
    public object? Result { get; set; }
    [JsonPropertyName("error")]
    public JsonRpcError? Error { get; set; }
    [JsonPropertyName("id")]
    public int Id { get; set; }
}

class JsonRpcError
{
    [JsonPropertyName("code")]
    public int Code { get; set; }
    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
}

class StartLoggingParams
{
    [JsonPropertyName("directory")]
    public string? Directory { get; set; }
    [JsonPropertyName("filename_format")]
    public string? FilenameFormat { get; set; }
}

class StopLoggingParams
{
    [JsonPropertyName("directory")]
    public string? Directory { get; set; }
}

class AddPortRuleParams
{
    [JsonPropertyName("local_port")]
    public int LocalPort { get; set; }
    [JsonPropertyName("target_host")]
    public string TargetHost { get; set; } = "";
    [JsonPropertyName("target_port")]
    public int TargetPort { get; set; }
}

class RemovePortRuleParams
{
    [JsonPropertyName("local_port")]
    public int LocalPort { get; set; }
}

// JSON source generator context for AOT compilation
[JsonSourceGenerationOptions(WriteIndented = false, DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull)]
[JsonSerializable(typeof(JsonRpcRequest))]
[JsonSerializable(typeof(JsonRpcResponse))]
[JsonSerializable(typeof(JsonRpcError))]
[JsonSerializable(typeof(StartLoggingParams))]
[JsonSerializable(typeof(StopLoggingParams))]
[JsonSerializable(typeof(AddPortRuleParams))]
[JsonSerializable(typeof(RemovePortRuleParams))]
[JsonSerializable(typeof(LogEventStartMcp))]
[JsonSerializable(typeof(LogEventStartLogging))]
[JsonSerializable(typeof(LogEventStartLoggingStdout))]
[JsonSerializable(typeof(LogEventStopLogging))]
[JsonSerializable(typeof(LogEventOpen))]
[JsonSerializable(typeof(LogEventClose))]
[JsonSerializable(typeof(LogEventData))]
partial class JsonContext : JsonSerializerContext
{
}

// Log event types for JSON serialization
class LogEventStartMcp
{
    public string time { get; set; } = "";
    [JsonPropertyName("event")]
    public string Event { get; set; } = "start-mcp";
    public int port { get; set; }
}

class LogEventStartLogging
{
    public string time { get; set; } = "";
    [JsonPropertyName("event")]
    public string Event { get; set; } = "start-logging";
    public string directory { get; set; } = "";
    public string filename_format { get; set; } = "";
}

class LogEventStartLoggingStdout
{
    public string time { get; set; } = "";
    [JsonPropertyName("event")]
    public string Event { get; set; } = "start-logging";
    [JsonIgnore(Condition = JsonIgnoreCondition.Never)]  // Always include directory field, even when null
    public string? directory { get; set; }
}

class LogEventStopLogging
{
    public string time { get; set; } = "";
    [JsonPropertyName("event")]
    public string Event { get; set; } = "stop-logging";
    [JsonIgnore(Condition = JsonIgnoreCondition.Never)]  // Always include directory field, even when null
    public string? directory { get; set; }
}

class LogEventOpen
{
    public string time { get; set; } = "";
    public string timestamp { get; set; } = "";
    public string ConnID { get; set; } = "";
    [JsonPropertyName("event")]
    public string Event { get; set; } = "open";
    public string from { get; set; } = "";
    public string to { get; set; } = "";
}

class LogEventClose
{
    public string time { get; set; } = "";
    public string timestamp { get; set; } = "";
    public string ConnID { get; set; } = "";
    [JsonPropertyName("event")]
    public string Event { get; set; } = "close";
    public string from { get; set; } = "";
    public string to { get; set; } = "";
}

class LogEventData
{
    public string time { get; set; } = "";
    public string timestamp { get; set; } = "";
    public string ConnID { get; set; } = "";
    [JsonPropertyName("event")]
    public string Event { get; set; } = "data";
    public string data { get; set; } = "";
    public string from { get; set; } = "";
    public string to { get; set; } = "";
}
