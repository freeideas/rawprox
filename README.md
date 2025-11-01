# RawProx

TCP proxy with full-speed traffic capture and dynamic runtime control.

## What It Does

RawProx forwards TCP connections while capturing all traffic in real-time. It logs every byte sent and received in a structured format (NDJSON) for analysis, debugging, and auditing.

## Key Features

- **Zero-copy TCP forwarding** -- Full-speed proxying without blocking network I/O
- **NDJSON logging** -- Structured logs with timestamps, connection IDs, and traffic data
- **Dynamic control** -- Add/remove port rules at runtime via JSON-RPC (opt-in with `--mcp` flag)
- **Time-rotated logs** -- Automatic file rotation (hourly, daily, per-minute, etc.)
- **Multiple outputs** -- Log to STDOUT and/or multiple directories simultaneously
- **No dependencies** -- Single executable, runs anywhere

## Quick Start

```bash
# Simple proxy (forward port 8080 to example.com:80, log to stdout)
rawprox 8080:example.com:80

# Log to time-rotated files
rawprox 8080:example.com:80 @./logs

# Multiple port rules
rawprox 8080:example.com:80 9000:api.example.com:443 @./logs

# With MCP server for dynamic control
rawprox --mcp 8080:example.com:80 @./logs
```

Stop with `Ctrl-C`.

If a port is already in use, RawProx will show an error indicating which port is occupied.

## Usage

### Command-Line Format

```bash
rawprox [--mcp] [PORT_RULE...] [LOG_DESTINATION...]
```

**Port rules:**
```
LOCAL_PORT:TARGET_HOST:TARGET_PORT
```

Examples:
- `8080:example.com:80` -- Forward local port 8080 to example.com:80
- `9000:api.example.com:443` -- Forward local port 9000 to api.example.com:443

**Log destinations:**
```
@DIRECTORY                    # Log to time-rotated files
```

Examples:
- `@./logs` -- Log to `./logs/` directory with hourly rotation
- `@/var/log/rawprox` -- Log to `/var/log/rawprox/` directory

**Without any log destination:** Logs go to STDOUT only.

**Without port rules and with --mcp:** RawProx shows usage message to STDERR and waits for MCP commands to add port rules.

**Without port rules and without --mcp:** RawProx shows usage message to STDERR and exits.

**Invalid port rules:** If arguments don't parse as valid port rules or destinations, RawProx shows an error and exits.

### Multiple Services

Monitor several services simultaneously by providing multiple port rules:

```bash
rawprox 8080:web.example.com:80 9000:api.example.com:443 3000:db.example.com:5432 @./logs
```

Each port rule creates an independent listener. Connections are forwarded independently and logged with unique connection IDs.

### Stopping

- **Ctrl-C** -- Graceful shutdown
- **MCP shutdown command** -- Graceful shutdown via JSON-RPC (when using `--mcp`)

On shutdown, RawProx closes all connections, stops all listeners, flushes buffered logs, and terminates.

## Runtime Requirements

RawProx runs without any external dependencies. It's a single executable that can be run directly.

## Limitations

- **TCP only** -- RawProx accepts TCP port forwarding rules only. UDP is not supported. TCP connections are proxied and logged.
- **No TLS decryption** -- RawProx captures encrypted bytes as-is without TLS/HTTPS decryption. Encrypted traffic is logged in its encrypted form (still useful for connection patterns and timing analysis).

## Documentation

- **[Log Format](./readme/LOG_FORMAT.md)** -- NDJSON event structure and parsing examples
- **[MCP Server](./readme/MCP_SERVER.md)** -- JSON-RPC API for dynamic control (requires `--mcp` flag)
- **[Performance](./readme/PERFORMANCE.md)** -- Memory buffering and I/O strategy

## Use Cases

- **API debugging** -- Capture request/response traffic between client and server
- **Protocol analysis** -- Log raw bytes for protocol reverse engineering
- **Connection monitoring** -- Track connection timing and data volume
- **Integration testing** -- Record traffic for replay and validation
- **Security auditing** -- Capture network activity for compliance
