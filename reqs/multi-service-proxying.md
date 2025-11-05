# Multi-Service Proxying

**Source:** ./README.md, ./readme/HELP.md, ./readme/LOG_FORMAT.md

Run RawProx with multiple port rules to proxy several services simultaneously.

## $REQ_MULTI_001: Parse Command-Line Arguments

**Source:** ./README.md (Section: "Usage")

Parse command-line arguments for multiple port rules and optional log destinations.

## $REQ_MULTI_002: Accept Multiple Port Rules

**Source:** ./README.md (Section: "Multiple Services"), ./readme/HELP.md (Section: "Arguments")

Accept multiple `LOCAL_PORT:TARGET_HOST:TARGET_PORT` arguments on the command line.

## $REQ_MULTI_003: Create Independent Listeners

**Source:** ./README.md (Section: "Multiple Services")

Create a separate TCP listener for each port rule provided.

## $REQ_MULTI_004: Accept Client Connections

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Accept incoming client connections on each configured local port.

## $REQ_MULTI_005: Connect to Target Servers

**Source:** ./README.md (Section: "What It Does")

Establish TCP connections to the respective target hosts and ports specified in each port rule.

## $REQ_MULTI_006: Log Connection Open Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Emit NDJSON event with `"event":"open"`, unique ConnID, timestamp, `from` address, and `to` address for each connection.

## $REQ_MULTI_007: Forward Connections Independently

**Source:** ./README.md (Section: "Multiple Services")

Forward connections for each port rule independently of other port rules.

## $REQ_MULTI_008: Log Traffic for All Services

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic events with ConnID, timestamp, `data` field, `from` and `to` addresses for traffic on all services.

## $REQ_MULTI_009: Unique Connection IDs Across Services

**Source:** ./README.md (Section: "Multiple Services")

Assign unique connection IDs across all services to distinguish traffic from different connections.

## $REQ_MULTI_010: Log All Services to Same Destination

**Source:** ./README.md (Section: "Multiple Services")

Write log events from all port rules to the same output destination(s).

## $REQ_MULTI_011: Handle Connection Closes

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When connections close, emit NDJSON event with `"event":"close"`, ConnID, timestamp, `from` and `to` addresses.

## $REQ_MULTI_012: Graceful Shutdown with Ctrl-C

**Source:** ./README.md (Section: "Stopping")

Respond to Ctrl-C (SIGINT) by closing all connections on all services, stopping all listeners, flushing buffered logs, and terminating.
