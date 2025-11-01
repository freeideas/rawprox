# MCP Server Mode (Optional)

When started with the `--mcp` flag, RawProx operates as an MCP (Model Context Protocol) server, allowing dynamic control via JSON-RPC over TCP/IP. This enables starting/stopping logging to different directories and port forwardings at runtime.

## Start-up Behavior

**With --mcp and port rules:**
```bash
rawprox --mcp 8080:example.com:80 @./logs
```
- Starts logging immediately
- MCP server available for dynamic control
- Can be stopped with Ctrl-C or via MCP shutdown command

**With --mcp but without port rules:**
```bash
rawprox --mcp
```
- Waits for JSON-RPC commands to add port rules
- Helpful usage message printed to STDERR
- Can be stopped with Ctrl-C or via MCP shutdown command

**Without --mcp flag:**
```bash
rawprox 8080:example.com:80 @./logs
```
- Runs as a simple proxy without MCP server
- No JSON-RPC control available
- Can only be stopped with Ctrl-C

The `start-mcp` event is emitted to STDOUT (with the TCP port number) only when the `--mcp` flag is used.

## JSON-RPC Protocol

The MCP server accepts JSON-RPC 2.0 requests over TCP/IP and returns JSON-RPC 2.0 responses (success results or error objects).

**Available methods:**

### start-logging

Start logging to a destination (STDOUT or directory).

**Parameters:**
```json
{
  "directory": "./logs",           // Directory path, or null for STDOUT
  "filename_format": "rawprox_%Y-%m-%d-%H.ndjson"  // Optional, strftime pattern
}
```

**Examples:**
```json
// Start logging to STDOUT
{"jsonrpc": "2.0", "method": "start-logging", "params": {"directory": null}, "id": 1}

// Start logging to directory with hourly rotation
{"jsonrpc": "2.0", "method": "start-logging", "params": {"directory": "./logs"}, "id": 2}

// Start logging with custom rotation (daily)
{"jsonrpc": "2.0", "method": "start-logging", "params": {"directory": "./logs", "filename_format": "rawprox_%Y-%m-%d.ndjson"}, "id": 3}
```

### stop-logging

Stop logging to one or all destinations.

**Important: Argument subtlety:**
- `{}` (no arguments) → stops ALL logging (all destinations)
- `{"directory": null}` → stops only STDOUT logging
- `{"directory": "./logs"}` → stops only logging to `./logs` directory

**Parameters:**
```json
{
  "directory": "./logs"  // Optional: specific directory, null for STDOUT, omit to stop all
}
```

**Examples:**
```json
// Stop ALL logging
{"jsonrpc": "2.0", "method": "stop-logging", "params": {}, "id": 4}

// Stop only STDOUT logging
{"jsonrpc": "2.0", "method": "stop-logging", "params": {"directory": null}, "id": 5}

// Stop only logging to ./logs
{"jsonrpc": "2.0", "method": "stop-logging", "params": {"directory": "./logs"}, "id": 6}
```

This distinction allows independent management of multiple logging destinations.

### add-port-rule

Add a new port forwarding rule at runtime.

**Parameters:**
```json
{
  "local_port": 9000,
  "target_host": "api.example.com",
  "target_port": 443
}
```

**Example:**
```json
{"jsonrpc": "2.0", "method": "add-port-rule", "params": {"local_port": 9000, "target_host": "api.example.com", "target_port": 443}, "id": 7}
```

### remove-port-rule

Remove an existing port forwarding rule.

**Parameters:**
```json
{
  "local_port": 9000
}
```

**Example:**
```json
{"jsonrpc": "2.0", "method": "remove-port-rule", "params": {"local_port": 9000}, "id": 8}
```

### shutdown

Gracefully shutdown the RawProx application.

**Parameters:** None (empty object)

**Example:**
```json
{"jsonrpc": "2.0", "method": "shutdown", "params": {}, "id": 9}
```

The application will close all connections, stop all listeners, flush any buffered logs, and terminate.

## Connection

When started with `--mcp`, the MCP server listens on a random available TCP port between 10000 and 65500. The `start-mcp` event in the output stream provides the connection details:

```json
{"time":"2025-10-22T15:32:47.123456Z","event":"start-mcp","port":54321}
```

Connect to `localhost:54321` and send JSON-RPC requests.

## Error Handling

Failed requests return standard JSON-RPC error responses:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Port 8080 already in use"
  },
  "id": 1
}
```

Successful responses:

```json
{
  "jsonrpc": "2.0",
  "result": "success",
  "id": 1
}
```
