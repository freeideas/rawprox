using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

[JsonSourceGenerationOptions(WriteIndented = false)]
[JsonSerializable(typeof(JsonElement))]
[JsonSerializable(typeof(Dictionary<string, object>))]
[JsonSerializable(typeof(int))]
internal partial class AppJsonContext : JsonSerializerContext { }

class Program
{
    private static readonly ConcurrentDictionary<int, TcpListener> _listeners = new();
    private static readonly ConcurrentBag<LogDestination> _logDestinations = new();
    private static readonly CancellationTokenSource _cts = new();
    private static int _mcpPort = -1;
    private static int _flushMillis = 2000;
    private static string _filenameFormat = "rawprox_%Y-%m-%d-%H.ndjson";
    private static long _nextConnId = 0;
    private static TcpListener? _mcpListener = null;
    private static int _exitCode = 0;

    static async Task<int> Main(string[] args)
    {
        var portRules = new List<(int local, string target, int targetPort)>();
        string? logDirectory = null;
        var filenameFormatExplicit = false;

        // Parse arguments
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--mcp-port" && i + 1 < args.Length)
            {
                if (!int.TryParse(args[++i], out _mcpPort) || _mcpPort < 0)
                {
                    await Console.Error.WriteLineAsync("Error: --mcp-port requires a non-negative integer");
                    return 1;
                }
            }
            else if (args[i] == "--flush-millis" && i + 1 < args.Length)
            {
                if (!int.TryParse(args[++i], out _flushMillis) || _flushMillis < 0)
                {
                    await Console.Error.WriteLineAsync("Error: --flush-millis requires a non-negative integer");
                    return 1;
                }
            }
            else if (args[i] == "--filename-format" && i + 1 < args.Length)
            {
                _filenameFormat = args[++i];
                filenameFormatExplicit = true;
            }
            else if (args[i].StartsWith('@'))
            {
                if (logDirectory != null)
                {
                    await Console.Error.WriteLineAsync("Error: Only one @DIRECTORY allowed on command line");
                    return 1;
                }
                logDirectory = args[i].Substring(1);
            }
            else if (args[i].Contains(':'))
            {
                var parts = args[i].Split(':');
                if (parts.Length == 3 && int.TryParse(parts[0], out int local) && int.TryParse(parts[2], out int targetPort))
                {
                    portRules.Add((local, parts[1], targetPort));
                }
            }
        }

        if (filenameFormatExplicit && logDirectory == null)
        {
            await Console.Error.WriteLineAsync("Error: --filename-format requires an @DIRECTORY destination"); // $REQ_ROT_015
            return 1;
        }

        // Validate arguments
        if (logDirectory != null && portRules.Count == 0 && _mcpPort == -1)
        {
            await Console.Error.WriteLineAsync("Error: @DIRECTORY specified without port rules. Use MCP's start-logging tool for dynamic logging control.");
            return 1;
        }

        if (_mcpPort == -1 && portRules.Count == 0)
        {
            await ShowHelp();
            return 0;
        }

        // Initialize connection ID
        _nextConnId = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() * 1000;

        // Start logging if directory specified
        if (logDirectory != null)
        {
            await StartLogging(logDirectory, _filenameFormat);
        }
        else
        {
            // Add STDOUT as default destination
            var stdoutDest = new LogDestination(null, _filenameFormat);
            _logDestinations.Add(stdoutDest);
            _ = Task.Run(() => stdoutDest.FlushLoop(_flushMillis, _cts.Token));
        }

        // Start MCP server if requested
        if (_mcpPort != -1)
        {
            try
            {
                // $REQ_MCP_001: Enable MCP server when --mcp-port is provided
                // $REQ_MCP_002: Allow system-chosen port when 0 is requested
                _mcpListener = new TcpListener(IPAddress.Loopback, _mcpPort);
                _mcpListener.Start();
                var actualPort = ((IPEndPoint)_mcpListener.LocalEndpoint).Port;

                LogEvent(new Dictionary<string, object> {
                    ["time"] = GetTimestamp(),
                    ["event"] = "mcp-ready",
                    ["endpoint"] = $"http://127.0.0.1:{actualPort}/mcp"
                }, flush: true); // $REQ_MCP_003, $REQ_MCP_004
                _ = Task.Run(() => RunMcpServer(_mcpListener, _cts.Token));
            }
            catch (Exception ex)
            {
                await Console.Error.WriteLineAsync($"Error starting MCP server: {ex.Message}");
                return 1;
            }
        }

