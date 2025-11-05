# Simple Proxy Session

**Source:** ./README.md, ./readme/HELP.md, ./readme/LOG_FORMAT.md

Start RawProx with a single port rule, proxy connections, log traffic to STDOUT, and shut down cleanly.

## $REQ_SIMPLE_001: Parse Port Rule Argument

**Source:** ./README.md (Section: "Usage")

Parse command-line argument in format `LOCAL_PORT:TARGET_HOST:TARGET_PORT` (e.g., `8080:example.com:80`).

## $REQ_SIMPLE_002: Start Proxy Listener

**Source:** ./README.md (Section: "Usage")

Bind to the specified local port and listen for incoming TCP connections.

## $REQ_SIMPLE_003: Accept Client Connection

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Accept incoming client connections on the local port.

## $REQ_SIMPLE_004: Connect to Target Server

**Source:** ./README.md (Section: "What It Does")

Establish TCP connection to the target host and port specified in the port rule.

## $REQ_SIMPLE_005: Log Connection Open Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Emit NDJSON event with `"event":"open"`, unique ConnID (8-character base-62 string), timestamp, `from` address, and `to` address.

## $REQ_SIMPLE_006: Forward Client to Server Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data received from client to target server.

## $REQ_SIMPLE_007: Log Client to Server Traffic

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic event with ConnID, timestamp, `data` field containing transmitted bytes, `from` (client address), and `to` (target server address).

## $REQ_SIMPLE_008: Forward Server to Client Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data received from target server back to client.

## $REQ_SIMPLE_009: Log Server to Client Traffic

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic event with ConnID, timestamp, `data` field containing transmitted bytes, `from` (server address), and `to` (client address).

## $REQ_SIMPLE_010: Handle Connection Close

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When connection closes, emit NDJSON event with `"event":"close"`, ConnID, timestamp, `from` and `to` addresses.

## $REQ_SIMPLE_011: Binary Data Escaping

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

JSON-escape binary data in `data` field using standard JSON escaping rules.

## $REQ_SIMPLE_012: Unique Connection Identifiers

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Assign a different ConnID to each connection opened, ensuring all events for the same connection share the same ConnID.

## $REQ_SIMPLE_012A: ConnID Generation Algorithm

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Generate ConnID as 8-character base-62 string where the first connection uses the last 8 base62 digits of microseconds since Unix epoch, and each subsequent connection increments by one.

## $REQ_SIMPLE_013: Timestamp Format

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Use ISO 8601 timestamp format with microsecond precision in UTC for all events.

## $REQ_SIMPLE_014: NDJSON Format

**Source:** ./readme/LOG_FORMAT.md (Section: "Parsing")

Output one complete JSON object per line, with no comma separators between objects.

## $REQ_SIMPLE_015: Default STDOUT Logging

**Source:** ./README.md (Section: "Usage"), ./readme/LOG_FORMAT.md (Section: "Output Destinations")

When no log destination is specified, write all events to STDOUT.

## $REQ_SIMPLE_016: Graceful Shutdown with Ctrl-C

**Source:** ./README.md (Section: "Stopping")

Respond to Ctrl-C (SIGINT) by closing all connections, stopping listeners, flushing buffered logs, and terminating.

## $REQ_SIMPLE_017: Full-Speed Forwarding

**Source:** ./README.md (Section: "Key Features"), ./readme/PERFORMANCE.md (Section: "Core Principle")

Maintain full throughput for proxied connections without blocking or slowing down network I/O due to logging operations.

## $REQ_SIMPLE_018: No External Dependencies

**Source:** ./README.md (Section: "Runtime Requirements")

Run as a single executable without requiring external libraries or runtime dependencies.

## $REQ_SIMPLE_019: AOT Compilation

**Source:** ./README.md (Section: "Build Artifacts")

Compile as .NET Native AOT (single-file, no dependencies).

## $REQ_SIMPLE_020: Single Executable Output

**Source:** ./README.md (Section: "Build Artifacts")

Place only rawprox.exe in ./release/ directory after build, with no debug files (.pdb) or runtime files (.dll) included.

## $REQ_SIMPLE_021: Cross-Platform .exe Extension

**Source:** ./README.md (Section: "Runtime Requirements")

Use .exe extension on all platforms (Linux and Windows) for consistency.

## $REQ_SIMPLE_022: STDOUT Buffered Flushing

**Source:** ./readme/PERFORMANCE.md (Section: "STDOUT Mode")

When logging to STDOUT, buffer events in memory and flush at intervals (not per-event).
