# MCP Server Session Flow

**Source:** ./README.md, ./readme/COMMAND-LINE_USAGE.md, ./readme/MCP_SERVER.md, ./readme/LOG_FORMAT.md

Start RawProx with MCP server enabled, use dynamic control via HTTP, and shutdown.

## $REQ_MCP_001: Accept MCP Port Argument

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts `--mcp-port PORT` argument to enable MCP server for dynamic runtime control over HTTP.

## $REQ_MCP_002: System-Chosen Port

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When --mcp-port is 0, the system chooses an available port.

## $REQ_MCP_003: MCP Ready Event

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When using --mcp-port, RawProx emits an NDJSON event to stdout with time, event type "mcp-ready", and endpoint URL.

## $REQ_MCP_004: MCP Event to STDOUT

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events")

The mcp-ready event is emitted to stdout as NDJSON, maintaining compatibility with stdout logging.

## $REQ_MCP_005: Run with MCP Only

**Source:** ./README.md (Section: "Usage"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

RawProx runs and waits for MCP commands when started with --mcp-port but without port rules.

## $REQ_MCP_006: No Help Text with MCP

**Source:** ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When --mcp-port is specified, RawProx does not show help text even without port rules (MCP server gives it something to do).

## $REQ_MCP_007: MCP Protocol Over HTTP

**Source:** ./readme/MCP_SERVER.md (Section: "MCP Protocol")

RawProx implements the Model Context Protocol over HTTP with SSE (Server-Sent Events) for transport.

## $REQ_MCP_021: MCP Endpoint Path

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events"), ./readme/MCP_SERVER.md (Section: "Example Session")

The MCP server accepts requests at the `/mcp` path via HTTP POST.

## $REQ_MCP_022: MCP Protocol Version

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

RawProx supports MCP protocol version "2024-11-05".

## $REQ_MCP_008: Initialize Method

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

RawProx responds to the "initialize" JSON-RPC method with protocol version, capabilities, and server info.

## $REQ_MCP_009: Tools List Method

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

RawProx responds to the "tools/list" JSON-RPC method with available tools and their input schemas.

## $REQ_MCP_039: Available Tools List

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The tools/list response includes five tools: start-logging, stop-logging, add-port-rule, remove-port-rule, and shutdown.

## $REQ_MCP_010: Tools Call Method

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

RawProx responds to the "tools/call" JSON-RPC method by executing the specified tool with provided arguments.

## $REQ_MCP_011: JSON-RPC Error Response

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

RawProx returns JSON-RPC error response with code and message when tool execution fails.

## $REQ_MCP_012: Start Logging Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

RawProx provides "start-logging" tool to start logging to a destination (STDOUT or directory) with directory argument (string or null) and optional filename_format argument.

## $REQ_MCP_013: Stop Logging Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

RawProx provides "stop-logging" tool to stop logging to one or all destinations.

## $REQ_MCP_014: Add Port Rule Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

RawProx provides "add-port-rule" tool to add a new port forwarding rule at runtime with local_port, target_host, and target_port arguments.

## $REQ_MCP_015: Remove Port Rule Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

RawProx provides "remove-port-rule" tool to remove an existing port forwarding rule by local_port.

## $REQ_MCP_016: Shutdown Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

RawProx provides "shutdown" tool to shutdown the RawProx application.

## $REQ_MCP_017: Tool Success Response

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

RawProx returns JSON-RPC success response with content containing text describing the result.

## $REQ_MCP_018: MCP with Port Rules

**Source:** ./README.md (Section: "Usage"), ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When started with both --mcp-port and port rules, RawProx runs, forwards traffic, and accepts MCP commands for dynamic control.

## $REQ_MCP_023: Immediate Logging Start with Command-Line Directory

**Source:** ./readme/MCP_SERVER.md (Section: "Starting the MCP Server")

When started with both --mcp-port and @directory argument, RawProx starts logging immediately to the specified directory.

## $REQ_MCP_019: MCP Server Info

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

RawProx responds to initialize with server name and version.

## $REQ_MCP_020: Shutdown via MCP Tool

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When the shutdown tool is called, RawProx terminates the application and exits the process.

## $REQ_MCP_024: MCP Endpoint URL Format

**Source:** ./readme/LOG_FORMAT.md (Section: "MCP Server Events")

The mcp-ready event endpoint field contains the full HTTP URL where MCP server is listening (format: http://localhost:PORT/mcp).

## $REQ_MCP_025: HTTP POST for MCP Requests

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The MCP server accepts HTTP POST requests to the /mcp endpoint with Content-Type application/json.

## $REQ_MCP_026: SSE Accept Header

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

MCP requests include Accept header with application/json and text/event-stream for SSE transport.

## $REQ_MCP_027: Initialize Request Parameters

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The initialize method accepts params with protocolVersion, capabilities, and clientInfo fields.

## $REQ_MCP_028: Initialize Response Content

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The initialize response returns protocolVersion, capabilities with tools object, and serverInfo with name and version.

## $REQ_MCP_029: Tools List Response Structure

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The tools/list response returns tools array with each tool containing name, description, and inputSchema fields.

## $REQ_MCP_034: Start Logging Tool Schema

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The start-logging tool inputSchema includes directory property (type string or null) and filename_format property (type string).

## $REQ_MCP_035: Stop Logging Tool Schema

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The stop-logging tool inputSchema includes optional directory property (type string or null).

## $REQ_MCP_036: Add Port Rule Tool Schema

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The add-port-rule tool inputSchema requires local_port (integer), target_host (string), and target_port (integer) properties.

## $REQ_MCP_037: Remove Port Rule Tool Schema

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The remove-port-rule tool inputSchema requires local_port (integer) property.

## $REQ_MCP_038: Shutdown Tool Schema

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The shutdown tool inputSchema has empty properties object.

## $REQ_MCP_030: Tool Call Parameters

**Source:** ./readme/MCP_SERVER.md (Section: "Example Session")

The tools/call method accepts params with name field (tool name) and arguments field (tool-specific arguments).

## $REQ_MCP_031: Add Port Rule Required Arguments

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

The add-port-rule tool requires local_port (integer), target_host (string), and target_port (integer) arguments.

## $REQ_MCP_032: Remove Port Rule Required Argument

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

The remove-port-rule tool requires local_port (integer) argument.

## $REQ_MCP_033: Shutdown Tool No Arguments

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

The shutdown tool accepts no arguments (empty properties object).
