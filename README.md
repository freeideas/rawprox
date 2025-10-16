# RawProx - Raw Traffic Logging Proxy

A transparent TCP proxy that logs every byte of network traffic as it passes through. Outputs streaming NDJSON (Newline-Delimited JSON) for easy parsing and analysis.

> **Documentation**: [FOUNDATION.md](FOUNDATION.md) - project goals and philosophy | [doc/](doc/) - implementation notes

## Installation

Download pre-built binaries from [releases](https://github.com/yourusername/rawprox/releases), or build from source:

**Requirements:**
- .NET 8 SDK or later
- Native AOT workload (for standalone compilation)

```bash
# Build native executable with .NET Native AOT
uv run --script ./scripts/build.py
```

The executable will be at `./release/rawprox.exe` (Windows) or `./release/rawprox` (Linux/macOS).

## Quick Start

```bash
# Build native executable
uv run --script ./scripts/build.py

# Run: Listen on port 8080, forward to example.com:80
./release/rawprox.exe 8080:example.com:80

# In another terminal, send traffic through the proxy
curl http://localhost:8080
```

**Note**: If you get an error like "Port 8080 is already in use", another process is listening on that port. Choose a different port or stop the conflicting process.

For use cases and design philosophy, see [FOUNDATION.md](FOUNDATION.md).

## Usage

```bash
rawprox [ARGS ...]
```

**Arguments**:
- **Port forwarding rules** (required, at least one): `LOCAL_PORT:TARGET_HOST:TARGET_PORT`
  - `LOCAL_PORT` - Port to listen on for incoming connections
  - `TARGET_HOST` - Destination hostname or IP to forward traffic to
  - `TARGET_PORT` - Destination port to forward traffic to
- **Output file** (optional): `@FILEPATH` - Write output to file instead of stdout (directories created automatically)
- **Flush interval** (optional): `--flush-interval-ms=MILLISECONDS` - Buffer flush interval in milliseconds (default: 2000)

**Multiple ports**: You can specify multiple port forwardings to monitor several services simultaneously from one proxy instance.

**Examples:**
```bash
# Proxy local port 3306 to MySQL server
rawprox 3306:db.example.com:3306

# Intercept HTTP traffic
rawprox 8080:api.example.com:80

# Monitor Redis protocol
rawprox 6379:localhost:6380

# Monitor multiple services at once
rawprox 8080:api.example.com:80 3306:db.example.com:3306 6379:localhost:6379

# Save all traffic to a file (using @file argument)
rawprox 9000:server.com:443 @traffic.ndjson

# Fast flushing for testing (100ms interval)
rawprox 8080:api.example.com:80 --flush-interval-ms=100 @debug.ndjson

# Can also use shell redirection if preferred
rawprox 9000:server.com:443 > traffic.ndjson
```

## Output Format

RawProx outputs NDJSON (Newline-Delimited JSON) to stdout - one JSON object per line.

**Example:**
```json
{"time":"2025-10-14T15:32:47.123456Z","ConnID":"0tK3X","event":"open","from":"127.0.0.1:54321","to":"example.com:80"}
{"time":"2025-10-14T15:32:47.234567Z","ConnID":"0tK3X","data":"GET / HTTP/1.1\r\n...","from":"127.0.0.1:54321","to":"example.com:80"}
{"time":"2025-10-14T15:32:47.456789Z","ConnID":"0tK3X","event":"close","from":"example.com:80","to":"127.0.0.1:54321"}
```

Each line is a JSON object with fields like `time`, `ConnID`, `event`/`data`, `from`, `to`.

For complete format specification, see [SPECIFICATION.md](SPECIFICATION.md).
