using System.Net;
using System.Net.Sockets;
using System.Text;

class Program
{
    static OutputWriter? _globalWriter = null;

    static async Task<int> Main(string[] args)
    {
        // Check for test mode
        if (args.Length == 1 && args[0] == "--run-tests")
        {
            return RunTests();
        }

        try
        {
            var config = ParseArgs(args);
            var outputWriter = new OutputWriter(config.OutputFile, config.FlushIntervalMs);
            _globalWriter = outputWriter;
            var connIdGen = new ConnIdGenerator();

            // Handle Ctrl+C and process termination
            Console.CancelKeyPress += (sender, e) =>
            {
                e.Cancel = true;
                outputWriter.Flush();
                Environment.Exit(0);
            };

            AppDomain.CurrentDomain.ProcessExit += (sender, e) =>
            {
                outputWriter.Flush();
            };

            Console.Error.WriteLine($"RawProx starting with {config.PortForwardings.Count} port forwarding(s)");

            var tasks = new List<Task>();
            foreach (var forwarding in config.PortForwardings)
            {
                tasks.Add(StartListener(forwarding, outputWriter, connIdGen));
            }

            await Task.WhenAll(tasks);
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error: {ex.Message}");
            return 1;
        }
        finally
        {
            _globalWriter?.Flush();
        }
    }

    static int RunTests()
    {
        Console.WriteLine("Running unit tests...");
        var testMethods = typeof(Program).GetMethods(
            System.Reflection.BindingFlags.Static |
            System.Reflection.BindingFlags.NonPublic |
            System.Reflection.BindingFlags.Public)
            .Where(m => m.Name.Contains("_TEST_"))
            .ToList();

        int passed = 0;
        int failed = 0;

        foreach (var method in testMethods)
        {
            Console.Write($"  {method.Name}... ");
            try
            {
                method.Invoke(null, null);
                Console.WriteLine("PASS");
                passed++;
            }
            catch (Exception ex)
            {
                Console.WriteLine("FAIL");
                Console.Error.WriteLine($"    {ex.InnerException?.Message ?? ex.Message}");
                failed++;
            }
        }

        Console.WriteLine($"\nTests: {testMethods.Count}, Passed: {passed}, Failed: {failed}");
        return failed == 0 ? 0 : 1;
    }

    static Config ParseArgs(string[] args)
    {
        if (args.Length == 0)
        {
            Console.Error.WriteLine("Usage: rawprox [LOCAL_PORT:TARGET_HOST:TARGET_PORT ...] [@FILEPATH] [--flush-interval-ms=MILLISECONDS]");
            Environment.Exit(1);
        }

        var forwardings = new List<PortForwarding>();
        string? outputFile = null;
        int flushIntervalMs = 2000;

        foreach (var arg in args)
        {
            if (arg.StartsWith("@"))
            {
                outputFile = arg.Substring(1);
            }
            else if (arg.StartsWith("--flush-interval-ms="))
            {
                var value = arg.Substring("--flush-interval-ms=".Length);
                if (!int.TryParse(value, out flushIntervalMs) || flushIntervalMs < 0)
                {
                    throw new ArgumentException($"Invalid flush interval: {value}");
                }
            }
            else
            {
                var parts = arg.Split(':');
                if (parts.Length != 3)
                    throw new ArgumentException($"Invalid port forwarding format: {arg}");

                if (!int.TryParse(parts[0], out var localPort) || localPort < 1 || localPort > 65535)
                    throw new ArgumentException($"Invalid local port: {parts[0]}");

                if (!int.TryParse(parts[2], out var targetPort) || targetPort < 1 || targetPort > 65535)
                    throw new ArgumentException($"Invalid target port: {parts[2]}");

                forwardings.Add(new PortForwarding(localPort, parts[1], targetPort));
            }
        }

        if (forwardings.Count == 0)
            throw new ArgumentException("At least one port forwarding rule required");

        // Check for duplicate local ports
        var duplicates = forwardings.GroupBy(f => f.LocalPort).Where(g => g.Count() > 1).Select(g => g.Key);
        if (duplicates.Any())
            throw new ArgumentException($"Duplicate local port: {duplicates.First()}");

        return new Config(forwardings, outputFile, flushIntervalMs);
    }

