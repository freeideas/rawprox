# Simple Proxy Session Flow

**Source:** ./README.md, ./readme/COMMAND-LINE_USAGE.md, ./readme/LOG_FORMAT.md

Start RawProx with port rules, forward TCP connections, capture traffic, and shutdown cleanly.

## $REQ_SIMPLE_001: Single Executable

**Source:** ./README.md (Section: "Runtime Requirements")

RawProx runs as a single executable (`rawprox.exe`) without external dependencies.

## $REQ_SIMPLE_002A: Executable Extension on All Platforms

**Source:** ./README.md (Section: "Runtime Requirements")

The executable is named `rawprox.exe` on all platforms for consistency. Linux ignores the extension, while Windows requires it.

## $REQ_SIMPLE_027: AOT Compilation

**Source:** ./README.md (Section: "Runtime Requirements", "Build Artifacts")

The binary is AOT-compiled using .NET 8 or above.

## $REQ_SIMPLE_028: Build Artifacts Content

**Source:** ./README.md (Section: "Build Artifacts")

After building, the ./release/ directory contains only the single executable rawprox.exe with no debug files (.pdb) or runtime files (.dll).

## $REQ_SIMPLE_002: Accept Port Rule Argument

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts port rule arguments in format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`.

## $REQ_SIMPLE_003: Bind to Local Port

**Source:** ./README.md (Section: "Quick Start")

RawProx binds to the local port specified in the port rule.

## $REQ_SIMPLE_004: Port Already in Use Error

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Quick Tips")

If a port is already in use, RawProx shows an error to STDERR indicating which port is occupied and exits with a non-zero status.

## $REQ_SIMPLE_005: Forward TCP Connections

**Source:** ./README.md (Section: "What It Does")

RawProx forwards TCP connections from local port to target host and port.

## $REQ_SIMPLE_006: TCP Only

**Source:** ./README.md (Section: "Limitations")

RawProx accepts TCP port forwarding rules only. UDP is not supported.

## $REQ_SIMPLE_007: Multiple Port Rules

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts multiple port rules to proxy several services simultaneously.

## $REQ_SIMPLE_008: Independent Listeners

**Source:** ./README.md (Section: "Multiple Services")

Each port rule creates an independent listener that forwards connections independently.

## $REQ_SIMPLE_008A: Unique Connection IDs

**Source:** ./README.md (Section: "Multiple Services")

Connections are logged with unique connection IDs.

## $REQ_SIMPLE_009: STDOUT Logging by Default

**Source:** ./README.md (Section: "Usage"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

Without a log directory argument, logs go to STDOUT only.

## $REQ_SIMPLE_010: NDJSON Format

**Source:** ./README.md (Section: "Key Features"), ./readme/LOG_FORMAT.md (Section: "Parsing")

All logs use NDJSON (newline-delimited JSON) format with one complete JSON object per line.

## $REQ_SIMPLE_011: Connection Open Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

RawProx emits a connection open event with time, ConnID, event type "open", from address, and to address.

## $REQ_SIMPLE_012: Connection ID Format

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Connection identifier is an 8-character base-62 string. The first connection uses the last 8 base62 digits of microseconds since the Unix epoch. Each subsequent connection increments by one.

## $REQ_SIMPLE_013: Traffic Data Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

RawProx emits traffic events for each chunk of data transmitted with time, ConnID, data, from address, and to address.

## $REQ_SIMPLE_014: Data Escaping

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

The data field uses URL-encoding: printable ASCII (0x20-0x7E except %) as literal characters, percent sign as %25, standard JSON escapes for tab/newline/carriage return/quote/backslash, and all other bytes as %XX format.

## $REQ_SIMPLE_014A: Byte-Perfect Data Restoration

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Standard JSON parsing followed by URL-decoding restores byte-perfect data from the escaped format.

## $REQ_SIMPLE_015: Connection Close Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

RawProx emits a connection close event with time, ConnID, event type "close", from address, and to address.

## $REQ_SIMPLE_015A: Connection Direction Indication

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

The from and to fields indicate traffic direction and may swap between open/close events depending on which side initiated the close.

## $REQ_SIMPLE_016: ISO 8601 Timestamps

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

All event timestamps use ISO 8601 format with microsecond precision in UTC.

## $REQ_SIMPLE_017: No TLS Decryption

**Source:** ./README.md (Section: "Limitations")

RawProx captures encrypted bytes as-is without TLS/HTTPS decryption. Encrypted traffic is logged in its encrypted form.

## $REQ_SIMPLE_018: Non-blocking Logging

**Source:** ./README.md (Section: "Key Features"), ./readme/PERFORMANCE.md (Section: "Core Principle: Never Block Network I/O")

Network forwarding never waits for disk writes. Network data forwarding is never slowed down by file write operations.

## $REQ_SIMPLE_019: Memory Buffering

**Source:** ./readme/PERFORMANCE.md (Section: "Core Principle: Never Block Network I/O")

Log messages are buffered in memory until written to disk.

## $REQ_SIMPLE_019A: STDOUT Buffered Flushing

**Source:** ./readme/PERFORMANCE.md (Section: "STDOUT Mode")

When logging to STDOUT (no @DIRECTORY), events are buffered and flushed at intervals to prevent excessive syscalls.

## $REQ_SIMPLE_020: File Logging with @DIRECTORY

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts log directory argument in format `@DIRECTORY` to log to time-rotated files.

## $REQ_SIMPLE_021: Single Log Destination on Command Line

**Source:** ./README.md (Section: "Usage"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

Command-line accepts only one @DIRECTORY. All port rules log to the same destination.

## $REQ_SIMPLE_021A: Simple Proxy Mode Without MCP

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Examples"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When started with port rules but without --mcp-port, RawProx runs as a simple proxy forwarding traffic on those ports without MCP control available.

## $REQ_SIMPLE_022: Help Text When Nothing to Do

**Source:** ./README.md (Section: "Usage"), ./readme/COMMAND-LINE_USAGE.md (Section: "Quick Tips")

If RawProx has nothing to do (no valid --mcp-port and no valid port rules), it displays help text to STDERR and exits.

## $REQ_SIMPLE_023: No NDJSON When Showing Help

**Source:** ./README.md (Section: "Usage")

When displaying help text, RawProx does not output NDJSON.

## $REQ_SIMPLE_024: Application Shutdown

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When RawProx is terminated (via shutdown tool or process termination), the application exits the process.
