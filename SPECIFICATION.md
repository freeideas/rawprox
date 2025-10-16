# RawProx Technical Specification

Version: 2.0
Last Updated: 2025-10-16

> **Documentation**: [FOUNDATION.md](FOUNDATION.md) - project goals and philosophy | [README.md](README.md) - usage examples and quick start | [doc/](doc/) - implementation notes

## 1. Overview

RawProx is a transparent TCP proxy that intercepts network traffic between clients and servers, forwarding all data unchanged while logging every transmitted byte as NDJSON (Newline-Delimited JSON). Output is written to stdout by default, or to a file when specified via `@FILEPATH` argument.

### 1.1 Design Goals

See [FOUNDATION.md](FOUNDATION.md) for complete design goals and philosophy.

## 2. System Architecture

### 2.1 Data Flow

1. Client connects to RawProx's local port
2. RawProx connects to target server → `open` event logged
3. Bidirectional data transfer:
   - Client→Server data logged with `from`=client, `to`=server
   - Server→Client data logged with `from`=server, `to`=client
4. Either side closes → `close` event logged with `from`=closing side, `to`=other side

### 2.2 Concurrency Model

- Asynchronous I/O using Tokio runtime
- Multiple listening sockets bound concurrently (one per port forwarding rule)
- Each client connection spawns an independent handler task
- Each handler spawns two subtasks:
  - Client→Server forwarding and logging
  - Server→Client forwarding and logging
- Double-buffered output system prevents network threads from blocking on I/O (see §8.1)

## 3. Command Line Interface

### 3.1 Syntax

```
rawprox [ARGS ...]
```

Where `ARGS` can be:
- Port forwarding rules: `LOCAL_PORT:TARGET_HOST:TARGET_PORT`
- Output file specifier: `@FILEPATH` (optional)
- Flush interval: `--flush-interval-ms=MILLISECONDS` (optional)

### 3.2 Parameters

#### 3.2.1 Port Forwarding Rules

Each port forwarding rule has the format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`:

| Component | Type | Range | Description |
|-----------|------|-------|-------------|
| `LOCAL_PORT` | unsigned 16-bit integer | 1-65535 | Port to bind for incoming connections |
| `TARGET_HOST` | string | hostname or IP | Destination to forward traffic to |
| `TARGET_PORT` | unsigned 16-bit integer | 1-65535 | Destination port |

**Requirements**:
- At least one port forwarding rule must be specified
- Multiple rules can be specified to monitor multiple services simultaneously
- Each local port must be unique (no duplicate local ports)

#### 3.2.2 Output File Specifier

Format: `@FILEPATH`

**Behavior**:
- If specified, all NDJSON output is written to `FILEPATH` instead of stdout
- Parent directories are created automatically if they don't exist
- File writes use double-buffering with minimum 2-second intervals between writes (see §8.1 and [doc/DOUBLE_BUFFERING.md](doc/DOUBLE_BUFFERING.md) for complete details)
- Optional: without this argument, output goes to stdout (default behavior)
- Can appear at any position among the arguments
- If multiple `@` arguments are specified, the last one takes precedence

**Example**:
```bash
# Multiple port forwardings with file output
rawprox 8080:api.example.com:80 3306:db.example.com:3306 @output.ndjson
```

#### 3.2.3 Flush Interval

Format: `--flush-interval-ms=MILLISECONDS`

**Behavior**:
- Sets the buffer flush interval in milliseconds
- Default: 2000ms (2 seconds) per §8.1
- Minimum recommended: 100ms for testing, 2000ms for production (especially network drives)
- Can appear at any position among the arguments
- If multiple `--flush-interval-ms` arguments are specified, the last one takes precedence

**Purpose**:
- Controls how frequently buffered log entries are written to output
- Higher values reduce I/O overhead and prevent issues on network drives (see [doc/LESSONS_LEARNED.md](doc/LESSONS_LEARNED.md))
- Lower values provide more real-time output (useful for testing)

**Examples**:
```bash
# Fast flushing for testing (100ms)
rawprox 8080:example.com:80 --flush-interval-ms=100

