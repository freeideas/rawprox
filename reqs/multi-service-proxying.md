# Multi-Service Proxying Flow

**Source:** ./README.md, ./readme/LOG_FORMAT.md

Verify build artifacts, start RawProx with multiple port rules, proxy multiple services simultaneously, and stop cleanly.

## $REQ_RUNTIME_005: Release Directory Contents

**Source:** ./README.md (Section: "Build Artifacts")

The `./release/` directory must contain only `rawprox.exe` with no other files (no .pdb, no .dll, no config files).

## $REQ_STARTUP_002: Start with Multiple Port Rules

**Source:** ./README.md (Section: "Multiple Services")

Start RawProx with multiple port rules provided as separate arguments.

## $REQ_ARGS_014: Flexible Argument Order

**Source:** ./readme/HELP.md (Section: "Usage")

Command-line arguments (flags, port rules, log destinations) must be accepted in any order.

## $REQ_STARTUP_003: Create Independent Listeners

**Source:** ./README.md (Section: "Multiple Services")

Each port rule must create an independent TCP listener on the specified local port.

## $REQ_FILE_015: Multiple Destinations

**Source:** ./README.md (Section: "Key Features")

RawProx must support logging to STDOUT and multiple directories simultaneously.

## $REQ_PROXY_016: Accept Connections

**Source:** ./README.md (Section: "Quick Start")

RawProx must accept TCP connections on configured local ports.

## $REQ_PROXY_010: Independent Connections

**Source:** ./README.md (Section: "Multiple Services")

Connections must be forwarded independently with unique connection IDs.

## $REQ_STDOUT_008: Unique Connection IDs

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Each connection opened must receive a different ConnID to distinguish traffic from different connections.

## $REQ_PROXY_021: Forward Traffic Bidirectionally

**Source:** ./README.md (Section: "What It Does")

RawProx must forward all data bidirectionally between client and target.

## $REQ_SHUTDOWN_007: Ctrl-C Graceful Shutdown

**Source:** ./README.md (Section: "Stopping")

RawProx must shut down gracefully when receiving Ctrl-C signal.

## $REQ_SHUTDOWN_011: Close All Connections

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must close all active connections.

## $REQ_SHUTDOWN_015: Stop All Listeners

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must stop all TCP listeners.

## $REQ_SHUTDOWN_019: Flush Buffered Logs

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must flush any buffered logs to disk before terminating.
