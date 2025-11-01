# Log Format Specification

RawProx outputs NDJSON (Newline-Delimited JSON) for all events, connections, and traffic.

## Output Destinations

Logs can be written to:
- **STDOUT** -- for piping to other tools
- **Time-rotated files** -- for persistent storage with automatic rotation

## Event Types

### MCP Server Events

Emitted when the MCP server starts (only when using `--mcp` flag):

```json
{"time":"2025-10-22T15:32:47.123456Z","event":"start-mcp","port":54321}
```

**Fields:**
- `time` -- ISO 8601 timestamp with microsecond precision (UTC)
- `event` -- Always `"start-mcp"`
- `port` -- TCP port number where MCP server is listening

**Note:** This event only appears when RawProx is started with the `--mcp` flag.

### Logging Control Events

Emitted when logging starts or stops:

```json
{"time":"2025-10-22T15:32:47.123456Z","event":"start-logging","directory":"./logs","filename_format":"rawprox_%Y-%m-%d-%H.ndjson"}
{"time":"2025-10-22T15:32:47.123456Z","event":"start-logging","directory":null}
{"time":"2025-10-22T15:32:48.123456Z","event":"stop-logging","directory":"./logs"}
{"time":"2025-10-22T15:32:48.123456Z","event":"stop-logging","directory":null}
```

**Fields:**
- `time` -- ISO 8601 timestamp with microsecond precision (UTC)
- `event` -- Either `"start-logging"` or `"stop-logging"`
- `directory` -- Directory path (string) or `null` for STDOUT
- `filename_format` -- Optional, only present in `start-logging` events for directory destinations

### Connection Events

Emitted when TCP connections open or close:

**Open:**
```json
{"time":"2025-10-22T15:32:47.123456Z","ConnID":"0tK3X","event":"open","from":"127.0.0.1:54321","to":"example.com:80"}
```

**Close:**
```json
{"time":"2025-10-22T15:32:48.456789Z","ConnID":"0tK3X","event":"close","from":"example.com:80","to":"127.0.0.1:54321"}
```

**Fields:**
- `time` -- ISO 8601 timestamp with microsecond precision (UTC)
- `ConnID` -- Connection identifier as 5-character base-62 string. Each connection opened receives a different ConnID to distinguish traffic from different connections.
- `event` -- Either `"open"` or `"close"`
- `from` -- Source address (IP:port)
- `to` -- Destination address (hostname/IP:port)

**Note:** `from` and `to` indicate traffic direction -- may swap between open/close events depending on which side initiated the close.

### Traffic Events

Emitted for each chunk of data transmitted:

```json
{"time":"2025-10-22T15:32:47.234567Z","ConnID":"0tK3X","data":"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n","from":"127.0.0.1:54321","to":"example.com:80"}
{"time":"2025-10-22T15:32:47.345678Z","ConnID":"0tK3X","data":"HTTP/1.1 200 OK\r\nContent-Length: 1234\r\n\r\n...","from":"example.com:80","to":"127.0.0.1:54321"}
```

**Fields:**
- `time` -- ISO 8601 timestamp with microsecond precision (UTC)
- `ConnID` -- Unique connection identifier (matches corresponding `open`/`close` events)
- `data` -- Raw bytes transmitted (JSON-escaped string)
- `from` -- Source address sending this data
- `to` -- Destination address receiving this data

**Note:** Binary data is JSON-escaped using standard JSON string escaping rules (`\u0000` for null bytes, `\n` for newlines, etc.).

## Complete Example Session

This example shows output when using the `--mcp` flag.

```json
{"time":"2025-10-22T15:32:47.000000Z","event":"start-mcp","port":54321}
{"time":"2025-10-22T15:32:47.100000Z","event":"start-logging","directory":"./logs","filename_format":"rawprox_%Y-%m-%d-%H.ndjson"}
{"time":"2025-10-22T15:32:47.123456Z","ConnID":"0tK3X","event":"open","from":"127.0.0.1:54321","to":"example.com:80"}
{"time":"2025-10-22T15:32:47.234567Z","ConnID":"0tK3X","data":"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n","from":"127.0.0.1:54321","to":"example.com:80"}
{"time":"2025-10-22T15:32:47.345678Z","ConnID":"0tK3X","data":"HTTP/1.1 200 OK\r\nContent-Length: 12\r\n\r\nHello World!","from":"example.com:80","to":"127.0.0.1:54321"}
{"time":"2025-10-22T15:32:48.456789Z","ConnID":"0tK3X","event":"close","from":"example.com:80","to":"127.0.0.1:54321"}
{"time":"2025-10-22T15:32:50.000000Z","event":"stop-logging","directory":"./logs"}
```

## File Rotation

When using `@DIRECTORY`, files rotate based on `--filename-format` (strftime pattern):

**Rotation patterns:**
- **Hourly** (default): `rawprox_%Y-%m-%d-%H.ndjson` → `rawprox_2025-10-22-15.ndjson`
- **Daily**: `rawprox_%Y-%m-%d.ndjson` → `rawprox_2025-10-22.ndjson`
- **Per-minute**: `rawprox_%Y-%m-%d-%H-%M.ndjson` → `rawprox_2025-10-22-15-32.ndjson`
- **Per-second** (testing): `rawprox_%Y-%m-%d-%H-%M-%S.ndjson` → `rawprox_2025-10-22-15-32-47.ndjson`
- **No rotation**: `rawprox.ndjson` → Single file

**File behavior:**
- Files are opened in **append mode** -- restarts continue writing to the same file
- Never overwrite existing files
- Files are created automatically if they don't exist
- Directory is created automatically if it doesn't exist

## Parsing

NDJSON is line-oriented JSON -- one complete JSON object per line.

**Parse example (bash):**
```bash
# Extract all connection opens
cat rawprox_2025-10-22-15.ndjson | jq 'select(.event == "open")'

# Extract all data from a specific connection
cat rawprox_2025-10-22-15.ndjson | jq 'select(.ConnID == "0tK3X" and .data)'

# Count connections
cat rawprox_2025-10-22-15.ndjson | jq 'select(.event == "open")' | wc -l
```

**Parse example (Python):**
```python
import json

with open('rawprox_2025-10-22-15.ndjson') as f:
    for line in f:
        event = json.loads(line)
        if event.get('event') == 'open':
            print(f"Connection {event['ConnID']}: {event['from']} -> {event['to']}")
```