# Default 2-second interval (recommended for production)
rawprox 8080:example.com:80 @output.ndjson

# Explicit 2-second interval for network drive
rawprox 8080:example.com:80 @//server/share/traffic.ndjson --flush-interval-ms=2000

# Immediate flushing (0ms, not recommended)
rawprox 8080:example.com:80 --flush-interval-ms=0
```

### 3.3 Error Behavior

- **Invalid arguments**: Print usage/error to stderr, exit 1
  - Missing arguments (no port forwarding rules)
  - Malformed port forwarding rule (wrong format, invalid port numbers)
  - Duplicate local ports
- **Output file failure**: Print error message to stderr, exit 1
  - Parent directories cannot be created
  - File cannot be opened or written to at startup (fail-fast validation)
- **Bind failure**: Print clear error message to stderr indicating the port and reason, exit 1
  - Common case: "Error: Port XXXX is already in use" (when another process is listening)
  - General case: Include the system error for other bind failures
- **Accept failure**: Log to stderr, continue running
- **Connection errors**: Silent cleanup, do not crash

## 4. NDJSON Output Format

### 4.1 General Structure

- NDJSON output: one object per line, UTF-8, LF terminator, compact
- Output destination: stdout (default) or file specified by `@FILEPATH` argument (append mode)
- **Two entry types**: Event entries (with `event` field) and Data entries (with `data` field)
- **Field order**: `time`, `ConnID`, then `event`/`data`, then `from`, `to`

### 4.2 Log Entry Schema

There are two types of log entries:

#### 4.2.1 Event Entry (Connection Open/Close)

```json
{
  "time": "<ISO8601_timestamp>",
  "ConnID": "<base62_id>",
  "event": "<event_type>",
  "from": "<source_address:port>",
  "to": "<destination_address:port>"
}
```

**Event types:**
- `"open"` - Connection established (from=client, to=server)
- `"close"` - Connection closed (from=closing side, to=other side)

**Examples:**
```json
{"time":"2025-10-14T15:32:47.123456Z","ConnID":"0tK3X","event":"open","from":"192.168.1.100:52341","to":"example.com:80"}
{"time":"2025-10-14T15:32:47.999999Z","ConnID":"0tK3X","event":"close","from":"example.com:80","to":"192.168.1.100:52341"}
```

#### 4.2.2 Data Entry (Traffic)

```json
{
  "time": "<ISO8601_timestamp>",
  "ConnID": "<base62_id>",
  "data": "<json_escaped_payload>",
  "from": "<source_address:port>",
  "to": "<destination_address:port>"
}
```

**Example:**
```json
{"time":"2025-10-14T15:32:47.234567Z","ConnID":"0tK3X","data":"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n","from":"192.168.1.100:52341","to":"example.com:80"}
```

### 4.3 Field Specifications

#### time
ISO 8601 with microsecond precision, UTC: `YYYY-MM-DDTHH:MM:SS.microseconds Z`
Example: `2025-10-14T15:32:47.123456Z`

#### ConnID
5-character base62 string (`0-9A-Za-z`), unique per connection.
Initial value: Last 5 base62 digits of Unix timestamp. Increments by 1 per connection.
Base62 ordering: `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz`

#### event
String: `"open"` (connection established) or `"close"` (connection terminated).
Only in event entries.

#### data
String containing payload bytes with JSON escaping (see §5).
Data is logged in 32KB chunks as transmitted. Only in data entries.

#### from / to
Format: `address:port`
IPv4: `192.168.1.100:52341` | IPv6: `[2001:db8::1]:52341`

**Direction semantics:**
- Data entries: `from`=sender, `to`=receiver
- `open` event: `from`=client, `to`=server
- `close` event: `from`=closing side, `to`=other side

## 5. Data Encoding

### 5.1 Encoding Rules

The `data` field contains payload bytes encoded with **standard JSON escape sequences for common control characters and percent-encoding for other non-printable/non-ASCII bytes**:

#### 5.1.1 Standard JSON escape sequences:

**JSON-escaped characters (use backslash escapes):**
- `"` (0x22) → `\"`
- `\` (0x5C) → `\\`
- `\n` (0x0A) → `\n` (line feed)
- `\r` (0x0D) → `\r` (carriage return)
- `\t` (0x09) → `\t` (tab)
- `\b` (0x08) → `\b` (backspace)
- `\f` (0x0C) → `\f` (form feed)

#### 5.1.2 Percent-encoded characters:

**Percent character (meta-character):**
- `%` (0x25) → `%25`

**Other control characters (0x00-0x1F, 0x7F)** except those with JSON escapes:
- Encoded as `%XX` (percent-encoded 2-digit uppercase hex)
- Examples: `0x00` → `%00`, `0x01` → `%01`, `0x1F` → `%1F`, `0x7F` → `%7F`

**Non-ASCII bytes (0x80-0xFF):**
- All encoded as `%XX` (percent-encoded 2-digit uppercase hex)
- Examples: `0x80` → `%80`, `0xE9` → `%E9`, `0xFF` → `%FF`

#### 5.1.3 Characters preserved as-is:

**Printable ASCII (0x20-0x7E)** except `"`, `\`, and `%`:
- Space (0x20) through tilde (0x7E)
- Includes: letters, digits, punctuation marks
- Examples: `<`, `>`, `{`, `}`, `[`, `]`, `'`, `/`, `:`, `;`, etc.

