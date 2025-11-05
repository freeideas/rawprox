# Command-Line Arguments Flow

**Source:** ./readme/COMMAND-LINE_USAGE.md, ./README.md

Start RawProx with command-line arguments, process arguments, execute accordingly, and exit.

## $REQ_CMD_001: Command-Line Format

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Usage")

RawProx accepts command-line format: rawprox.exe [--mcp-port PORT] [--flush-millis MS] [--filename-format FORMAT] PORT_RULE... [@LOG_DIRECTORY]

## $REQ_CMD_002: MCP Port Option

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

--mcp-port PORT enables MCP server for dynamic runtime control over HTTP, accepting a port number or 0 for system-chosen port.

## $REQ_CMD_003: Flush Millis Option

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

--flush-millis MS sets buffer flush interval in milliseconds with default of 2000. Lower values mean more frequent disk writes, higher values mean larger memory buffers.

## $REQ_CMD_004: Filename Format Option

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

--filename-format FORMAT sets log file naming pattern using strftime format with default of rawprox_%Y-%m-%d-%H.ndjson.

## $REQ_CMD_005: Port Rule Format

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

PORT_RULE format is LOCAL_PORT:TARGET_HOST:TARGET_PORT to forward connections from local port to remote host and port.

## $REQ_CMD_006: Multiple Port Rules

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

Multiple port rules can be specified to proxy several services simultaneously.

## $REQ_CMD_007: Log Directory Format

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

LOG_DIRECTORY format is @DIRECTORY to log traffic to time-rotated files in the specified directory.

## $REQ_CMD_008: Single Directory on Command Line

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

Only one directory can be specified on the command line - all port rules log to the same destination.

## $REQ_CMD_009: STDOUT Default

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

If no directory is specified, logs go to STDOUT only.

## $REQ_CMD_014: Directory Without Port Rules Shows Error

**Source:** ./README.md (Section: "Quick Start")

If a log directory is specified (`@DIRECTORY`) without any port rules, RawProx shows an error to STDERR and exits with a non-zero status. Use MCP's start-logging tool for dynamic logging control.

## $REQ_CMD_015: Help Text Destination

**Source:** ./README.md (Section: "Usage")

When displaying help text, RawProx outputs it to STDERR.

## $REQ_CMD_010: MCP Endpoint URL Output

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "MCP Introspection"), ./readme/LOG_FORMAT.md (Section: "MCP Server Events")

When using --mcp-port, the server emits the MCP endpoint URL as an NDJSON event to stdout.

## $REQ_CMD_013: Help Text Content

**Source:** ./readme/COMMAND-LINE_USAGE.md (entire document)

When displaying help text, RawProx shows usage format, argument descriptions, examples, and documentation references.

## $REQ_CMD_011: Execute Based on Arguments

**Source:** ./README.md (Section: "Usage"), ./readme/COMMAND-LINE_USAGE.md (Section: "Quick Tips")

RawProx runs if given --mcp-port or port rules (or both). It only shows help and exits when given neither.

## $REQ_CMD_012: Application Shutdown

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When RawProx is terminated (via shutdown tool or process termination), the application exits the process.
