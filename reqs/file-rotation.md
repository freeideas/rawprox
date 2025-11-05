# File Rotation Flow

**Source:** ./README.md, ./readme/COMMAND-LINE_USAGE.md, ./readme/LOG_FORMAT.md, ./readme/PERFORMANCE.md

Start RawProx with file logging, write to time-rotated files with configurable naming patterns, and shutdown.

## $REQ_ROT_STARTUP_001: Single Executable

**Source:** ./README.md (Section: "Runtime Requirements")

RawProx runs as a single executable (`rawprox.exe`) without external dependencies.

## $REQ_ROT_STARTUP_002: Accept Port Rule Argument

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts port rule arguments in format `LOCAL_PORT:TARGET_HOST:TARGET_PORT`.

## $REQ_ROT_001A: Accept Log Directory Argument

**Source:** ./README.md (Section: "Quick Start"), ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts log directory argument in format `@DIRECTORY` to log to time-rotated files.

## $REQ_ROT_002: Time-Rotated Logs

**Source:** ./README.md (Section: "Key Features")

RawProx supports automatic file rotation (hourly, daily, per-minute, etc.).

## $REQ_ROT_003: Filename Format Argument

**Source:** ./readme/COMMAND-LINE_USAGE.md (Section: "Arguments")

RawProx accepts --filename-format argument to set log file naming pattern using strftime format (default: rawprox_%Y-%m-%d-%H.ndjson).

## $REQ_ROT_004: Hourly Rotation Default

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Default filename format provides hourly rotation: rawprox_%Y-%m-%d-%H.ndjson produces files like rawprox_2025-10-22-15.ndjson.

## $REQ_ROT_005: Daily Rotation

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Format rawprox_%Y-%m-%d.ndjson produces daily rotation files like rawprox_2025-10-22.ndjson.

## $REQ_ROT_006: Per-Minute Rotation

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Format rawprox_%Y-%m-%d-%H-%M.ndjson produces per-minute rotation files like rawprox_2025-10-22-15-32.ndjson.

## $REQ_ROT_007: Per-Second Rotation

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Format rawprox_%Y-%m-%d-%H-%M-%S.ndjson produces per-second rotation files like rawprox_2025-10-22-15-32-47.ndjson.

## $REQ_ROT_008: No Rotation Single File

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Format rawprox.ndjson produces a single file without rotation.

## $REQ_ROT_009: Append Mode

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Files are opened in append mode so restarts continue writing to the same file.

## $REQ_ROT_010: Never Overwrite

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

RawProx never overwrites existing files.

## $REQ_ROT_011: Create Files Automatically

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Files are created automatically if they don't exist.

## $REQ_ROT_012: Create Directory Automatically

**Source:** ./readme/LOG_FORMAT.md (Section: "File Rotation")

Directory is created automatically if it doesn't exist.

## $REQ_ROT_013: Multiple Active Buffers

**Source:** ./readme/PERFORMANCE.md (Section: "Batched File I/O")

When using time-rotated filenames, there may be multiple buffers active simultaneously - one for each time period. Each buffer is flushed to its corresponding file with a single write operation.

## $REQ_ROT_014: Fast Rotation Testing

**Source:** ./readme/PERFORMANCE.md (Section: "STDOUT Mode")

For testing with fast rotation, use small --flush-millis (e.g., 100) with per-second rotation format.

## $REQ_ROT_SHUTDOWN_001: Application Shutdown

**Source:** ./readme/MCP_SERVER.md (Section: "Tool Reference")

When RawProx is terminated (via shutdown tool or process termination), the application exits the process.
