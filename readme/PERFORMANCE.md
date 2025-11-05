# Performance Model

RawProx is designed to capture network traffic at full speed without blocking or slowing down proxied connections.

## Core Principle: Never Block Network I/O

**Network communication is king:**
- Proxied connections maintain full throughput regardless of logging activity
- Network data forwarding is never slowed down by file write operations
- If logging can't keep up → buffer in memory
- If buffer fills → crash with OOM (intentional)

**This means:**
- ✅ No backpressure on proxied connections
- ✅ Captures traffic at line rate
- ✅ Predictable failure mode (OOM crash, not slowdown)
- ❌ Data loss on OOM crash (last unflushed buffer)

## Memory Buffering Strategy

**Log events appear in files only after flush intervals, not immediately:**

1. Network events arrive (connection open/close, data transfer)
2. Events serialized to JSON and appended to memory buffer
3. Buffer flushes to disk at intervals (configurable via --flush-millis)
4. If buffer grows faster than flush rate → OOM

**Buffer grows when:**
- Network traffic rate exceeds disk write rate
- Disk I/O is slow (network filesystem, slow disk)
- Flush interval is too long

## Batched File I/O

**Files are written in batches, not per-event:**

**Write cycle:**
1. Accumulate events in memory buffer
2. Wait for flush interval (default: 2000ms)
3. Open file → write entire buffer → close file
4. Clear buffer, repeat

**Why open-write-close each flush?**
- Minimizes system calls to approximately one write per interval
- Keeps files closed and unlocked most of the time
- Allows other processes to read/move/analyze log files while proxy runs

**Configurable parameters:**
- `--flush-millis MILLISECONDS` -- Time between disk writes (default: 2000)

**Minimum flush interval:**
Files are never opened/written/closed more frequently than the flush interval. This:
- Reduces disk I/O operations
- Improves performance on slow disks
- Trades memory usage for I/O efficiency

**Example:**
```bash
# Flush every 5 seconds (lower memory usage, more I/O)
rawprox.exe 8080:example.com:80 @./logs --flush-millis 5000

# Flush every 500ms (higher memory usage, less I/O)
rawprox.exe 8080:example.com:80 @./logs --flush-millis 500

# Flush every 100ms (for testing with 1-second rotation)
rawprox.exe 8080:example.com:80 @./logs --filename-format "rawprox_%Y-%m-%d-%H-%M-%S.ndjson" --flush-millis 100
```

## STDOUT Mode

When logging to STDOUT (no `@DIRECTORY`), events are still buffered and flushed at intervals. This prevents excessive syscalls when piping to other processes:

```bash
# Events buffered and flushed every 2000ms
rawprox.exe 8080:example.com:80 | jq .
```

**Testing with fast rotation:**
- Use small `--flush-millis` (e.g., 100) with per-second rotation
- Example: `--filename-format "rawprox_%Y-%m-%d-%H-%M-%S.ndjson" --flush-millis 100`
