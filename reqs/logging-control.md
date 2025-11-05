# Logging Control Flow

**Source:** ./README.md, ./readme/LOG_FORMAT.md, ./readme/MCP_SERVER.md, ./readme/PERFORMANCE.md

Control logging destinations dynamically at runtime.

## $REQ_LOG_001: Start Logging Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

RawProx emits a start-logging event with time, event type "start-logging", and directory (string or null).

## $REQ_LOG_016: Start Logging Event Filename Format

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

The start-logging event includes filename_format field only when logging to directory destinations (not for STDOUT).

## $REQ_LOG_002: Stop Logging Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

RawProx emits a stop-logging event with time, event type "stop-logging", and directory (string or null).

## $REQ_LOG_003: Directory Null for STDOUT

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

In logging control events, directory is null for STDOUT logging.

## $REQ_LOG_004: Multiple Log Destinations via MCP

**Source:** ./README.md (Section: "Key Features"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

Via MCP, log to STDOUT and/or multiple directories simultaneously.

## $REQ_LOG_005: Stop All Logging

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When stop-logging tool is called with directory argument omitted, RawProx stops ALL logging (all destinations).

## $REQ_LOG_006: Stop STDOUT Logging

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When stop-logging tool is called with directory set to null, RawProx stops only STDOUT logging.

## $REQ_LOG_007: Stop Specific Directory Logging

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When stop-logging tool is called with directory set to a path, RawProx stops only logging to that directory.

## $REQ_LOG_008: Buffered STDOUT Logging

**Source:** ./readme/PERFORMANCE.md (Section: "STDOUT Mode")

When logging to STDOUT (no @DIRECTORY), events are buffered and flushed at intervals to prevent excessive syscalls.

## $REQ_LOG_009: Flush Interval Configuration

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments"), ./readme/PERFORMANCE.md (Section: "Batched File I/O")

RawProx accepts --flush-millis argument to set buffer flush interval in milliseconds (default: 2000).

## $REQ_LOG_010: Buffer Flush Timing

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Buffers flush to disk at intervals configured via --flush-millis.

## $REQ_LOG_011: Events After Flush Only

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Log events appear in files only after flush intervals, not immediately.

## $REQ_LOG_012: Buffer per Destination

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Events are serialized to JSON and appended to memory buffer with one buffer per destination file.

## $REQ_LOG_013: Batched File Writes

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Files are written in batches: accumulate events in memory buffer, wait for flush interval, open file, write entire buffer, close file, clear buffer.

## $REQ_LOG_014: Open-Write-Close Pattern

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Each flush performs open-write-close cycle to keep files closed and unlocked most of the time, allowing other processes to read/move/analyze log files.

## $REQ_LOG_015: Minimum Flush Frequency

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Files are never opened/written/closed more frequently than the flush interval.

## $REQ_LOG_018: Start Logging Tool Arguments

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

The start-logging tool accepts directory argument (string or null for STDOUT) and optional filename_format argument with default rawprox_%Y-%m-%d-%H.ndjson.

## $REQ_LOG_019: Stop Logging Tool Optional Directory

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

The stop-logging tool accepts optional directory argument (string for specific directory, null for STDOUT, or omitted to stop all).

