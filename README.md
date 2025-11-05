# RawProx

TCP proxy with full-speed traffic capture and dynamic runtime control.

## What It Does

RawProx forwards TCP connections while capturing all traffic in real-time. It logs every byte sent and received in a structured format (NDJSON) for analysis, debugging, and auditing.

## Key Features

- **Non-blocking logging** -- Network forwarding never waits for disk writes
- **NDJSON logging** -- Structured logs with timestamps, connection IDs, and traffic data
- **Dynamic control** -- Add/remove port rules and log destinations at runtime via MCP
- **Time-rotated logs** -- Automatic file rotation (hourly, daily, per-minute, etc.)
- **Multiple log destinations** -- Via MCP, log to STDOUT and/or multiple directories simultaneously
- **No dependencies** -- Single executable, runs anywhere

## Quick Start

```bash
# Simple proxy (forward port 8080 to example.com:80, log to stdout)
rawprox.exe 8080:example.com:80

# Log to time-rotated files
rawprox.exe 8080:example.com:80 @logs

# Multiple port rules
rawprox.exe 8080:example.com:80 9000:api.example.com:443 @logs

# With MCP server for dynamic control
rawprox.exe --mcp-port 8765 8080:example.com:80 @logs
```

**Error conditions:**
- If a port is already in use, RawProx will show an error to STDERR indicating which port is occupied, and will exit with a non-zero status.
- If a log directory is specified (`@DIRECTORY`) without any port rules, RawProx will show an error to STDERR and exit with a non-zero status. Use MCP's `start-logging` tool for dynamic logging control.

## Usage

### Command-Line Format

```bash
rawprox.exe [--mcp-port PORT] [PORT_RULE...] [@LOG_DIRECTORY]
```

**Port rules:**
```
LOCAL_PORT:TARGET_HOST:TARGET_PORT
```

Examples:
- `8080:example.com:80` -- Forward local port 8080 to example.com:80
- `9000:api.example.com:443` -- Forward local port 9000 to api.example.com:443

**Log directory:**
```
@DIRECTORY                    # Log to time-rotated files in this directory
```

Examples:
- `@./logs` -- Log to `./logs/` directory with hourly rotation
- `@/var/log/rawprox` -- Log to `/var/log/rawprox/` directory

**Note:** Command-line accepts only one @DIRECTORY. All port rules log to the same destination. For multiple log destinations, use MCP mode (see MCP Server documentation).

**Without any log directory:** Logs go to STDOUT only.

**With --mcp-port (no port rules):** RawProx runs and waits for MCP commands to add port rules dynamically.

**With port rules (no --mcp-port):** RawProx runs as a simple proxy forwarding traffic on those ports.

**With both --mcp-port and port rules:** RawProx runs, forwards traffic, and accepts MCP commands for dynamic control.

**With nothing to do:** If RawProx has nothing to do (no valid `--mcp-port` and no valid port rules), it displays help text to STDERR and exits (no NDJSON output).

### Multiple Services

Monitor several services simultaneously by providing multiple port rules:

```bash
rawprox.exe 8080:web.example.com:80 9000:api.example.com:443 3000:db.example.com:5432 @logs
```

Each port rule creates an independent listener. Connections are forwarded independently and logged with unique connection IDs.

## Runtime Requirements

RawProx runs without any external dependencies. It's a single executable (`rawprox.exe`, even on Linux) that can be run directly.

The binary is AOT-compiled using .NET 8 or above.

**Note:** The `.exe` extension is used on all platforms for consistency. Linux ignores the extension, while Windows requires it.

## Build Artifacts

After building, the `./release/` directory must contain **only** the single executable:
- `rawprox.exe` -- Single AOT-compiled binary (no .pdb, .dll, or config files)

The build process should:
1. Compile as .NET Native AOT (single-file, no dependencies)
2. Place only `rawprox.exe` in `./release/`
3. Ensure no debug files (.pdb) or runtime files (.dll) are included

## Limitations

- **TCP only** -- RawProx accepts TCP port forwarding rules only. UDP is not supported. TCP connections are proxied and logged.
- **No TLS decryption** -- RawProx captures encrypted bytes as-is without TLS/HTTPS decryption. Encrypted traffic is logged in its encrypted form (still useful for connection patterns and timing analysis).

## Documentation

- **[Help Text](./readme/COMMAND-LINE_USAGE.md)** -- Complete usage and examples (this information is shown when there are no valid command-line arguments)
- **[Log Format](./readme/LOG_FORMAT.md)** -- NDJSON event structure and parsing examples
- **[MCP Server](./readme/MCP_SERVER.md)** -- JSON-RPC API for dynamic control (requires `--mcp-port` flag)
- **[Performance](./readme/PERFORMANCE.md)** -- Memory buffering and I/O strategy

## Use Cases

- **API debugging** -- Capture request/response traffic between client and server
- **Protocol analysis** -- Log raw bytes for protocol reverse engineering
- **Connection monitoring** -- Track connection timing and data volume
- **Integration testing** -- Record traffic for replay and validation
- **Security auditing** -- Capture network activity for compliance