    static async Task StartListener(PortForwarding forwarding, OutputWriter writer, ConnIdGenerator connIdGen)
    {
        var listener = new TcpListener(IPAddress.Any, forwarding.LocalPort);
        try
        {
            listener.Start();
            Console.Error.WriteLine($"Listening on port {forwarding.LocalPort} -> {forwarding.TargetHost}:{forwarding.TargetPort}");
        }
        catch (SocketException ex)
        {
            if (ex.SocketErrorCode == SocketError.AddressAlreadyInUse)
                throw new Exception($"Port {forwarding.LocalPort} is already in use");
            throw new Exception($"Failed to bind port {forwarding.LocalPort}: {ex.Message}");
        }

        while (true)
        {
            try
            {
                var client = await listener.AcceptTcpClientAsync();
                _ = Task.Run(async () => await HandleConnection(client, forwarding, writer, connIdGen));
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Accept error on port {forwarding.LocalPort}: {ex.Message}");
            }
        }
    }

    static async Task HandleConnection(TcpClient client, PortForwarding forwarding, OutputWriter writer, ConnIdGenerator connIdGen)
    {
        var connId = connIdGen.Next();
        TcpClient? server = null;

        try
        {
            // Connect to target
            server = new TcpClient();
            await server.ConnectAsync(forwarding.TargetHost, forwarding.TargetPort);

            var clientEp = client.Client.RemoteEndPoint?.ToString() ?? "unknown";
            var serverEp = $"{forwarding.TargetHost}:{forwarding.TargetPort}";

            // Log open event
            writer.WriteEvent(connId, "open", clientEp, serverEp);

            // Bidirectional forwarding
            var clientStream = client.GetStream();
            var serverStream = server.GetStream();

            var clientToServer = ForwardData(clientStream, serverStream, connId, clientEp, serverEp, writer);
            var serverToClient = ForwardData(serverStream, clientStream, connId, serverEp, clientEp, writer);

            await Task.WhenAny(clientToServer, serverToClient);

            // Determine who closed first
            var closedFrom = clientToServer.IsCompleted ? clientEp : serverEp;
            var closedTo = clientToServer.IsCompleted ? serverEp : clientEp;
            writer.WriteEvent(connId, "close", closedFrom, closedTo);
        }
        catch (Exception)
        {
            // Failed to connect to target - just close client silently
        }
        finally
        {
            client?.Close();
            server?.Close();
        }
    }

    static async Task ForwardData(NetworkStream from, NetworkStream to, string connId, string fromEp, string toEp, OutputWriter writer)
    {
        var buffer = new byte[32 * 1024]; // 32KB chunks
        try
        {
            while (true)
            {
                var bytesRead = await from.ReadAsync(buffer, 0, buffer.Length);
                if (bytesRead == 0)
                    break; // EOF

                await to.WriteAsync(buffer, 0, bytesRead);

                // Log data
                var data = new ReadOnlySpan<byte>(buffer, 0, bytesRead);
                writer.WriteData(connId, data, fromEp, toEp);
            }
        }
        catch
        {
            // Connection error - silent cleanup
        }
    }

    // Unit tests
    static void _TEST_ConnIdGenerator_GeneratesFiveCharBase62()
    {
        var gen = new ConnIdGenerator();
        var id1 = gen.Next();
        var id2 = gen.Next();

        // Check length
        if (id1.Length != 5 || id2.Length != 5)
        {
            Console.Error.WriteLine($"ConnID length wrong: {id1.Length}, {id2.Length}");
            Environment.Exit(1);
        }

        // Check base62 characters
        const string base62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
        foreach (var c in id1 + id2)
        {
            if (!base62.Contains(c))
            {
                Console.Error.WriteLine($"Invalid base62 character: {c}");
                Environment.Exit(1);
            }
        }

        // Check IDs are different (counter increments)
        if (id1 == id2)
        {
            Console.Error.WriteLine("ConnIDs should be unique");
            Environment.Exit(1);
        }
    }

