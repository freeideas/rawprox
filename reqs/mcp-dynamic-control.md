# MCP Dynamic Control

**Source:** ./README.md, ./readme/HELP.md, ./readme/MCP_SERVER.md, ./readme/LOG_FORMAT.md

Start RawProx with MCP server enabled for dynamic runtime control over HTTP.

## $REQ_MCP_001: Parse Command-Line Arguments

**Source:** ./README.md (Section: "Usage")

Parse command-line arguments including port rules and `--mcp-port PORT` flag.

## $REQ_MCP_002: Enable MCP Server

**Source:** ./readme/HELP.md (Section: "Arguments"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

Accept `--mcp-port PORT` argument to enable MCP server on specified port.

## $REQ_MCP_003: System-Assigned Port

**Source:** ./readme/HELP.md (Section: "Arguments"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When `--mcp-port 0` is specified, let the system choose an available port.

## $REQ_MCP_004: Start MCP HTTP Server

**Source:** ./readme/MCP_SERVER.md (Section: "MCP Protocol")

Start HTTP server for MCP protocol implementation.

## $REQ_MCP_005: Emit MCP Ready Event

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

Emit NDJSON event with `"event":"mcp-ready"` and `endpoint` field containing the full HTTP URL when MCP server starts.

## $REQ_MCP_006: MCP Ready Event to STDOUT

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events")

Emit MCP ready event to STDOUT as NDJSON when using `--mcp-port`.

## $REQ_MCP_007: Start Without Port Rules

**Source:** ./readme/HELP.md (Section: "Examples"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When started with `--mcp-port` but no port rules, wait for MCP commands to add port rules without displaying help text or exiting.

## $REQ_MCP_008: Start with Initial Port Rules

**Source:** ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When started with `--mcp-port` and port rules, start listeners immediately and enable MCP for dynamic control.

## $REQ_MCP_009: MCP Protocol Implementation

**Source:** ./readme/MCP_SERVER.md (Section: "MCP Protocol")

Implement Model Context Protocol over HTTP with JSON-RPC 2.0.

## $REQ_MCP_010: Initialize Method

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

Accept `initialize` method with protocol version, capabilities, and client info parameters.

## $REQ_MCP_011: Initialize Response

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

Respond to `initialize` with protocol version `2024-11-05`, capabilities object with `tools`, and server info.

## $REQ_MCP_011A: SSE Transport Support

**Source:** ./readme/MCP_SERVER.md (Section: "MCP Protocol")

Accept SSE (Server-Sent Events) for transport.

## $REQ_MCP_012: Tools List Method

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

Implement `tools/list` method to return available tools with schemas.

## $REQ_MCP_013: Start Logging Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

Provide `start-logging` tool with `directory` (string or null) and optional `filename_format` parameters.

## $REQ_MCP_014: Start Logging Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

Emit NDJSON event with `"event":"start-logging"`, `directory`, and optional `filename_format` fields when logging starts.

## $REQ_MCP_015: Stop Logging Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

Provide `stop-logging` tool with optional `directory` parameter.

## $REQ_MCP_016: Stop All Logging

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When `stop-logging` is called with no `directory` argument, stop logging to all destinations.

## $REQ_MCP_017: Stop STDOUT Logging

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When `stop-logging` is called with `"directory": null`, stop only STDOUT logging.

## $REQ_MCP_018: Stop Directory Logging

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When `stop-logging` is called with a directory path, stop only logging to that specific directory.

## $REQ_MCP_019: Stop Logging Event

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

Emit NDJSON event with `"event":"stop-logging"` and `directory` field when logging stops.

## $REQ_MCP_020: Add Port Rule Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

Provide `add-port-rule` tool with `local_port`, `target_host`, and `target_port` parameters.

## $REQ_MCP_021: Runtime Port Rule Addition

**Source:** ./README.md (Section: "Key Features"), ./readme/MCP_SERVER.md (Section: "Tool Reference")

Add new port forwarding rules at runtime via MCP without restarting.

## $REQ_MCP_022: Remove Port Rule Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

Provide `remove-port-rule` tool with `local_port` parameter.

## $REQ_MCP_023: Runtime Port Rule Removal

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

Remove existing port forwarding rules at runtime via MCP.

## $REQ_MCP_024: Shutdown Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

Provide `shutdown` tool with no parameters for graceful shutdown.

## $REQ_MCP_025: Tools Call Method

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

Implement `tools/call` method to execute tools with provided arguments.

## $REQ_MCP_026: Tool Success Response

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

Return success response with `content` array containing text results when tool succeeds.

## $REQ_MCP_027: Tool Error Response

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

Return error response with error code and message when tool fails.

## $REQ_MCP_028: Accept Client Connections

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Accept incoming client connections on configured local ports.

## $REQ_MCP_029: Connect to Target Servers

**Source:** ./README.md (Section: "What It Does")

Establish TCP connections to target hosts and ports specified in port rules.

## $REQ_MCP_030: Log Connection Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Emit NDJSON events for connection open and close with ConnID, timestamp, `from` and `to` addresses.

## $REQ_MCP_031: Forward Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data between client and server bidirectionally.

## $REQ_MCP_032: Log Traffic Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON traffic events with ConnID, timestamp, `data` field, `from` and `to` addresses.

## $REQ_MCP_033: MCP Graceful Shutdown

**Source:** ./README.md (Section: "Stopping"), ./readme/MCP_SERVER.md (Section: "Tool Reference")

Close all connections, stop listeners, flush buffered logs, and terminate when shutdown tool is called.

## $REQ_MCP_034: Ctrl-C Graceful Shutdown

**Source:** ./README.md (Section: "Stopping")

Respond to Ctrl-C (SIGINT) by closing all connections, stopping listeners, flushing buffered logs, and terminating.

## $REQ_MCP_035: Create Log Directory for start-logging

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Automatically create the directory if it doesn't exist when start-logging tool is called with a directory path.