        // Start port rules
        foreach (var rule in portRules)
        {
            await AddPortRule(rule.local, rule.target, rule.targetPort);
        }

        // Wait for cancellation
        Console.CancelKeyPress += (s, e) => { e.Cancel = true; _cts.Cancel(); };
        await Task.Delay(-1, _cts.Token).ContinueWith(_ => { });

        // Cleanup
        _mcpListener?.Stop();
        foreach (var listener in _listeners.Values)
        {
            listener.Stop();
        }

        return _exitCode;
    }

    private static async Task ShowHelp()
    {
        await Console.Error.WriteLineAsync(@"RawProx - TCP Proxy with Traffic Capture

Usage:
  rawprox.exe [--mcp-port PORT] [--flush-millis MS] [--filename-format FORMAT] PORT_RULE... [@LOG_DIRECTORY]

Arguments:
  --mcp-port PORT         Enable MCP server on specified port (0 for system-chosen)
  --flush-millis MS       Buffer flush interval in milliseconds (default: 2000)
  --filename-format FMT   Log filename pattern using strftime format (default: rawprox_%Y-%m-%d-%H.ndjson)
  PORT_RULE               Port forwarding rule: LOCAL_PORT:TARGET_HOST:TARGET_PORT
  @LOG_DIRECTORY          Log to time-rotated files in directory

Examples:
  rawprox.exe 8080:example.com:80
  rawprox.exe 8080:example.com:80 @logs
  rawprox.exe --mcp-port 8765 8080:example.com:80 @logs

Documentation:
  See ./readme/*.md for detailed documentation");
    }

    private static async Task AddPortRule(int localPort, string targetHost, int targetPort)
    {
        try
        {
            var listener = new TcpListener(IPAddress.Any, localPort);
            listener.Start();
            _listeners[localPort] = listener;
            _ = Task.Run(() => AcceptConnections(listener, targetHost, targetPort, localPort, _cts.Token));
        }
        catch (SocketException ex) when (ex.SocketErrorCode == SocketError.AddressAlreadyInUse)
        {
            // $REQ_SIMPLE_004: Port Already in Use Error
            await Console.Error.WriteLineAsync($"Error: Port {localPort} is already in use");
            _exitCode = 1;
            _cts.Cancel();
        }
    }

    private static async Task AcceptConnections(TcpListener listener, string targetHost, int targetPort, int localPort, CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                var client = await listener.AcceptTcpClientAsync(ct);
                _ = Task.Run(() => HandleConnection(client, targetHost, targetPort, localPort, ct));
            }
            catch when (ct.IsCancellationRequested) { break; }
            catch { }
        }
    }

    private static async Task HandleConnection(TcpClient client, string targetHost, int targetPort, int localPort, CancellationToken ct)
    {
        var connId = GetNextConnId();
        TcpClient? server = null;

        var clientEp = client.Client.RemoteEndPoint?.ToString() ?? "unknown";
        var listenerEp = client.Client.LocalEndPoint?.ToString() ?? $"0.0.0.0:{localPort}";
        var serverEp = $"{targetHost}:{targetPort}";

        try
        {
            // $REQ_SIMPLE_011: Connection Open Event
            // $REQ_SIMPLE_018: Don't block network forwarding on disk writes
            // $REQ_SIMPLE_019: Fire-and-forget logging - network never waits for disk
            LogEvent(new Dictionary<string, object> {
                ["time"] = GetTimestamp(),
                ["ConnID"] = connId,
                ["event"] = "open",
                ["from"] = clientEp,
                ["to"] = serverEp,
                ["listener"] = listenerEp,
                ["listen_port"] = localPort
            });

            // $REQ_SIMPLE_005: Establish outbound TCP connection before forwarding
            server = await ConnectToTarget(targetHost, targetPort, ct);

            var clientStream = client.GetStream();
            var serverStream = server.GetStream();

            var task1 = ForwardData(clientStream, serverStream, connId, clientEp, serverEp, listenerEp, localPort, ct);
            var task2 = ForwardData(serverStream, clientStream, connId, serverEp, clientEp, listenerEp, localPort, ct);

            await Task.WhenAny(task1, task2);
        }
        catch (Exception)
        {
            // Swallow errors after logging to maintain proxy availability
        }
        finally
        {
            // $REQ_SIMPLE_015: Connection Close Event
            // $REQ_SIMPLE_018: Don't block network forwarding on disk writes
            // $REQ_SIMPLE_019: Fire-and-forget logging - network never waits for disk
            LogEvent(new Dictionary<string, object> {
                ["time"] = GetTimestamp(),
                ["ConnID"] = connId,
                ["event"] = "close",
                ["from"] = serverEp,
                ["to"] = clientEp,
                ["listener"] = listenerEp,
            });

            client?.Close();
            server?.Close();
        }
    }

    private static async Task ForwardData(NetworkStream from, NetworkStream to, string connId, string fromEp, string toEp, string listenerEp, int localPort, CancellationToken ct)
    {
        var buffer = new byte[8192];
        try
        {
            while (!ct.IsCancellationRequested)
            {
                int read = await from.ReadAsync(buffer, 0, buffer.Length, ct);
                if (read == 0) break;

                await to.WriteAsync(buffer, 0, read, ct);

                var data = EscapeData(buffer, read);
                // $REQ_SIMPLE_013: Traffic Data Events
                // $REQ_SIMPLE_018: Don't block network forwarding on disk writes
                // $REQ_SIMPLE_019: Fire-and-forget logging - network never waits for disk
                LogEvent(new Dictionary<string, object> {
                    ["time"] = GetTimestamp(),
                    ["ConnID"] = connId,
                    ["data"] = data,
                    ["from"] = fromEp,
                    ["to"] = toEp,
                    ["listener"] = listenerEp,
                    ["listen_port"] = localPort
                });
            }
        }
        catch when (ct.IsCancellationRequested) { }
        catch { }
    }

    private static async Task<TcpClient> ConnectToTarget(string targetHost, int targetPort, CancellationToken ct)
    {
        var addresses = await Dns.GetHostAddressesAsync(targetHost);
        if (addresses.Length == 0)
        {
            throw new SocketException((int)SocketError.HostNotFound);
        }

        // Prefer IPv4 to match tests binding to IPv4 loopback
        var ordered = addresses.OrderByDescending(a => a.AddressFamily == AddressFamily.InterNetwork ? 1 : 0).ToArray();

        Exception? lastError = null;
        foreach (var address in ordered)
        {
            if (ct.IsCancellationRequested)
            {
                throw new OperationCanceledException(ct);
            }

            var client = new TcpClient(address.AddressFamily);
            using var registration = ct.Register(() =>
            {
                try { client.Dispose(); } catch { }
            });

            try
            {
                await client.ConnectAsync(address, targetPort);
                return client;
            }
            catch (Exception ex)
            {
                lastError = ex;
                try { client.Dispose(); } catch { }
            }
        }

        throw lastError ?? new SocketException((int)SocketError.HostUnreachable);
    }

    private static string EscapeData(byte[] bytes, int length)
    {
        // $REQ_SIMPLE_014: URL-encode data for JSON embedding
        // JSON serializer will handle JSON escaping, we only do URL encoding
        var sb = new StringBuilder();
        for (int i = 0; i < length; i++)
        {
            var b = bytes[i];
            // Percent sign must be encoded as %25
            if (b == 0x25) sb.Append("%25");
            // Printable ASCII (0x20-0x7E except %) as literal
            else if (b >= 0x20 && b <= 0x7E) sb.Append((char)b);
            // All other bytes as %XX (including \t, \n, \r, etc.)
            else sb.Append($"%{b:X2}");
        }
        return sb.ToString();
    }

    private static string GetNextConnId()
    {
        // $REQ_SIMPLE_012: Get current ID, then increment for next connection
        long id = Interlocked.Add(ref _nextConnId, 1) - 1;
        var base62 = ToBase62(id);
        // $REQ_SIMPLE_012: Use last 8 characters of base-62 representation
        if (base62.Length >= 8)
        {
            return base62.Substring(base62.Length - 8);
        }
        else
        {
            return base62.PadLeft(8, '0');
        }
    }

    private static string ToBase62(long num)
    {
        const string chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
        var sb = new StringBuilder();
        while (num > 0)
        {
            sb.Insert(0, chars[(int)(num % 62)]);
            num /= 62;
        }
        return sb.Length > 0 ? sb.ToString() : "0";
    }

    private static string GetTimestamp()
    {
        return DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ", CultureInfo.InvariantCulture);
    }

    private static void LogEvent(Dictionary<string, object> obj, bool flush = false)
    {
        var json = JsonSerializer.Serialize(obj, AppJsonContext.Default.DictionaryStringObject);
        foreach (var dest in _logDestinations)
        {
            // Fire-and-forget: Log() returns Task.CompletedTask immediately, no need to await
            _ = dest.Log(json);
            if (flush)
            {
                _ = Task.Run(() => dest.FlushNow());
            }
        }
    }

    private static Task StartLogging(string? directory, string filenameFormat)
    {
        var dest = new LogDestination(directory, filenameFormat);
        _logDestinations.Add(dest);
        _ = Task.Run(() => dest.FlushLoop(_flushMillis, _cts.Token));

        // $REQ_LOG_016: filename_format only in event for directory logging, not STDOUT
        var logEvent = new Dictionary<string, object> {
            ["time"] = GetTimestamp(),
            ["event"] = "start-logging",
            ["directory"] = directory!
        };
        if (directory != null)
        {
            logEvent["filename_format"] = filenameFormat;
        }

        LogEvent(logEvent, flush: true);
        return Task.CompletedTask;
    }

    private enum StopLoggingTarget
    {
        All,
        Stdout,
        Directory
    }

    private static Task StopLogging(string? directory, StopLoggingTarget target)
    {
        var active = _logDestinations.Where(d => !d.IsStopped).ToList();
        IEnumerable<LogDestination> selected = target switch
        {
            StopLoggingTarget.All => active,
            StopLoggingTarget.Stdout => active.Where(d => d.Directory == null),
            StopLoggingTarget.Directory => active.Where(d => string.Equals(d.Directory, directory, StringComparison.Ordinal)),
            _ => Enumerable.Empty<LogDestination>()
        };

        foreach (var dest in selected)
        {
            LogEvent(new Dictionary<string, object> {
                ["time"] = GetTimestamp(),
                ["event"] = "stop-logging",
                ["directory"] = dest.Directory!
            }, flush: true); // $REQ_LOG_002, $REQ_LOG_005, $REQ_LOG_006, $REQ_LOG_007
            dest.Stop();
        }
        return Task.CompletedTask;
    }

    private static async Task RunMcpServer(TcpListener listener, CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                // $REQ_MCP_007: Accept MCP HTTP connections
                var client = await listener.AcceptTcpClientAsync(ct);
                _ = Task.Run(() => HandleMcpClient(client, ct));
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
            }
        }
    }

    private static async Task HandleMcpClient(TcpClient client, CancellationToken ct)
    {
        using var tcp = client;
        using var stream = tcp.GetStream();
        using var reader = new StreamReader(stream, Encoding.UTF8, leaveOpen: true);

        var requestLine = await reader.ReadLineAsync();
        if (string.IsNullOrEmpty(requestLine))
        {
            await WriteHttpResponse(stream, 400, "Bad Request", "{\"error\":\"invalid request\"}", "application/json");
            return;
        }

        var parts = requestLine.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length < 2)
        {
            await WriteHttpResponse(stream, 400, "Bad Request", "{\"error\":\"invalid request\"}", "application/json");
            return;
        }

        var method = parts[0];
        var path = parts[1];

        var headers = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        string? line;
        while (!string.IsNullOrEmpty(line = await reader.ReadLineAsync()))
        {
            var separator = line.IndexOf(':');
            if (separator > 0)
            {
                var name = line[..separator].Trim();
                var value = line[(separator + 1)..].Trim();
                headers[name] = value;
            }
        }

        if (!headers.TryGetValue("Content-Length", out var contentLengthValue) || !int.TryParse(contentLengthValue, out var contentLength) || contentLength < 0)
        {
            await WriteHttpResponse(stream, 411, "Length Required", "{\"error\":\"content-length required\"}", "application/json");
            return;
        }

        var bodyBuffer = new char[contentLength];
        var read = 0;
        while (read < contentLength)
        {
            var chunk = await reader.ReadAsync(bodyBuffer, read, contentLength - read);
            if (chunk == 0) break;
            read += chunk;
        }

        var body = new string(bodyBuffer, 0, read);

        if (!string.Equals(method, "POST", StringComparison.OrdinalIgnoreCase) || !path.StartsWith("/mcp", StringComparison.Ordinal))
        {
            // $REQ_MCP_021: Serve MCP only on /mcp path
            await WriteHttpResponse(stream, 404, "Not Found", "{\"error\":\"not found\"}", "application/json");
            return;
        }

        var (statusCode, responseBody) = await ProcessMcpRequest(body);
        await WriteHttpResponse(stream, statusCode, statusCode == 200 ? "OK" : "Error", responseBody, "application/json");
    }

    private static async Task<(int StatusCode, string Body)> ProcessMcpRequest(string body)
    {
        try
        {
            var request = JsonSerializer.Deserialize<JsonElement>(body, AppJsonContext.Default.JsonElement);
            var method = request.GetProperty("method").GetString();
            var id = request.TryGetProperty("id", out var idProp) ? idProp : default;

            return method switch
            {
                "initialize" => JsonRpcSuccess(id, WriteInitializeResult), // $REQ_MCP_008, $REQ_MCP_019, $REQ_MCP_022, $REQ_MCP_027, $REQ_MCP_028
                "tools/list" => JsonRpcSuccess(id, WriteToolsListResult), // $REQ_MCP_009, $REQ_MCP_029, $REQ_MCP_034, $REQ_MCP_035, $REQ_MCP_036, $REQ_MCP_037, $REQ_MCP_038, $REQ_MCP_039
                "tools/call" => await HandleToolCall(request, id), // $REQ_MCP_010, $REQ_MCP_030
                _ => JsonRpcError(id, -32601, $"Unknown method: {method}")
            };
        }
        catch (Exception ex)
        {
            return JsonRpcError(default, -32603, ex.Message); // $REQ_MCP_011
        }
    }

    private static async Task WriteHttpResponse(NetworkStream stream, int statusCode, string reasonPhrase, string body, string contentType)
    {
        body ??= string.Empty;
        var encodedBody = Encoding.UTF8.GetBytes(body);
        var headerBuilder = new StringBuilder();
        headerBuilder.Append($"HTTP/1.1 {statusCode} {reasonPhrase}\r\n");
        headerBuilder.Append($"Content-Type: {contentType}\r\n");
        headerBuilder.Append("Connection: close\r\n");
        headerBuilder.Append($"Content-Length: {encodedBody.Length}\r\n\r\n");
        var headerBytes = Encoding.UTF8.GetBytes(headerBuilder.ToString());
        await stream.WriteAsync(headerBytes, 0, headerBytes.Length);
        if (encodedBody.Length > 0)
        {
            await stream.WriteAsync(encodedBody, 0, encodedBody.Length);
        }
    }

    private static async Task<(int StatusCode, string Body)> HandleToolCall(JsonElement request, JsonElement id)
    {
        try
        {
            var name = request.GetProperty("params").GetProperty("name").GetString();
            var args = request.GetProperty("params").GetProperty("arguments");
            var message = await ExecuteTool(name!, args); // $REQ_MCP_010, $REQ_MCP_012, $REQ_MCP_013, $REQ_MCP_014, $REQ_MCP_015, $REQ_MCP_016, $REQ_MCP_017, $REQ_MCP_020, $REQ_MCP_031, $REQ_MCP_032, $REQ_MCP_033

            return JsonRpcSuccess(id, writer =>
            {
                writer.WriteStartObject();
                writer.WritePropertyName("content");
                writer.WriteStartArray();
                writer.WriteStartObject();
                writer.WriteString("type", "text");
                writer.WriteString("text", message);
                writer.WriteEndObject();
                writer.WriteEndArray();
                writer.WriteEndObject();
            });
        }
        catch (Exception ex)
        {
            return JsonRpcError(id, -32000, ex.Message);
        }
    }

    private static async Task<string> ExecuteTool(string name, JsonElement args)
    {
        switch (name)
        {
            case "start-logging":
                // $REQ_MCP_012: Start logging tool
                var dir = args.TryGetProperty("directory", out var dirProp) && dirProp.ValueKind != JsonValueKind.Null ? dirProp.GetString() : null;
                var fmt = args.TryGetProperty("filename_format", out var fmtProp) ? fmtProp.GetString()! : _filenameFormat;
                await StartLogging(dir, fmt);
                return $"Started logging to {dir ?? "STDOUT"}";

            case "stop-logging":
                // $REQ_MCP_013: Stop logging tool
                if (!args.TryGetProperty("directory", out var stopDirProp))
                {
                    await StopLogging(null, StopLoggingTarget.All); // $REQ_LOG_005
                    return "Stopped logging to all destinations";
                }

                if (stopDirProp.ValueKind == JsonValueKind.Null)
                {
                    await StopLogging(null, StopLoggingTarget.Stdout); // $REQ_LOG_006
                    return "Stopped logging to STDOUT";
                }

                var stopDirectory = stopDirProp.GetString();
                if (string.IsNullOrEmpty(stopDirectory))
                {
                    throw new Exception("stop-logging requires a non-empty directory when provided");
                }
                await StopLogging(stopDirectory, StopLoggingTarget.Directory); // $REQ_LOG_007
                return $"Stopped logging to {stopDirectory}";

            case "add-port-rule":
                // $REQ_MCP_014: Add port rule tool
                var local = args.GetProperty("local_port").GetInt32(); // $REQ_MCP_031
                var target = args.GetProperty("target_host").GetString()!;
                var targetPort = args.GetProperty("target_port").GetInt32();
                await AddPortRule(local, target, targetPort);
                return $"Added port rule {local}:{target}:{targetPort}";

            case "remove-port-rule":
                // $REQ_MCP_015: Remove port rule tool
                var removePort = args.GetProperty("local_port").GetInt32(); // $REQ_MCP_032
                if (_listeners.TryRemove(removePort, out var listener))
                {
                    listener.Stop();
                    return $"Removed port rule for port {removePort}";
                }
                throw new Exception($"Port {removePort} not found");

            case "shutdown":
                // $REQ_MCP_016: Shutdown tool
                _cts.Cancel(); // $REQ_MCP_020, $REQ_MCP_033
                return "Shutting down";

            default:
                throw new Exception($"Unknown tool: {name}");
        }
    }

    private static (int StatusCode, string Body) JsonRpcSuccess(JsonElement id, Action<Utf8JsonWriter> writeResult)
    {
        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream))
        {
            writer.WriteStartObject();
            writer.WriteString("jsonrpc", "2.0");
            if (id.ValueKind != JsonValueKind.Undefined && id.ValueKind != JsonValueKind.Null)
            {
                writer.WritePropertyName("id");
                id.WriteTo(writer);
            }
            writer.WritePropertyName("result");
            writeResult(writer);
            writer.WriteEndObject();
            writer.Flush();
        }
        return (200, Encoding.UTF8.GetString(stream.ToArray()));
    }

    private static (int StatusCode, string Body) JsonRpcError(JsonElement id, int code, string message)
    {
        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream))
        {
            writer.WriteStartObject();
            writer.WriteString("jsonrpc", "2.0");
            if (id.ValueKind != JsonValueKind.Undefined && id.ValueKind != JsonValueKind.Null)
            {
                writer.WritePropertyName("id");
                id.WriteTo(writer);
            }
            writer.WritePropertyName("error");
            writer.WriteStartObject();
            writer.WriteNumber("code", code);
            writer.WriteString("message", message);
            writer.WriteEndObject();
            writer.WriteEndObject();
            writer.Flush();
        }
        return (200, Encoding.UTF8.GetString(stream.ToArray()));
    }

    private static void WriteInitializeResult(Utf8JsonWriter writer)
    {
        writer.WriteStartObject();
        writer.WriteString("protocolVersion", "2024-11-05"); // $REQ_MCP_022
        writer.WritePropertyName("capabilities");
        writer.WriteStartObject();
        writer.WritePropertyName("tools");
        writer.WriteStartObject();
        writer.WriteEndObject();
        writer.WriteEndObject();
        writer.WritePropertyName("serverInfo");
        writer.WriteStartObject();
        writer.WriteString("name", "rawprox"); // $REQ_MCP_019
        writer.WriteString("version", "1.0"); // $REQ_MCP_019
        writer.WriteEndObject();
        writer.WriteEndObject();
    }

    private static void WriteToolsListResult(Utf8JsonWriter writer)
    {
        writer.WriteStartObject();
        writer.WritePropertyName("tools");
        writer.WriteStartArray();
        WriteToolDescriptor(writer, "start-logging", "Start logging to a destination", schemaWriter =>
        {
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("object");
            schemaWriter.WritePropertyName("properties");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("directory");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStartArray();
            schemaWriter.WriteStringValue("string");
            schemaWriter.WriteStringValue("null");
            schemaWriter.WriteEndArray();
            schemaWriter.WriteEndObject();
            schemaWriter.WritePropertyName("filename_format");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("string");
            schemaWriter.WriteEndObject();
            schemaWriter.WriteEndObject();
        }); // $REQ_MCP_034

        WriteToolDescriptor(writer, "stop-logging", "Stop logging to a destination", schemaWriter =>
        {
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("object");
            schemaWriter.WritePropertyName("properties");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("directory");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStartArray();
            schemaWriter.WriteStringValue("string");
            schemaWriter.WriteStringValue("null");
            schemaWriter.WriteEndArray();
            schemaWriter.WriteEndObject();
            schemaWriter.WriteEndObject();
        }); // $REQ_MCP_035

        WriteToolDescriptor(writer, "add-port-rule", "Add port forwarding rule", schemaWriter =>
        {
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("object");
            schemaWriter.WritePropertyName("properties");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("local_port");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("integer");
            schemaWriter.WriteEndObject();
            schemaWriter.WritePropertyName("target_host");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("string");
            schemaWriter.WriteEndObject();
            schemaWriter.WritePropertyName("target_port");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("integer");
            schemaWriter.WriteEndObject();
            schemaWriter.WriteEndObject();
            schemaWriter.WritePropertyName("required");
            schemaWriter.WriteStartArray();
            schemaWriter.WriteStringValue("local_port");
            schemaWriter.WriteStringValue("target_host");
            schemaWriter.WriteStringValue("target_port");
            schemaWriter.WriteEndArray();
        }); // $REQ_MCP_036

        WriteToolDescriptor(writer, "remove-port-rule", "Remove port forwarding rule", schemaWriter =>
        {
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("object");
            schemaWriter.WritePropertyName("properties");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("local_port");
            schemaWriter.WriteStartObject();
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("integer");
            schemaWriter.WriteEndObject();
            schemaWriter.WriteEndObject();
            schemaWriter.WritePropertyName("required");
            schemaWriter.WriteStartArray();
            schemaWriter.WriteStringValue("local_port");
            schemaWriter.WriteEndArray();
        }); // $REQ_MCP_037

        WriteToolDescriptor(writer, "shutdown", "Shutdown RawProx", schemaWriter =>
        {
            schemaWriter.WritePropertyName("type");
            schemaWriter.WriteStringValue("object");
            schemaWriter.WritePropertyName("properties");
            schemaWriter.WriteStartObject();
            schemaWriter.WriteEndObject();
        }); // $REQ_MCP_038

        writer.WriteEndArray();
        writer.WriteEndObject();
    }

    private static void WriteToolDescriptor(Utf8JsonWriter writer, string name, string description, Action<Utf8JsonWriter> writeSchema)
    {
        writer.WriteStartObject();
        writer.WriteString("name", name);
        writer.WriteString("description", description);
        writer.WritePropertyName("inputSchema");
        writer.WriteStartObject();
        writeSchema(writer);
        writer.WriteEndObject();
        writer.WriteEndObject();
    }
}

class LogDestination
{
    private readonly ConcurrentQueue<string> _buffer = new();
    private readonly string? _directory;
    private readonly string _filenameFormat;
    private bool _stopped;

    public string? Directory => _directory;
    public bool IsStopped => _stopped;

    public LogDestination(string? directory, string filenameFormat)
    {
        _directory = directory;
        _filenameFormat = filenameFormat;
        if (directory != null)
        {
            System.IO.Directory.CreateDirectory(directory);
        }
    }

    public Task Log(string json)
    {
        if (_stopped) return Task.CompletedTask;
        _buffer.Enqueue(json);
        return Task.CompletedTask;
    }

    public void Stop()
    {
        _stopped = true;
    }

    public async Task FlushNow()
    {
        await Flush();
    }

    public async Task FlushLoop(int intervalMs, CancellationToken ct)
    {
        while (!ct.IsCancellationRequested && !_stopped)
        {
            await Task.Delay(intervalMs, ct).ContinueWith(_ => { });
            await Flush();
        }
        await Flush(); // Final flush
    }

    private async Task Flush()
    {
        if (_buffer.IsEmpty) return;

        var lines = new List<string>();
        while (_buffer.TryDequeue(out var line))
        {
            lines.Add(line);
        }

        if (lines.Count == 0) return;

        var text = string.Join("\n", lines) + "\n";

        if (_directory == null)
        {
            await Console.Out.WriteAsync(text);
            await Console.Out.FlushAsync();
        }
        else
        {
            var filename = FormatFilename(_filenameFormat);
            var path = Path.Combine(_directory, filename);
            await File.AppendAllTextAsync(path, text);
        }
    }

    private static string FormatFilename(string format)
    {
        var sb = new StringBuilder();
        var literal = new StringBuilder();

        void FlushLiteral()
        {
            if (literal.Length == 0) return;
            sb.Append('\'');
            sb.Append(literal.ToString().Replace("'", "''"));
            sb.Append('\'');
            literal.Clear();
        }

        for (int i = 0; i < format.Length; i++)
        {
            if (format[i] == '%' && i + 1 < format.Length)
            {
                FlushLiteral();
                i++;
                sb.Append(format[i] switch
                {
                    'Y' => "yyyy",
                    'm' => "MM",
                    'd' => "dd",
                    'H' => "HH",
                    'M' => "mm",
                    'S' => "ss",
                    '%' => "'%'",
                    _ => $"'{format[i]}'"
                });
            }
            else
            {
                literal.Append(format[i]);
            }
        }

        FlushLiteral();

        var now = DateTimeOffset.UtcNow;
        return now.ToString(sb.ToString(), CultureInfo.InvariantCulture); // $REQ_ROT_002
    }
}
