# Simple Proxy Session Flow

**Source:** ./README.md, ./readme/HELP.md, ./readme/LOG_FORMAT.md, ./readme/PERFORMANCE.md

Verify build artifacts, start RawProx, proxy connections with STDOUT logging, and stop cleanly.

## $REQ_RUNTIME_001: Single Executable

**Source:** ./README.md (Section: "Key Features")

RawProx must be distributed as a single executable.

## $REQ_RUNTIME_002: No External Dependencies

**Source:** ./README.md (Section: "Runtime Requirements")

RawProx must run without any external dependencies.

## $REQ_RUNTIME_003: Direct Execution

**Source:** ./README.md (Section: "Runtime Requirements")

RawProx must be runnable directly as an executable.

## $REQ_RUNTIME_004: AOT Compilation

**Source:** ./README.md (Section: "Runtime Requirements")

RawProx must be AOT-compiled using .NET 8 or above.

## $REQ_RUNTIME_006: Release Directory Contents

**Source:** ./README.md (Section: "Build Artifacts")

The `./release/` directory must contain only `rawprox.exe` with no other files (no .pdb, no .dll, no config files).

## $REQ_BUILD_001: Clean Release Directory

**Source:** ./README.md (Section: "Build Artifacts")

The build process must ensure no debug files (.pdb) or runtime files (.dll) are included in the `./release/` directory.

## $REQ_BUILD_002: Native AOT Single-File Compilation

**Source:** ./README.md (Section: "Build Artifacts")

The build process must compile as .NET Native AOT single-file with no dependencies.

## $REQ_BUILD_003: Place Executable in Release Directory

**Source:** ./README.md (Section: "Build Artifacts")

The build process must place only `rawprox.exe` in the `./release/` directory.

## $REQ_STARTUP_008: Start with Single Port Rule

**Source:** ./README.md (Section: "Quick Start")

Start RawProx with a single port rule in the format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`.

## $REQ_STARTUP_006: No MCP Server Without Flag

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior")

When started without the `--mcp` flag, RawProx must NOT operate as an MCP server and must NOT accept JSON-RPC control requests.

## $REQ_ARGS_012: Port Rule Format Validation

**Source:** ./README.md (Section: "Command-Line Format")

If a port rule doesn't follow the format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`, RawProx must show an error and exit.

## $REQ_ARGS_015: Flexible Argument Order

**Source:** ./readme/HELP.md (Section: "Usage")

Command-line arguments (flags, port rules, log destinations) must be accepted in any order.

## $REQ_STARTUP_009: Listen on Configured Ports

**Source:** ./README.md (Section: "Usage")

RawProx must bind to all local ports specified in port rules and accept incoming TCP connections on those ports.

## $REQ_STARTUP_010: Port Already in Use Error

**Source:** ./README.md (Section: "Quick Start")

If a local port is already in use, RawProx must show an error indicating which port is occupied.

## $REQ_STDOUT_001: Default to STDOUT

**Source:** ./README.md (Section: "Command-Line Format")

When no log destination is specified, logs must go to STDOUT only.

## $REQ_STDOUT_002: NDJSON Format

**Source:** ./readme/LOG_FORMAT.md (Section: "Log Format Specification")

All log output must be in NDJSON (Newline-Delimited JSON) format.

## $REQ_STDOUT_003: One JSON Object Per Line

**Source:** ./readme/LOG_FORMAT.md (Section: "Parsing")

Each log event must be a complete JSON object on a single line.

## $REQ_PROXY_018: Accept Connections

**Source:** ./README.md (Section: "Quick Start")

RawProx must accept TCP connections on configured local ports.

## $REQ_PROXY_019: Connect to Target

**Source:** ./README.md (Section: "Command-Line Format")

For each incoming connection, RawProx must establish a connection to the target host and port.

## $REQ_STDOUT_016: Connection Open Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When a TCP connection opens, log an event with `event: "open"`, unique ConnID, timestamp, from address, and to address.

## $REQ_STDOUT_022: Unique Connection IDs

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Each connection opened must receive a different ConnID to distinguish traffic from different connections.

## $REQ_STDOUT_009: ISO 8601 Timestamps

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

All timestamps must be in ISO 8601 format with microsecond precision in UTC.

## $REQ_PROXY_023: Forward Traffic Bidirectionally

**Source:** ./README.md (Section: "What It Does")

RawProx must forward all data bidirectionally between client and target.

## $REQ_PROXY_006: Capture All Traffic

**Source:** ./README.md (Section: "What It Does")

RawProx must log every byte sent and received during proxied connections.

## $REQ_PROXY_004: Full-Speed Proxying

**Source:** ./README.md (Section: "Key Features")

RawProx must provide full-speed TCP proxying without blocking network I/O.

## $REQ_PROXY_008: TCP Only

**Source:** ./README.md (Section: "Limitations")

RawProx must accept TCP port forwarding rules only.

## $REQ_PROXY_009: No TLS Decryption

**Source:** ./README.md (Section: "Limitations")

RawProx must capture encrypted bytes as-is without TLS/HTTPS decryption.

## $REQ_PROXY_007: Log Encrypted Traffic

**Source:** ./README.md (Section: "Limitations")

Encrypted traffic must be logged in its encrypted form.

## $REQ_PROXY_005: Never Block Network I/O

**Source:** ./readme/PERFORMANCE.md (Section: "Core Principle: Never Block Network I/O")

Network data forwarding must never be slowed down by file write operations.

## $REQ_STDOUT_021: Traffic Data Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

For each chunk of transmitted data, log an event with ConnID, timestamp, data (JSON-escaped), from address, and to address.

## $REQ_STDOUT_010: Binary Data Escaping

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Binary data must be JSON-escaped using standard JSON string escaping rules.

## $REQ_STDOUT_004: Buffered Output

**Source:** ./readme/PERFORMANCE.md (Section: "STDOUT Mode")

Events to STDOUT must be buffered and flushed at intervals.

## $REQ_PROXY_011: Memory Buffering for Slow Logging

**Source:** ./readme/PERFORMANCE.md (Section: "Core Principle: Never Block Network I/O")

If logging can't keep up with network traffic, events must be buffered in memory.

## $REQ_PROXY_013: Serialize Events to JSON

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Network events must be serialized to JSON and appended to memory buffer.

## $REQ_PROXY_014: Buffer Flush at Intervals

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Buffer must flush to disk at configurable intervals.

## $REQ_STDOUT_018: Connection Close Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When a TCP connection closes, log an event with `event: "close"`, ConnID, timestamp, from address, and to address.

## $REQ_STDOUT_013: Close Event Direction Swap

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

The `from` and `to` fields in close events may swap between open/close events depending on which side initiated the close.

## $REQ_SHUTDOWN_005: Ctrl-C Stopping Mechanism

**Source:** ./README.md (Section: "Stopping")

Ctrl-C must be available as a stopping mechanism for RawProx.

## $REQ_SHUTDOWN_009: Ctrl-C Graceful Shutdown

**Source:** ./README.md (Section: "Stopping")

RawProx must shut down gracefully when receiving Ctrl-C signal.

## $REQ_SHUTDOWN_013: Close All Connections

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must close all active connections.

## $REQ_SHUTDOWN_017: Stop All Listeners

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must stop all TCP listeners.

## $REQ_SHUTDOWN_021: Flush Buffered Logs

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must flush any buffered logs to disk before terminating.
