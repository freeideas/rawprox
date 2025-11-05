# RawProx Help

## Usage

```
rawprox.exe [--mcp-port PORT] [--flush-millis MS] [--filename-format FORMAT] PORT_RULE... [LOG_DESTINATION...]
```

## Arguments

**--mcp-port PORT**
Enable MCP (Model Context Protocol) server for dynamic runtime control over HTTP.
Specify a port number, or use 0 to let the system choose an available port.
When enabled, you can add/remove port rules and start/stop logging without restarting.

**--flush-millis MS**
Set buffer flush interval in milliseconds (default: 2000).
Lower values = more frequent disk writes, higher values = larger memory buffers.

**--filename-format FORMAT**
Set log file naming pattern using strftime format (default: `rawprox_%Y-%m-%d-%H.ndjson`).
Examples:
  - `rawprox_%Y-%m-%d.ndjson` -- Daily rotation
  - `rawprox_%Y-%m-%d-%H-%M.ndjson` -- Per-minute rotation
  - `rawprox.ndjson` -- No rotation (single file)

**PORT_RULE**
Format: `LOCAL_PORT:TARGET_HOST:TARGET_PORT`

Forward connections from a local port to a remote host and port.
You can specify multiple port rules to proxy several services simultaneously.

Examples:
  - `8080:example.com:80` -- Forward local port 8080 to example.com:80
  - `9000:api.example.com:443` -- Forward local port 9000 to api.example.com:443

**LOG_DESTINATION**
Format: `@DIRECTORY`

Log traffic to time-rotated files in the specified directory.
You can specify multiple destinations to log to several directories simultaneously.
If no destination is specified, logs go to STDOUT only.

Examples:
  - `@./logs` -- Log to ./logs/ directory
  - `@/var/log/rawprox` -- Log to /var/log/rawprox/ directory

## Examples

**Simple proxy with STDOUT logging:**
```bash
rawprox.exe 8080:example.com:80
```

**Proxy with file logging:**
```bash
rawprox.exe 8080:example.com:80 @./logs
```

**Multiple port rules:**
```bash
rawprox.exe 8080:example.com:80 9000:api.example.com:443 @./logs
```

**MCP server for dynamic control:**
```bash
rawprox.exe --mcp-port 8765 8080:example.com:80 @./logs
```

**MCP server with no initial port rules (wait for commands):**
```bash
rawprox.exe --mcp-port 8765
```

**Custom flush interval and daily rotation:**
```bash
rawprox.exe 8080:example.com:80 @./logs --flush-millis 5000 --filename-format "rawprox_%Y-%m-%d.ndjson"
```

## MCP Introspection

When using `--mcp-port`, the server will print the MCP endpoint URL on startup. Use any HTTP client to send MCP requests to that endpoint. See the MCP Server documentation for protocol details and examples.

## Quick Tips

- Press **Ctrl-C** to stop RawProx gracefully
- All logs use NDJSON (newline-delimited JSON) format
- Network I/O is never blocked by logging -- if logging can't keep up, RawProx buffers in memory
- If a port is already in use, RawProx will exit with an error
- Use `--mcp-port` for runtime control without restarting the process

## Documentation

For more details, see:
- **Log Format** -- NDJSON event structure and parsing examples
- **MCP Server** -- JSON-RPC API for dynamic control
- **Performance** -- Memory buffering and I/O strategy
