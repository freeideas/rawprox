# MCP Dynamic Control Flow

**Source:** ./readme/MCP_SERVER.md, ./readme/LOG_FORMAT.md

Start RawProx with MCP server, dynamically add/remove port rules and logging destinations, then shutdown via JSON-RPC.

## $REQ_MCP_026: Start with MCP Flag

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior")

When started with `--mcp` flag, RawProx must operate as an MCP server.

## $REQ_MCP_023: MCP with Initial Port Rules

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior")

When started with `--mcp` flag AND port rules, RawProx must start logging immediately and make MCP server available for dynamic control.

## $REQ_ARGS_002: No Port Rules With MCP

**Source:** ./README.md (Section: "Usage"), ./readme/MCP_SERVER.md (Section: "Start-up Behavior")

When started with `--mcp` flag but without port rules, RawProx must NOT show usage message (since MCP server is running) and must wait for MCP commands to add port rules.

## $REQ_MCP_027: Random Port Selection

**Source:** ./readme/MCP_SERVER.md (Section: "Connection")

MCP server must listen on a random available TCP port between 10000 and 65500.

## $REQ_MCP_021: Listen on Localhost

**Source:** ./readme/MCP_SERVER.md (Section: "Connection")

MCP server must accept connections on localhost at the selected port.

## $REQ_MCP_028: Emit Start MCP Event Only With Flag

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior"), ./readme/LOG_FORMAT.md (Section: "MCP Server Events")

The `start-mcp` event must be emitted to STDOUT only when the `--mcp` flag is used, including the TCP port number.

## $REQ_MCP_004: Start MCP Event Format

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events")

The `start-mcp` event must include timestamp, event type, and port number.

## $REQ_MCP_029: JSON-RPC Protocol

**Source:** ./readme/MCP_SERVER.md (Section: "JSON-RPC Protocol")

MCP server must accept JSON-RPC 2.0 requests over TCP/IP.

## $REQ_MCP_022: TCP Transport for JSON-RPC

**Source:** ./readme/MCP_SERVER.md (Section: "Connection")

MCP server must accept JSON-RPC requests over TCP/IP connections.

## $REQ_MCP_007: Start Logging Method

**Source:** ./readme/MCP_SERVER.md (Section: "start-logging")

MCP server must support `start-logging` method to start logging to STDOUT or directory.

## $REQ_MCP_008: Start Logging Parameters

**Source:** ./readme/MCP_SERVER.md (Section: "start-logging")

`start-logging` method must accept `directory` (path or null) and optional `filename_format` parameters.

## $REQ_FILE_023: Start Logging Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging starts to a directory, emit a `start-logging` event with directory path and filename_format.

## $REQ_STDOUT_011: Start Logging Event for STDOUT

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging starts to STDOUT, emit a `start-logging` event with `directory: null` and no `filename_format` field.

## $REQ_MCP_030: Add Port Rule Method

**Source:** ./readme/MCP_SERVER.md (Section: "add-port-rule")

MCP server must support `add-port-rule` method to add port forwarding rules at runtime.

## $REQ_MCP_031: Add Port Rule Parameters

**Source:** ./readme/MCP_SERVER.md (Section: "add-port-rule")

`add-port-rule` method must accept `local_port`, `target_host`, and `target_port` parameters.

## $REQ_MCP_019: Success Response

**Source:** ./readme/MCP_SERVER.md (Section: "Error Handling")

Successful requests must return JSON-RPC response with `result: "success"`.

## $REQ_MCP_034: Error Response

**Source:** ./readme/MCP_SERVER.md (Section: "Error Handling")

Failed requests must return JSON-RPC error response with error code and message.

## $REQ_PROXY_015: Accept Connections

**Source:** ./README.md (Section: "Quick Start")

RawProx must accept TCP connections on configured local ports.

## $REQ_PROXY_020: Forward Traffic Bidirectionally

**Source:** ./README.md (Section: "What It Does")

RawProx must forward all data bidirectionally between client and target.

## $REQ_STDOUT_014: Connection Open Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

When a TCP connection opens, log an event with `event: "open"`, unique ConnID, timestamp, from address, and to address.

## $REQ_STDOUT_019: Traffic Data Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Traffic Events")

For each chunk of transmitted data, log an event with ConnID, timestamp, data (JSON-escaped), from address, and to address.

## $REQ_MCP_009: Stop Logging Method

**Source:** ./readme/MCP_SERVER.md (Section: "stop-logging")

MCP server must support `stop-logging` method to stop logging to one or all destinations.

## $REQ_MCP_010: Stop Logging All Destinations

**Source:** ./readme/MCP_SERVER.md (Section: "stop-logging")

When `stop-logging` is called with empty parameters, it must stop ALL logging to all destinations.

## $REQ_MCP_011: Stop Logging STDOUT

**Source:** ./readme/MCP_SERVER.md (Section: "stop-logging")

When `stop-logging` is called with `{"directory": null}`, it must stop only STDOUT logging.

## $REQ_MCP_012: Stop Logging Specific Directory

**Source:** ./readme/MCP_SERVER.md (Section: "stop-logging")

When `stop-logging` is called with specific directory path, it must stop only logging to that directory.

## $REQ_FILE_024: Stop Logging Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging stops to a directory, emit a `stop-logging` event with directory path.

## $REQ_STDOUT_012: Stop Logging Event for STDOUT

**Source:** ./readme/LOG_FORMAT.md (Section: "Logging Control Events")

When logging stops to STDOUT, emit a `stop-logging` event with `directory: null`.

## $REQ_MCP_015: Remove Port Rule Method

**Source:** ./readme/MCP_SERVER.md (Section: "remove-port-rule")

MCP server must support `remove-port-rule` method to remove existing port forwarding rules.

## $REQ_MCP_016: Remove Port Rule Parameters

**Source:** ./readme/MCP_SERVER.md (Section: "remove-port-rule")

`remove-port-rule` method must accept `local_port` parameter.

## $REQ_MCP_025: Remove Port Rule Stops Listener

**Source:** ./readme/MCP_SERVER.md (Section: "remove-port-rule")

When a port rule is removed, the listener on that local port must stop accepting new connections.

## $REQ_SHUTDOWN_006: MCP Shutdown Stopping Mechanism

**Source:** ./README.md (Section: "Stopping")

MCP shutdown command must be available as a stopping mechanism via JSON-RPC when using `--mcp` flag.

## $REQ_MCP_032: Shutdown Method

**Source:** ./readme/MCP_SERVER.md (Section: "shutdown")

MCP server must support `shutdown` method to gracefully shutdown RawProx.

## $REQ_MCP_033: Shutdown Behavior

**Source:** ./readme/MCP_SERVER.md (Section: "shutdown")

On shutdown command, RawProx must close all connections, stop all listeners, flush buffered logs, and terminate.

## $REQ_MCP_006: JSON-RPC Responses

**Source:** ./readme/MCP_SERVER.md (Section: "JSON-RPC Protocol")

MCP server must return JSON-RPC 2.0 responses with success results or error objects.
