# Error Handling

**Source:** ./README.md, ./readme/HELP.md, ./readme/MCP_SERVER.md

Handle error conditions and edge cases appropriately with proper exit behavior and error messages.

## $REQ_ERROR_001: Parse Command-Line Arguments

**Source:** ./README.md (Section: "Usage")

Parse command-line arguments for port rules, log destinations, and options.

## $REQ_ERROR_002: Invalid Port Rule Arguments

**Source:** ./README.md (Section: "Usage")

Show error message and exit when arguments don't parse as valid port rules or log destinations.

## $REQ_ERROR_003: No Arguments Without MCP

**Source:** ./README.md (Section: "Usage"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

Display help text to STDERR and exit when started without port rules and without `--mcp-port`.

## $REQ_ERROR_004: No NDJSON on Help Exit

**Source:** ./README.md (Section: "Usage")

Output only help text to STDERR (no NDJSON to STDOUT) when exiting because there is nothing to do.

## $REQ_ERROR_005: Port Already in Use on Startup

**Source:** ./README.md (Section: "Quick Start"), ./readme/HELP.md (Section: "Quick Tips")

Show error message indicating which port is occupied when a port is already in use during startup, then exit.

## $REQ_ERROR_006: Start Valid Listeners

**Source:** ./README.md (Section: "Usage")

Bind to specified local ports and listen for incoming TCP connections for valid port rules.

## $REQ_ERROR_007: Accept Client Connections

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events")

Accept incoming client connections on configured local ports.

## $REQ_ERROR_008: Connect to Target Servers

**Source:** ./README.md (Section: "What It Does")

Establish TCP connections to target hosts and ports specified in port rules.

## $REQ_ERROR_009: TLS Pass-Through Only

**Source:** ./README.md (Section: "Limitations")

Capture encrypted bytes as-is without TLS/HTTPS decryption, logging encrypted traffic in its encrypted form.

## $REQ_ERROR_010: TCP Only Support

**Source:** ./README.md (Section: "Limitations")

Accept only TCP port forwarding rules; UDP is not supported.

## $REQ_ERROR_011: Log Connection and Traffic Events

**Source:** ./readme/LOG_FORMAT.md (Section: "Connection Events"), ./readme/LOG_FORMAT.md (Section: "Traffic Events")

Emit NDJSON events for connection open/close and traffic data.

## $REQ_ERROR_012: Forward Traffic

**Source:** ./README.md (Section: "What It Does")

Forward all data between client and server bidirectionally.

## $REQ_ERROR_013: MCP Tool Error Response

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

Return JSON-RPC error with code -32602 and descriptive message when MCP tool fails (e.g., port already in use).

## $REQ_ERROR_014: Graceful Shutdown

**Source:** ./README.md (Section: "Stopping")

Respond to Ctrl-C (SIGINT) by closing all connections, stopping all listeners, flushing buffered logs, and terminating.

## $REQ_ERROR_015: Exit Code on Help

**Source:** ./README.md (Section: "Usage")

Exit with code 1 when displaying help text due to no arguments without --mcp-port.
