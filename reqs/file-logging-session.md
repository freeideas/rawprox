# File Logging Session Flow

**Source:** ./README.md, ./readme/LOG_FORMAT.md, ./readme/PERFORMANCE.md

Start RawProx with time-rotated file logging, proxy connections, and stop cleanly.

## $REQ_STARTUP_001: Start with Single Port Rule

**Source:** ./README.md (Section: "Quick Start")

Start RawProx with a single port rule in the format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`.

## $REQ_FILE_001: Log Destination Prefix

**Source:** ./README.md (Section: "Command-Line Format")

Log destinations must be specified with `@` prefix followed by directory path.

## $REQ_ARGS_013: Log Destination Format Validation

**Source:** ./README.md (Section: "Command-Line Format")

If a log destination doesn't start with `@` followed by a directory path, RawProx must show an error and exit.

## $REQ_ARGS_008: Flexible Argument Order

**Source:** ./readme/HELP.md (Section: "Usage")

Command-line arguments (flags, port rules, log destinations) must be accepted in any order.

## $REQ_ARGS_009: Accept Flush Millis Flag

**Source:** ./readme/HELP.md (Section: "Arguments")

RawProx must accept the `--flush-millis MS` command-line flag to set buffer flush interval in milliseconds.

## $REQ_ARGS_010: Accept Filename Format Flag

**Source:** ./readme/HELP.md (Section: "Arguments")

RawProx must accept the `--filename-format FORMAT` command-line flag to set log file naming pattern using strftime format.

## $REQ_STARTUP_004: Listen on Configured Ports

**Source:** ./README.md (Section: "Usage")

RawProx must bind to all local ports specified in port rules and accept incoming TCP connections on those ports.

## $REQ_FILE_002: Create Directory

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

If the target directory doesn't exist, it must be created automatically.

## $REQ_FILE_006: Hourly Rotation Default

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Default filename format must be `rawprox_%Y-%m-%d-%H.ndjson` for hourly rotation.

## $REQ_FILE_007: Custom Filename Format

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Filename format must support strftime patterns via `--filename-format` option.

## $REQ_FILE_008: Start Logging Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging starts to a directory, emit a `start-logging` event with directory path and filename_format.

## $REQ_PROXY_001: Accept Connections

**Source:** ./README.md (Section: "Quick Start")

RawProx must accept TCP connections on configured local ports.

## $REQ_PROXY_002: Connect to Target

**Source:** ./README.md (Section: "Command-Line Format")

For each incoming connection, RawProx must establish a connection to the target host and port.

## $REQ_STDOUT_005: Connection Open Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When a TCP connection opens, log an event with `event: "open"`, unique ConnID, timestamp, from address, and to address.

## $REQ_PROXY_003: Forward Traffic Bidirectionally

**Source:** ./README.md (Section: "What It Does")

RawProx must forward all data bidirectionally between client and target.

## $REQ_STDOUT_007: Traffic Data Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

For each chunk of transmitted data, log an event with ConnID, timestamp, data (JSON-escaped), from address, and to address.

## $REQ_FILE_010: Buffered Writes

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Events must be buffered in memory and flushed to disk at intervals.

## $REQ_FILE_011: Default Flush Interval

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Default flush interval must be 2000 milliseconds.

## $REQ_FILE_012: Configurable Flush Interval

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Flush interval must be configurable via `--flush-millis` option.

## $REQ_FILE_013: Batched File I/O

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Files must be opened, written with entire buffer, and closed during each flush cycle.

## $REQ_FILE_014: Minimum Flush Frequency

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Files must never be opened/written/closed more frequently than the flush interval.

## $REQ_FILE_017: Files Unlocked Between Flushes

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Log files must be kept closed and unlocked between flush cycles, allowing other processes to read, move, or analyze them while RawProx runs.

## $REQ_FILE_018: Minimize System Calls

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

File I/O must minimize system calls to approximately one write per flush interval.

## $REQ_FILE_003: Append Mode

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Files must be opened in append mode so restarts continue writing to the same file.

## $REQ_FILE_004: Never Overwrite

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Existing files must never be overwritten.

## $REQ_FILE_005: Create Files Automatically

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Files must be created automatically if they don't exist.

## $REQ_FILE_016: One JSON Object Per Line

**Source:** ./readme/LOG_FORMAT.md (Section: "Parsing")

Each log event in files must be a complete JSON object on a single line.

## $REQ_STDOUT_006: Connection Close Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When a TCP connection closes, log an event with `event: "close"`, ConnID, timestamp, from address, and to address.

## $REQ_SHUTDOWN_001: Ctrl-C Graceful Shutdown

**Source:** ./README.md (Section: "Stopping")

RawProx must shut down gracefully when receiving Ctrl-C signal.

## $REQ_FILE_009: Stop Logging Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging stops to a directory, emit a `stop-logging` event with directory path.

## $REQ_SHUTDOWN_010: Close All Connections

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must close all active connections.

## $REQ_SHUTDOWN_014: Stop All Listeners

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must stop all TCP listeners.

## $REQ_SHUTDOWN_018: Flush Buffered Logs

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must flush any buffered logs to disk before terminating.