    static void _TEST_OutputWriter_EncodesJsonEscapes()
    {
        // Test JSON escape sequences
        var tests = new (byte[] input, string expected)[]
        {
            (new byte[] { 0x22 }, "\\\""),  // "
            (new byte[] { 0x5C }, "\\\\"),  // \
            (new byte[] { 0x0A }, "\\n"),   // \n
            (new byte[] { 0x0D }, "\\r"),   // \r
            (new byte[] { 0x09 }, "\\t"),   // \t
            (new byte[] { 0x08 }, "\\b"),   // \b
            (new byte[] { 0x0C }, "\\f"),   // \f
        };

        foreach (var (input, expected) in tests)
        {
            var result = TestEncodeData(input);
            if (result != expected)
            {
                Console.Error.WriteLine($"JSON escape failed: input=0x{input[0]:X2} expected={expected} got={result}");
                Environment.Exit(1);
            }
        }
    }

    static void _TEST_OutputWriter_EncodesPercentEncoding()
    {
        // Test percent encoding
        var tests = new (byte[] input, string expected)[]
        {
            (new byte[] { 0x25 }, "%25"),       // % itself
            (new byte[] { 0x00 }, "%00"),       // null
            (new byte[] { 0x01 }, "%01"),       // control char
            (new byte[] { 0x1F }, "%1F"),       // control char
            (new byte[] { 0x7F }, "%7F"),       // DEL
            (new byte[] { 0x80 }, "%80"),       // non-ASCII
            (new byte[] { 0xFF }, "%FF"),       // high byte
        };

        foreach (var (input, expected) in tests)
        {
            var result = TestEncodeData(input);
            if (result != expected)
            {
                Console.Error.WriteLine($"Percent encoding failed: input=0x{input[0]:X2} expected={expected} got={result}");
                Environment.Exit(1);
            }
        }
    }

    static void _TEST_OutputWriter_PreservesPrintableAscii()
    {
        // Test printable ASCII is preserved
        var input = Encoding.ASCII.GetBytes("Hello World! <tag>");
        var result = TestEncodeData(input);
        var expected = "Hello World! <tag>";

        if (result != expected)
        {
            Console.Error.WriteLine($"Printable ASCII failed: expected={expected} got={result}");
            Environment.Exit(1);
        }
    }

    static void _TEST_OutputWriter_MixedEncoding()
    {
        // Test mixed content: printable + JSON escapes + percent encoding
        var input = new byte[] { 0x48, 0x69, 0x0A, 0x00, 0x25, 0x80 }; // "Hi\n\0%\x80"
        var expected = "Hi\\n%00%25%80";
        var result = TestEncodeData(input);

        if (result != expected)
        {
            Console.Error.WriteLine($"Mixed encoding failed: expected={expected} got={result}");
            Environment.Exit(1);
        }
    }

    // Helper to test OutputWriter's EncodeData
    static string TestEncodeData(byte[] data)
    {
        var span = new ReadOnlySpan<byte>(data);
        return OutputWriter.EncodeDataForTest(span);
    }
}

record Config(List<PortForwarding> PortForwardings, string? OutputFile, int FlushIntervalMs);
record PortForwarding(int LocalPort, string TargetHost, int TargetPort);

class ConnIdGenerator
{
    private const string Base62Chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    private long _counter;

    public ConnIdGenerator()
    {
        // Initialize with last 5 base62 digits of Unix timestamp
        var unixTime = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        _counter = unixTime;
    }

    public string Next()
    {
        var value = Interlocked.Increment(ref _counter);
        return ToBase62(value, 5);
    }

    private static string ToBase62(long value, int length)
    {
        var chars = new char[length];
        for (int i = length - 1; i >= 0; i--)
        {
            chars[i] = Base62Chars[(int)(value % 62)];
            value /= 62;
        }
        return new string(chars);
    }
}

