# MCP Server Mode (Optional)

When started with `--mcp-port PORT`, RawProx operates as an MCP (Model Context Protocol) server, allowing dynamic control over HTTP. This enables starting/stopping logging to different directories and port forwardings at runtime.

## Starting the MCP Server

Use `--mcp-port` to specify the port for MCP commands:

```bash
# Listen on specific port
rawprox.exe --mcp-port 8765 8080:example.com:80 @./logs

# Let system choose available port
rawprox.exe --mcp-port 0 8080:example.com:80 @./logs
```

RawProx will emit an NDJSON event to stdout:
```json
{"time":"2025-10-22T15:32:47.123456Z","event":"mcp-ready","endpoint":"http://localhost:8765/mcp"}
```

**With --mcp-port and port rules:**
```bash
rawprox.exe --mcp-port 8765 8080:example.com:80 @./logs
```
- Starts logging immediately
- MCP server available for dynamic control
- Can be stopped with Ctrl-C or via MCP shutdown command

**With --mcp-port but without port rules:**
```bash
rawprox.exe --mcp-port 8765
```
- Waits for MCP commands to add port rules
- No help text shown (since MCP server is running)
- Can be stopped with Ctrl-C or via MCP shutdown command

**Without --mcp-port:**
```bash
rawprox.exe 8080:example.com:80 @./logs
```
- Runs as a simple proxy without MCP server
- No MCP control available
- Can only be stopped with Ctrl-C

**Without --mcp-port and without port rules:**
```bash
rawprox.exe
```
- Displays help text to STDERR
- Exits immediately with exit code 1
- No NDJSON output to STDOUT

## MCP Protocol

RawProx implements the [Model Context Protocol](https://modelcontextprotocol.io/) over HTTP. The server accepts SSE (Server-Sent Events) for transport.

### Example Session

**Initialize connection:**

```http
POST /mcp HTTP/1.1
Host: localhost:8765
Accept: application/json, text/event-stream
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "initialize",
  "id": 1,
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "example-client",
      "version": "1.0.0"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "rawprox",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

**List available tools:**

```http
POST /mcp HTTP/1.1
Host: localhost:8765
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2,
  "params": {}
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "start-logging",
        "description": "Start logging to a destination (STDOUT or directory)",
        "inputSchema": {
          "type": "object",
          "properties": {
            "directory": {
              "type": ["string", "null"],
              "description": "Directory path, or null for STDOUT"
            },
            "filename_format": {
              "type": "string",
              "description": "Optional strftime pattern (default: rawprox_%Y-%m-%d-%H.ndjson)"
            }
          }
        }
      },
      {
        "name": "stop-logging",
        "description": "Stop logging to one or all destinations",
        "inputSchema": {
          "type": "object",
          "properties": {
            "directory": {
              "type": ["string", "null"],
              "description": "Optional: specific directory, null for STDOUT, omit to stop all"
            }
          }
        }
      },
      {
        "name": "add-port-rule",
        "description": "Add a new port forwarding rule at runtime",
        "inputSchema": {
          "type": "object",
          "required": ["local_port", "target_host", "target_port"],
          "properties": {
            "local_port": {
              "type": "integer",
              "description": "Local port to listen on"
            },
            "target_host": {
              "type": "string",
              "description": "Target hostname or IP address"
            },
            "target_port": {
              "type": "integer",
              "description": "Target port number"
            }
          }
        }
      },
      {
        "name": "remove-port-rule",
        "description": "Remove an existing port forwarding rule",
        "inputSchema": {
          "type": "object",
          "required": ["local_port"],
          "properties": {
            "local_port": {
              "type": "integer",
              "description": "Local port of the rule to remove"
            }
          }
        }
      },
      {
        "name": "shutdown",
        "description": "Gracefully shutdown the RawProx application",
        "inputSchema": {
          "type": "object",
          "properties": {}
        }
      }
    ]
  },
  "id": 2
}
```

**Call a tool:**

```http
POST /mcp HTTP/1.1
Host: localhost:8765
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 3,
  "params": {
    "name": "add-port-rule",
    "arguments": {
      "local_port": 9000,
      "target_host": "api.example.com",
      "target_port": 443
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Port rule added: 9000 -> api.example.com:443"
      }
    ]
  },
  "id": 3
}
```

**Error response:**

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Port 9000 already in use"
  },
  "id": 3
}
```

## Tool Reference

The MCP server provides the following tools. Use `tools/list` to discover them dynamically with full schemas.

### start-logging

Start logging to a destination (STDOUT or directory).

**Arguments:**
- `directory` (string|null) -- Directory path, or null for STDOUT
- `filename_format` (string, optional) -- Strftime pattern (default: `rawprox_%Y-%m-%d-%H.ndjson`)

### stop-logging

Stop logging to one or all destinations.

**Important subtlety:**
- Omit `directory` argument → stops ALL logging (all destinations)
- `"directory": null` → stops only STDOUT logging
- `"directory": "./logs"` → stops only logging to `./logs` directory

**Arguments:**
- `directory` (string|null, optional) -- Specific directory, null for STDOUT, omit to stop all

### add-port-rule

Add a new port forwarding rule at runtime.

**Arguments:**
- `local_port` (integer, required) -- Local port to listen on
- `target_host` (string, required) -- Target hostname or IP address
- `target_port` (integer, required) -- Target port number

### remove-port-rule

Remove an existing port forwarding rule.

**Arguments:**
- `local_port` (integer, required) -- Local port of the rule to remove

### shutdown

Gracefully shutdown the RawProx application. Closes all connections, stops all listeners, flushes buffered logs, and terminates.

**Arguments:** None
