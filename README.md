# RawProx - Raw Traffic Logging Proxy

A simple TCP proxy that logs every byte of traffic in both directions as JSON.

## Building

```bash
cargo build --release
```

The executable will be created at `target/release/rawprox`.

## Usage

```bash
rawprox 8080 example.com 8081
```

### Parameters (all are required)

- Local port to listen on for incoming connections
- Destination hostname or IP address to forward traffic to
- Destination port to forward traffic to

### Log Format

Output is a JSON array to stdout with one entry per line. Each connection (client→proxy→target) gets a unique connection ID:

```json
[
{"id":1,"stamp":"2025-07-22_23:45:22.123456","type":"local_open","client":"192.168.1.100:54321"},
{"id":1,"stamp":"2025-07-22_23:45:22.234567","type":"remote_open","target":"example.com:8081"},
{"id":1,"stamp":"2025-07-22_23:45:22.392838","direction":">","data":"GET /favicon.ico HTTP/1.1\r\nHost: example.com\r\n\r\n"},
{"id":1,"stamp":"2025-07-22_23:45:22.425123","direction":"<","data":"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n\u0089PNG\r\n\u001a\n\u0000\u0000\u0000\rIHDR\u0000\u0000\u0000\u0010\u0000\u0000\u0000\u0010\u0008\u0006"},
{"id":2,"stamp":"2025-07-22_23:45:22.789012","type":"local_open","client":"192.168.1.101:54322"},
{"id":2,"stamp":"2025-07-22_23:45:22.890123","type":"remote_open","target":"example.com:8081"},
{"id":1,"stamp":"2025-07-22_23:45:23.567890","type":"remote_close"},
{"id":1,"stamp":"2025-07-22_23:45:23.678901","type":"local_close"},
{"id":2,"stamp":"2025-07-22_23:45:24.012345","type":"remote_close"},
{"id":2,"stamp":"2025-07-22_23:45:24.123456","type":"local_close"}
]
```

#### Common Fields:
- `id` - Connection ID (auto-incrementing integer, unique per client→proxy→target connection). This enables multiple simultaneous conversations to be distinguished from one another in the log output.
- `stamp` - Timestamp in YYYY-MM-DD_HH:MM:SS.microseconds format

#### Connection Events:
- `type: "local_open"` - Client connected to proxy's local port
  - `client` - Client address and port (e.g., "192.168.1.100:54321")
- `type: "remote_open"` - Proxy connected to target server
  - `target` - Target host and port (e.g., "example.com:8081")
- `type: "local_close"` - Client disconnected from proxy
- `type: "remote_close"` - Target server closed connection

#### Data Transfer Events:
- `direction` - `<` for client-to-server, `>` for server-to-client
- `data` - JSON-escaped string with printable ASCII kept readable, binary as \uXXXX

### Features

- Transparent TCP proxy - forwards all traffic unchanged
- Complete traffic logging in both directions
- JSON format for easy parsing and analysis
- JSON escaping keeps text readable while handling binary data
- 32KB buffer size so transmissions will rarely be divided into multiple console messages
- Async I/O with Tokio for high performance and concurrent connections