# Multiple Log Destinations

**Source:** ./README.md, ./readme/HELP.md, ./readme/LOG_FORMAT.md, ./readme/PERFORMANCE.md

Run RawProx logging to STDOUT and multiple directories simultaneously.

## $REQ_MULTIDEST_001: Parse Port Rule Argument

**Source:** ./README.md (Section: "Usage")

Parse command-line argument in format `LOCAL_PORT:TARGET_HOST:TARGET_PORT` (e.g., `8080:example.com:80`).

## $REQ_MULTIDEST_002: Accept Multiple Log Destinations

**Source:** ./readme/HELP.md (Section: "Arguments")

Accept multiple `@DIRECTORY` arguments on the command line.

## $REQ_MULTIDEST_003: Create Log Directories

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Automatically create log directories if they don't exist for each specified destination.

## $REQ_MULTIDEST_004: Start Proxy Listener

**Source:** ./README.md (Section: "Usage")

Bind to the specified local port and listen for incoming TCP connections.

## $REQ_MULTIDEST_005: Accept Client Connection

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Accept incoming client connections on the local port.

## $REQ_MULTIDEST_006: Connect to Target Server

**Source:** ./README.md (Section: "What It Does")

Establish TCP connection to the target host and port specified in the port rule.

## $REQ_MULTIDEST_007: Log Connection Open Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Emit NDJSON event with `"event":"open"`, unique ConnID, timestamp, `from` address, and `to` address.

## $REQ_MULTIDEST_008: Log to All Destinations

**Source:** ./README.md (Section: "Key Features")

Write each log event to all specified destinations (STDOUT and/or directories) simultaneously.

## $REQ_MULTIDEST_009: Forward Client to Server Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data received from client to target server.

## $REQ_MULTIDEST_010: Log Client to Server Traffic

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic event with ConnID, timestamp, `data` field, `from` (client address), and `to` (target server address).

## $REQ_MULTIDEST_011: Forward Server to Client Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data received from target server back to client.

## $REQ_MULTIDEST_012: Log Server to Client Traffic

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic event with ConnID, timestamp, `data` field, `from` (server address), and `to` (client address).

## $REQ_MULTIDEST_013: Handle Connection Close

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When connection closes, emit NDJSON event with `"event":"close"`, ConnID, timestamp, `from` and `to` addresses.

## $REQ_MULTIDEST_014: Independent Directory Buffers

**Source:** ./readme/PERFORMANCE.md (Section: "Memory Buffering Strategy")

Maintain separate memory buffers for each log destination.

## $REQ_MULTIDEST_015: Independent Flush Intervals

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Flush each destination's buffer at the configured interval independently.

## $REQ_MULTIDEST_016: STDOUT Plus Directories

**Source:** ./README.md (Section: "Key Features"), ./readme/LOG_FORMAT.md (Section: "Output Destinations")

Support logging to STDOUT simultaneously with directory destinations.

## $REQ_MULTIDEST_017: Graceful Shutdown with Ctrl-C

**Source:** ./README.md (Section: "Stopping")

Respond to Ctrl-C (SIGINT) by closing all connections, stopping listeners, flushing buffered logs to all destinations, and terminating.
