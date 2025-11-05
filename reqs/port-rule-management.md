# Port Rule Management Flow

**Source:** ./readme/MCP_SERVER.md, ./README.md

Start RawProx with MCP enabled, add and remove port forwarding rules dynamically at runtime, and shutdown.

## $REQ_PORT_001A: Enable MCP Server

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts `--mcp-port PORT` argument to enable MCP server for dynamic runtime control over HTTP.

## $REQ_PORT_001B: MCP Ready Event

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When using --mcp-port, RawProx emits an NDJSON event to stdout with time, event type "mcp-ready", and endpoint URL.

## $REQ_PORT_002: Add Port Rule at Runtime

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

RawProx adds a new port forwarding rule at runtime when add-port-rule tool is called with local_port, target_host, and target_port.

## $REQ_PORT_003: Add Port Rule Success

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

When port rule is successfully added, RawProx returns success response with text describing the added rule.

## $REQ_PORT_004: Add Port Rule Error

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

When port rule cannot be added (e.g., port already in use), RawProx returns JSON-RPC error response with code and message.

## $REQ_PORT_005: Remove Port Rule at Runtime

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

RawProx removes an existing port forwarding rule when remove-port-rule tool is called with local_port.

## $REQ_PORT_006: Dynamic Port Rule Logging

**Source:** ./README.md (Section: "Key Features")

Port rules added dynamically via MCP participate in active logging destinations.

## $REQ_PORT_008: Remove Port Rule Success

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When port rule is successfully removed, RawProx returns success response.

