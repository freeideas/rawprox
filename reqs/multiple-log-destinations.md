# Multiple Log Destinations Flow

**Source:** ./README.md, ./readme/LOG_FORMAT.md

Start RawProx with multiple simultaneous log destinations (STDOUT and multiple directories), proxy traffic, and verify all destinations receive events through shutdown.

## $REQ_STARTUP_007: Start with Single Port Rule

**Source:** ./README.md (Section: "Quick Start")

Start RawProx with a single port rule in the format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`.

## $REQ_FILE_025: Multiple Destinations

**Source:** ./README.md (Section: "Key Features")

RawProx must support logging to STDOUT and multiple directories simultaneously.

## $REQ_FILE_019: Multiple Start Logging Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging starts to multiple destinations, emit a separate `start-logging` event for each destination.

## $REQ_FILE_020: Events Written to All Destinations

**Source:** ./README.md (Section: "Key Features")

All log events (connection opens, data transfers, closes) must be written to all active log destinations.

## $REQ_PROXY_017: Accept Connections

**Source:** ./README.md (Section: "Quick Start")

RawProx must accept TCP connections on configured local ports.

## $REQ_PROXY_022: Forward Traffic Bidirectionally

**Source:** ./README.md (Section: "What It Does")

RawProx must forward all data bidirectionally between client and target.

## $REQ_STDOUT_015: Connection Open Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When a TCP connection opens, log an event with `event: "open"`, unique ConnID, timestamp, from address, and to address.

## $REQ_STDOUT_020: Traffic Data Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

For each chunk of transmitted data, log an event with ConnID, timestamp, data (JSON-escaped), from address, and to address.

## $REQ_STDOUT_017: Connection Close Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When a TCP connection closes, log an event with `event: "close"`, ConnID, timestamp, from address, and to address.

## $REQ_FILE_021: Independent Directory Buffers

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Each log destination must maintain its own memory buffer and flush independently at the configured interval.

## $REQ_SHUTDOWN_008: Ctrl-C Graceful Shutdown

**Source:** ./README.md (Section: "Stopping")

RawProx must shut down gracefully when receiving Ctrl-C signal.

## $REQ_FILE_022: Multiple Stop Logging Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging stops, emit a separate `stop-logging` event for each active destination.

## $REQ_SHUTDOWN_012: Close All Connections

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must close all active connections.

## $REQ_SHUTDOWN_016: Stop All Listeners

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must stop all TCP listeners.

## $REQ_SHUTDOWN_020: Flush Buffered Logs

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must flush any buffered logs to disk before terminating.
