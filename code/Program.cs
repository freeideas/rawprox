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
    private static HttpListener? _mcpServer = null;

    static async Task<int> Main(string[] args)
    {
        var portRules = new List<(int local, string target, int targetPort)>();
        string? logDirectory = null;

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
                _mcpServer = new HttpListener();
                int actualPort = _mcpPort == 0 ? 8765 : _mcpPort;
                var prefix = $"http://localhost:{actualPort}/";
                _mcpServer.Prefixes.Add(prefix);
                _mcpServer.Start();

                await LogEvent(new { time = GetTimestamp(), @event = "mcp-ready", endpoint = $"http://localhost:{actualPort}/mcp" });
                _ = Task.Run(() => RunMcpServer(_cts.Token));
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
        _mcpServer?.Stop();
        foreach (var listener in _listeners.Values)
        {
            listener.Stop();
        }

        return 0;
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
            _ = Task.Run(() => AcceptConnections(listener, targetHost, targetPort, _cts.Token));
        }
        catch (SocketException ex) when (ex.SocketErrorCode == SocketError.AddressAlreadyInUse)
        {
            await Console.Error.WriteLineAsync($"Error: Port {localPort} is already in use");
            _cts.Cancel();
        }
    }

    private static async Task AcceptConnections(TcpListener listener, string targetHost, int targetPort, CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                var client = await listener.AcceptTcpClientAsync(ct);
                _ = Task.Run(() => HandleConnection(client, targetHost, targetPort, ct));
            }
            catch when (ct.IsCancellationRequested) { break; }
            catch { }
        }
    }

    private static async Task HandleConnection(TcpClient client, string targetHost, int targetPort, CancellationToken ct)
    {
        var connId = GetNextConnId();
        TcpClient? server = null;

        try
        {
            server = new TcpClient();
            await server.ConnectAsync(targetHost, targetPort, ct);

            var clientEp = client.Client.RemoteEndPoint?.ToString() ?? "unknown";
            var serverEp = $"{targetHost}:{targetPort}";

            await LogEvent(new { time = GetTimestamp(), ConnID = connId, @event = "open", from = clientEp, to = serverEp });

            var clientStream = client.GetStream();
            var serverStream = server.GetStream();

            var task1 = ForwardData(clientStream, serverStream, connId, clientEp, serverEp, ct);
            var task2 = ForwardData(serverStream, clientStream, connId, serverEp, clientEp, ct);

            await Task.WhenAny(task1, task2);
        }
        catch { }
        finally
        {
            var clientEp = client.Client.RemoteEndPoint?.ToString() ?? "unknown";
            var serverEp = $"{targetHost}:{targetPort}";
            await LogEvent(new { time = GetTimestamp(), ConnID = connId, @event = "close", from = serverEp, to = clientEp });

            client?.Close();
            server?.Close();
        }
    }

    private static async Task ForwardData(NetworkStream from, NetworkStream to, string connId, string fromEp, string toEp, CancellationToken ct)
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
                await LogEvent(new { time = GetTimestamp(), ConnID = connId, data, from = fromEp, to = toEp });
            }
        }
        catch when (ct.IsCancellationRequested) { }
        catch { }
    }

    private static string EscapeData(byte[] bytes, int length)
    {
        var sb = new StringBuilder();
        for (int i = 0; i < length; i++)
        {
            var b = bytes[i];
            if (b == 0x09) sb.Append("\\t");
            else if (b == 0x0A) sb.Append("\\n");
            else if (b == 0x0D) sb.Append("\\r");
            else if (b == 0x22) sb.Append("\\\"");
            else if (b == 0x5C) sb.Append("\\\\");
            else if (b == 0x25) sb.Append("%25");
            else if (b >= 0x20 && b <= 0x7E) sb.Append((char)b);
            else sb.Append($"%{b:X2}");
        }
        return sb.ToString();
    }

    private static string GetNextConnId()
    {
        long id = Interlocked.Increment(ref _nextConnId);
        return ToBase62(id).PadLeft(8, '0').Substring(0, 8);
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

    private static async Task LogEvent(object obj)
    {
        var json = JsonSerializer.Serialize(obj, new JsonSerializerOptions { DefaultIgnoreCondition = JsonIgnoreCondition.Never });
        foreach (var dest in _logDestinations)
        {
            await dest.Log(json);
        }
    }

    private static async Task StartLogging(string? directory, string filenameFormat)
    {
        var dest = new LogDestination(directory, filenameFormat);
        _logDestinations.Add(dest);
        _ = Task.Run(() => dest.FlushLoop(_flushMillis, _cts.Token));
        await LogEvent(new { time = GetTimestamp(), @event = "start-logging", directory, filename_format = filenameFormat });
    }

    private static async Task StopLogging(string? directory)
    {
        var toRemove = _logDestinations.Where(d => d.Directory == directory).ToList();
        foreach (var dest in toRemove)
        {
            dest.Stop();
        }
        await LogEvent(new { time = GetTimestamp(), @event = "stop-logging", directory });
    }

    private static async Task RunMcpServer(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested && _mcpServer != null)
        {
            try
            {
                var context = await _mcpServer.GetContextAsync();
                _ = Task.Run(() => HandleMcpRequest(context, ct));
            }
            catch when (ct.IsCancellationRequested) { break; }
            catch { }
        }
    }

    private static async Task HandleMcpRequest(HttpListenerContext context, CancellationToken ct)
    {
        if (context.Request.HttpMethod != "POST" || !context.Request.Url!.AbsolutePath.StartsWith("/mcp"))
        {
            context.Response.StatusCode = 404;
            context.Response.Close();
            return;
        }

        try
        {
            using var reader = new StreamReader(context.Request.InputStream);
            var body = await reader.ReadToEndAsync();
            var request = JsonSerializer.Deserialize<JsonElement>(body, AppJsonContext.Default.JsonElement);

            var method = request.GetProperty("method").GetString();
            var id = request.TryGetProperty("id", out var idProp) ? idProp : default;

            object? result = method switch
            {
                "initialize" => new
                {
                    protocolVersion = "2024-11-05",
                    capabilities = new { tools = new { } },
                    serverInfo = new { name = "rawprox", version = "1.0" }
                },
                "tools/list" => new
                {
                    tools = new object[]
                    {
                        new { name = "start-logging", description = "Start logging to a destination", inputSchema = new { type = "object", properties = new { directory = new { type = new[] { "string", "null" } }, filename_format = new { type = "string" } } } },
                        new { name = "stop-logging", description = "Stop logging to a destination", inputSchema = new { type = "object", properties = new { directory = new { type = new[] { "string", "null" } } } } },
                        new { name = "add-port-rule", description = "Add port forwarding rule", inputSchema = new { type = "object", properties = new { local_port = new { type = "string" }, target_host = new { type = "string" }, target_port = new { type = "string" } }, required = new[] { "local_port", "target_host", "target_port" } } },
                        new { name = "remove-port-rule", description = "Remove port forwarding rule", inputSchema = new { type = "object", properties = new { local_port = new { type = "string" } }, required = new[] { "local_port" } } },
                        new { name = "shutdown", description = "Shutdown RawProx", inputSchema = new { type = "object", properties = new { } } }
                    }
                },
                "tools/call" => await HandleToolCall(request),
                _ => null
            };

            var response = new { jsonrpc = "2.0", id, result };
            var responseJson = JsonSerializer.Serialize(response);

            context.Response.ContentType = "application/json";
            await context.Response.OutputStream.WriteAsync(Encoding.UTF8.GetBytes(responseJson), ct);
        }
        catch (Exception ex)
        {
            var error = new { jsonrpc = "2.0", error = new { code = -32603, message = ex.Message } };
            var errorJson = JsonSerializer.Serialize(error);
            await context.Response.OutputStream.WriteAsync(Encoding.UTF8.GetBytes(errorJson), ct);
        }
        finally
        {
            context.Response.Close();
        }
    }

    private static async Task<object> HandleToolCall(JsonElement request)
    {
        var name = request.GetProperty("params").GetProperty("name").GetString();
        var args = request.GetProperty("params").GetProperty("arguments");

        switch (name)
        {
            case "start-logging":
                var dir = args.TryGetProperty("directory", out var dirProp) && dirProp.ValueKind != JsonValueKind.Null ? dirProp.GetString() : null;
                var fmt = args.TryGetProperty("filename_format", out var fmtProp) ? fmtProp.GetString() : _filenameFormat;
                await StartLogging(dir, fmt!);
                return new { content = new[] { new { type = "text", text = $"Started logging to {dir ?? "STDOUT"}" } } };

            case "stop-logging":
                var stopDir = args.TryGetProperty("directory", out var stopDirProp) && stopDirProp.ValueKind != JsonValueKind.Null ? stopDirProp.GetString() : null;
                await StopLogging(stopDir);
                return new { content = new[] { new { type = "text", text = $"Stopped logging to {stopDir ?? "STDOUT"}" } } };

            case "add-port-rule":
                var local = args.GetProperty("local_port").GetInt32();
                var target = args.GetProperty("target_host").GetString()!;
                var targetPort = args.GetProperty("target_port").GetInt32();
                await AddPortRule(local, target, targetPort);
                return new { content = new[] { new { type = "text", text = $"Added port rule {local}:{target}:{targetPort}" } } };

            case "remove-port-rule":
                var removePort = args.GetProperty("local_port").GetInt32();
                if (_listeners.TryRemove(removePort, out var listener))
                {
                    listener.Stop();
                    return new { content = new[] { new { type = "text", text = $"Removed port rule for port {removePort}" } } };
                }
                throw new Exception($"Port {removePort} not found");

            case "shutdown":
                _cts.Cancel();
                return new { content = new[] { new { type = "text", text = "Shutting down" } } };

            default:
                throw new Exception($"Unknown tool: {name}");
        }
    }
}

class LogDestination
{
    private readonly ConcurrentQueue<string> _buffer = new();
    private readonly string? _directory;
    private readonly string _filenameFormat;
    private bool _stopped;

    public string? Directory => _directory;

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
        _buffer.Enqueue(json);
        return Task.CompletedTask;
    }

    public void Stop()
    {
        _stopped = true;
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
        var now = DateTimeOffset.UtcNow;
        return now.ToString(format.Replace("%Y", "yyyy").Replace("%m", "MM").Replace("%d", "dd")
            .Replace("%H", "HH").Replace("%M", "mm").Replace("%S", "ss"));
    }
}
