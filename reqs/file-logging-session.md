# File Logging Session

**Source:** ./README.md, ./readme/HELP.md, ./readme/LOG_FORMAT.md, ./readme/PERFORMANCE.md

Start RawProx with directory logging, proxy connections with time-rotated file output, and shut down cleanly.

## $REQ_FILE_001: Parse Port Rule Argument

**Source:** ./README.md (Section: "Usage")

Parse command-line argument in format `LOCAL_PORT:TARGET_HOST:TARGET_PORT` (e.g., `8080:example.com:80`).

## $REQ_FILE_002: Parse Log Destination Argument

**Source:** ./README.md (Section: "Usage")

Parse command-line argument in format `@DIRECTORY` (e.g., `@./logs` or `@/var/log/rawprox`).

## $REQ_FILE_003: Create Log Directory

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Automatically create the log directory if it doesn't exist.

## $REQ_FILE_004: Default Filename Format

**Source:** ./readme/HELP.md (Section: "Arguments"), ./readme/LOG_FORMAT.md (Section: "File Rotation")

Use `rawprox_%Y-%m-%d-%H.ndjson` as the default filename format for hourly rotation.

## $REQ_FILE_005: Custom Filename Format

**Source:** ./readme/HELP.md (Section: "Arguments")

Accept `--filename-format FORMAT` argument to specify custom strftime pattern for log filenames.

## $REQ_FILE_006: Generate Time-Based Filenames

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Generate log filenames based on current time using the strftime pattern.

## $REQ_FILE_007: Append Mode

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Open log files in append mode, allowing restarts to continue writing to the same file without overwriting.

## $REQ_FILE_008: Start Proxy Listener

**Source:** ./README.md (Section: "Usage")

Bind to the specified local port and listen for incoming TCP connections.

## $REQ_FILE_009: Accept Client Connection

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Accept incoming client connections on the local port.

## $REQ_FILE_010: Connect to Target Server

**Source:** ./README.md (Section: "What It Does")

Establish TCP connection to the target host and port specified in the port rule.

## $REQ_FILE_011: Log Connection Open Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Emit NDJSON event with `"event":"open"`, unique ConnID, timestamp, `from` address, and `to` address.

## $REQ_FILE_012: Forward Client to Server Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data received from client to target server.

## $REQ_FILE_013: Log Client to Server Traffic

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic event with ConnID, timestamp, `data` field, `from` (client address), and `to` (target server address).

## $REQ_FILE_014: Forward Server to Client Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data received from target server back to client.

## $REQ_FILE_015: Log Server to Client Traffic

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic event with ConnID, timestamp, `data` field, `from` (server address), and `to` (client address).

## $REQ_FILE_016: Handle Connection Close

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When connection closes, emit NDJSON event with `"event":"close"`, ConnID, timestamp, `from` and `to` addresses.

## $REQ_FILE_017: Memory Buffering

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Buffer log events in memory before writing to disk.

## $REQ_FILE_018: Default Flush Interval

**Source:** ./readme/HELP.md (Section: "Arguments"), ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Use 2000 milliseconds as the default flush interval.

## $REQ_FILE_019: Custom Flush Interval

**Source:** ./readme/HELP.md (Section: "Arguments")

Accept `--flush-millis MS` argument to configure buffer flush interval.

## $REQ_FILE_020: Batched File Writes

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Write events to disk in batches at flush intervals, not per-event.

## $REQ_FILE_021: Open-Write-Close Cycle

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Open file, write entire buffer, and close file during each flush cycle.

## $REQ_FILE_022: File Rotation on Time Change

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Switch to new log file when the filename (based on strftime pattern) changes due to time passing.

## $REQ_FILE_023: No File Overwrite

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Never overwrite existing log files, always append.

## $REQ_FILE_024: Never Block Network I/O

**Source:** ./readme/PERFORMANCE.md (Section: "Core Principle")

Never slow down network data forwarding due to file write operations.

## $REQ_FILE_025: Graceful Shutdown with Ctrl-C

**Source:** ./README.md (Section: "Stopping")

Respond to Ctrl-C (SIGINT) by closing all connections, stopping listeners, flushing buffered logs, and terminating.

## $REQ_FILE_026: Memory Buffer Growth on High Traffic

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

If network traffic rate exceeds disk write rate, buffer grows in memory.