class OutputWriter
{
    private readonly string? _filePath;
    private readonly int _flushIntervalMs;
    private readonly object _lock = new();
    private StringBuilder _inputBuffer = new();
    private StringBuilder _outputBuffer = new();
    private readonly Timer _swapTimer;

    public OutputWriter(string? filePath, int flushIntervalMs)
    {
        _filePath = filePath;
        _flushIntervalMs = flushIntervalMs;

        // Validate file path if specified
        if (_filePath != null)
        {
            try
            {
                var dir = Path.GetDirectoryName(_filePath);
                if (dir != null && !Directory.Exists(dir))
                    Directory.CreateDirectory(dir);

                // Fail-fast validation: ensure file can be written to at startup
                File.AppendAllText(_filePath, "");
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to create output file: {ex.Message}");
            }
        }

        // Start swap timer
        _swapTimer = new Timer(_ => SwapBuffers(), null, _flushIntervalMs, _flushIntervalMs);
    }

    private void SwapBuffers()
    {
        StringBuilder toWrite;

        lock (_lock)
        {
            if (_inputBuffer.Length == 0)
                return;

            // Swap buffers: save input buffer (has data), swap with output (empty)
            toWrite = _inputBuffer;
            _inputBuffer = _outputBuffer;
            _outputBuffer = toWrite;
            _inputBuffer.Clear();
        }

        // Write the buffer with data (outside lock)
        WriteToOutput(toWrite);
    }

    public void Flush()
    {
        // Force immediate buffer swap and write
        SwapBuffers();
    }

    private void WriteToOutput(StringBuilder buffer)
    {
        try
        {
            var content = buffer.ToString();
            if (_filePath != null)
            {
                File.AppendAllText(_filePath, content);
            }
            else
            {
                Console.Write(content);
                Console.Out.Flush();
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Output write failed: {ex.Message}");
            Environment.Exit(1);
        }
    }

    public void WriteEvent(string connId, string eventType, string from, string to)
    {
        var timestamp = GetTimestamp();
        var json = $"{{\"time\":\"{timestamp}\",\"ConnID\":\"{connId}\",\"event\":\"{eventType}\",\"from\":\"{from}\",\"to\":\"{to}\"}}";

        lock (_lock)
        {
            _inputBuffer.AppendLine(json);
        }
    }

    public void WriteData(string connId, ReadOnlySpan<byte> data, string from, string to)
    {
        var timestamp = GetTimestamp();
        var encodedData = EncodeData(data);

        // Manually construct JSON to be AOT-friendly
        var json = $"{{\"time\":\"{timestamp}\",\"ConnID\":\"{connId}\",\"data\":\"{encodedData}\",\"from\":\"{from}\",\"to\":\"{to}\"}}";

        lock (_lock)
        {
            _inputBuffer.AppendLine(json);
        }
    }

    private static string GetTimestamp()
    {
        return DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ");
    }

    private static string EncodeData(ReadOnlySpan<byte> data)
    {
        var sb = new StringBuilder(data.Length * 2);

        foreach (var b in data)
        {
            switch (b)
            {
                case 0x22: sb.Append("\\\""); break; // "
                case 0x5C: sb.Append("\\\\"); break; // \
                case 0x0A: sb.Append("\\n"); break;  // \n
                case 0x0D: sb.Append("\\r"); break;  // \r
                case 0x09: sb.Append("\\t"); break;  // \t
                case 0x08: sb.Append("\\b"); break;  // \b
                case 0x0C: sb.Append("\\f"); break;  // \f
                case 0x25: sb.Append("%25"); break;  // %

                default:
                    if (b >= 0x20 && b <= 0x7E)
                    {
                        // Printable ASCII
                        sb.Append((char)b);
                    }
                    else if (b < 0x20 || b == 0x7F || b >= 0x80)
                    {
                        // Control chars or non-ASCII
                        sb.AppendFormat("%{0:X2}", b);
                    }
                    break;
            }
        }

        return sb.ToString();
    }

    // Exposed for testing
    internal static string EncodeDataForTest(ReadOnlySpan<byte> data)
    {
        return EncodeData(data);
    }
}
