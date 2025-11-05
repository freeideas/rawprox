# RawProx Help

## Usage

```
rawprox.exe [--mcp-port PORT] [--flush-millis MS] [--filename-format FORMAT] PORT_RULE... [@LOG_DIRECTORY]
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

**LOG_DIRECTORY**
Format: `@DIRECTORY`

Log traffic to time-rotated files in the specified directory.
Only one directory can be specified on the command line - all port rules log to the same destination.
For multiple log destinations, use `--mcp-port` mode (see MCP Server documentation).
If no directory is specified, logs go to STDOUT only.

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

- All logs use NDJSON (newline-delimited JSON) format
- Network I/O is never blocked by logging -- if logging can't keep up, RawProx buffers in memory
- If a port is already in use, RawProx will show an error to STDERR and exit with a non-zero status code
- If a log directory is specified without port rules, RawProx will show an error to STDERR and exit with a non-zero status code
- Use `--mcp-port` for runtime control without restarting the process
- RawProx runs if given `--mcp-port` or port rules (or both). It only shows help and exits when given neither.

## Documentation

For more details, see:
- **Log Format** -- NDJSON event structure and parsing examples
- **MCP Server** -- JSON-RPC API for dynamic control
- **Performance** -- Memory buffering and I/O strategy
