# Error Handling Flow

**Source:** ./README.md, ./readme/MCP_SERVER.md, ./readme/PERFORMANCE.md

Start RawProx with MCP server, test various error conditions during runtime, and shutdown gracefully.

## $REQ_ARGS_001: Help Text to STDERR

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior")

When started without arguments and without `--mcp` flag, RawProx must show help text (from HELP.md) to STDERR.

## $REQ_ARGS_006: Exit Code 1 on Help Display

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior")

When RawProx displays help text and exits, it must exit with exit code 1.

## $REQ_ARGS_007: No NDJSON on Help Exit

**Source:** ./README.md (Section: "Usage")

When RawProx exits to display help text, it must output only help text to STDERR and never output NDJSON to STDOUT.

## $REQ_ARGS_003: Invalid Port Rule Format

**Source:** ./README.md (Section: "Usage")

If arguments don't parse as valid port rules or log destinations, RawProx must show an error and exit.

## $REQ_ARGS_004: Port Rule Format Validation

**Source:** ./README.md (Section: "Command-Line Format")

If a port rule doesn't follow the format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`, RawProx must show an error and exit.

## $REQ_ARGS_005: Log Destination Format Validation

**Source:** ./README.md (Section: "Command-Line Format")

If a log destination doesn't start with `@` followed by a directory path, RawProx must show an error and exit.

## $REQ_PROXY_012: UDP Not Supported

**Source:** ./README.md (Section: "Limitations")

RawProx must not support UDP port forwarding -- only TCP connections are accepted and proxied.

## $REQ_ARGS_011: Accept MCP Flag

**Source:** ./readme/HELP.md (Section: "Arguments")

RawProx must accept the `--mcp` command-line flag to enable MCP server mode.

## $REQ_MCP_001: Start with MCP Flag

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior")

When started with `--mcp` flag, RawProx must operate as an MCP server.

## $REQ_MCP_002: Random Port Selection

**Source:** ./readme/MCP_SERVER.md (Section: "Connection")

MCP server must listen on a random available TCP port between 10000 and 65500.

## $REQ_MCP_003: Emit Start MCP Event Only With Flag

**Source:** ./readme/MCP_SERVER.md (Section: "Start-up Behavior"), ./readme/LOG_FORMAT.md (Section: "MCP Server Events")

The `start-mcp` event must be emitted to STDOUT only when the `--mcp` flag is used, including the TCP port number.

## $REQ_MCP_005: JSON-RPC Protocol

**Source:** ./readme/MCP_SERVER.md (Section: "JSON-RPC Protocol")

MCP server must accept JSON-RPC 2.0 requests over TCP/IP.

## $REQ_STARTUP_005: Port Already in Use Error

**Source:** ./README.md (Section: "Quick Start")

If a local port is already in use, RawProx must show an error indicating which port is occupied.

## $REQ_MCP_013: Add Port Rule Method

**Source:** ./readme/MCP_SERVER.md (Section: "add-port-rule")

MCP server must support `add-port-rule` method to add port forwarding rules at runtime.

## $REQ_MCP_014: Add Port Rule Parameters

**Source:** ./readme/MCP_SERVER.md (Section: "add-port-rule")

`add-port-rule` method must accept `local_port`, `target_host`, and `target_port` parameters.

## $REQ_MCP_020: Error Response

**Source:** ./readme/MCP_SERVER.md (Section: "Error Handling")

Failed requests must return JSON-RPC error response with error code and message.

## $REQ_MCP_024: Add Port Rule Port Conflict Error

**Source:** ./readme/MCP_SERVER.md (Section: "Error Handling")

When `add-port-rule` attempts to use a port that's already in use, it must return an error message indicating which port is occupied.

## $REQ_MCP_017: Shutdown Method

**Source:** ./readme/MCP_SERVER.md (Section: "shutdown")

MCP server must support `shutdown` method to gracefully shutdown RawProx.

## $REQ_MCP_018: Shutdown Behavior

**Source:** ./readme/MCP_SERVER.md (Section: "shutdown")

On shutdown command, RawProx must close all connections, stop all listeners, flush buffered logs, and terminate.

## $REQ_SHUTDOWN_002: Close All Connections

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must close all active connections.

## $REQ_SHUTDOWN_003: Stop All Listeners

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must stop all TCP listeners.

## $REQ_SHUTDOWN_004: Flush Buffered Logs

**Source:** ./README.md (Section: "Stopping")

On shutdown, RawProx must flush any buffered logs to disk before terminating.