### 5.2 Encoding Examples

| Input Bytes | Encoded Output | Description |
|-------------|----------------|-------------|
| `Hello World` | `Hello World` | Printable ASCII |
| `Line1\nLine2` | `Line1\nLine2` | Line feed (JSON escape) |
| `\r\n` | `\r\n` | CRLF sequence (JSON escapes) |
| `Tab\there` | `Tab\there` | Tab (JSON escape) |
| `Say "Hi"` | `Say \"Hi\"` | Quotes escaped |
| `Path\to\file` | `Path\\to\\file` | Backslashes escaped |
| `100%` | `100%25` | Percent sign |
| `50% off\n` | `50%25 off\n` | Percent + line feed |
| `\x00` | `%00` | Null byte |
| `\x01\x02` | `%01%02` | Other control chars |
| `\x89PNG` | `%89PNG` | PNG signature |
| `\xFF\xFE` | `%FF%FE` | High bytes |
| `café` (UTF-8: 0x63 0x61 0x66 0xC3 0xA9) | `caf%C3%A9` | Non-ASCII é bytes |
| `\b\f` | `\b\f` | Backspace + form feed (JSON escapes) |


## 6. Network Behavior

- Bind to `0.0.0.0` on local port
- Async accept loop (log errors to stderr, continue)
- DNS resolution per connection (no caching)
- Failed target connection: close client socket, no log entries
- Connection termination: EOF (0-byte read) logs `close` event, both directions logged independently

## 7. Streaming Capture

**No message buffering**: Each read operation's data is logged immediately. No aggregation, no protocol-level grouping. Large messages span multiple log lines with same `ConnID`.

To reconstruct: group by `ConnID`, sort by `time`, concatenate `data` fields.

## 8. Concurrency and Output Buffering

### 8.1 Double-Buffered Output System

Output (stdout or file) uses double-buffering with minimum 2-second swap intervals to prevent network threads from blocking on I/O operations.

**Output destinations:**
- Stdout (default): When no `@FILEPATH` specified
- File: When `@FILEPATH` specified, uses open-append-close per write cycle

See [doc/DOUBLE_BUFFERING.md](doc/DOUBLE_BUFFERING.md) for complete architecture and implementation details.

### 8.2 Async Runtime

- Tokio async runtime: one task per connection, two subtasks for bidirectional forwarding
- ConnID counter: atomic u64 with SeqCst ordering
- Per-connection state is task-local (no shared state)

## 9. Error Handling

- Invalid arguments or bind failure: print error to stderr, exit 1
- Connection errors: cleanup, log close event if connection was established
- Output writes: all errors are reported (never ignored), program exits on write failure
- Buffered output: on abrupt termination (kill -9, crash), up to 2 seconds of data in Input Buffer may be lost (bounded by swap interval)

