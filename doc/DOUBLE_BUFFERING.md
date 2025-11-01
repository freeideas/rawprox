# Double Buffering Strategy for Append-Only File Writes

## Problem Statement

Applications that generate high-frequency data and need to write it to files face contradictory requirements:

1. **Frequent writes/flushes → Poor performance** (especially on network drives, may cause OS errors)
2. **Large buffer with delayed flush → Data loss risk** (buffer never fills, or flush errors ignored)
3. **Direct writes from data-generating threads → Thread blocking** (threads wait on I/O)

This pattern solves the problem by decoupling data generation from data persistence.

---

## Solution: Double Buffering with Periodic Swap

Use two in-memory buffers that swap roles on a fixed schedule:

- **Input Buffer:** Where data-generating threads append fully-formatted data
- **Output Buffer:** What the writer thread writes to disk

### Key Insights

1. **Separate concerns:** Data collection (fast, in-memory) from data persistence (slow, I/O-bound) with minimal synchronization
2. **Pre-formatted data:** Threads format data completely before adding to buffer - as if writing directly to disk
3. **Format-agnostic:** Works with any data format (text, binary, JSON, CSV, protocol buffers, etc.)
4. **Drop-in abstraction:** Can be implemented as an independent component that replaces direct file writes

### Timing Rules

**CRITICAL:** Swap interval N is a **MINIMUM**, not a target. Swaps happen at least N seconds apart (measured swap-to-swap), never early. If a write takes 5s with N=2s, next swap is at t=7s (5s write + 2s rest). This guarantees maximum I/O frequency, preventing filesystem issues.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Data-Generating Threads                    │
│         (format data, then append to buffer)            │
└────────────┬────────────────────────────────────────────┘
             │ Fully-formatted data (ready to write)
             ▼
    ┌────────────────────┐
    │   Input Buffer     │◄─── Threads append here
    │   (Growing)        │     (Brief lock, microseconds)
    └──────────┬─────────┘
               │
               │ Every N seconds (fixed schedule, MINIMUM interval)
               │
        ┌──────▼────────┐
        │  BUFFER SWAP  │◄─── Very brief lock
        └──────┬────────┘
               │
    ┌──────────▼─────────┐
    │   Output Buffer    │
    │   (Full)           │
    └──────────┬─────────┘
               │ Single write() call
               ▼
    ┌──────────────────────┐
    │   Writer Thread      │
    │  Open, write, close  │
    │  entire buffer       │
    └──────────┬───────────┘
               │
               ▼
            File
```

---

## Buffer Lifecycle

**Phase 1 - Collection (0 to N seconds):** Threads append formatted data to input buffer while output buffer is empty. Writer waits for timer.

**Phase 2 - Swap (~microseconds):** Lock both buffers, swap contents (pointer swap), release locks. Input now empty, output now full.

**Phase 3 - Write (no locks held):** Open file in append mode, write entire output buffer, flush, close file, clear buffer, repeat. Closing between writes allows OS cleanup, metadata updates, and full commit (critical for network drives).

---

## Threading Model

### Data-Generating Threads (Many)

For each piece of data to persist:
1. Format data completely (as if writing directly to disk)
2. Acquire lock on input buffer
3. Append formatted data to input buffer
4. Release lock immediately
5. Continue working (never blocked on I/O)

**Key:** Threads only block on memory lock (nanoseconds), never on disk I/O. All formatting happens before lock acquisition.

### Writer Thread (One)

Loop:
1. Wait until at least N seconds since last swap
2. Lock both buffers, swap contents, unlock (microseconds)
3. Write entire output buffer to file (no locks held)
4. Clear output buffer
5. Repeat
(obviously this can be skipped when the input buffer is empty)

**Key:** Writer does I/O with no locks held - data threads never wait for disk.

---

## Edge Cases

**Slow writes:** If write takes longer than N, input buffer accumulates more data. No data loss, but next swap delayed (e.g., 5s write + 2s interval = 7s between swaps).

**Blocked I/O:** If filesystem unavailable (network down, disk failure), input buffer grows unbounded until OOM crash. **This is intentional** - fail loudly (visible error) rather than silently (data loss).

**High data rate:** If generation rate exceeds write throughput, buffer grows until OOM. Correct behavior: fail visibly rather than drop data.

**Graceful shutdown:** Stop new data, finish in-flight ops, final swap, write remaining data, exit. No data loss on clean shutdown.

---

## Why This Pattern Works

Alternative approaches fail: per-item writes cause excessive I/O and filesystem errors; automatic buffering silently loses data on flush errors; large buffers never fill or fail to flush.

Double buffering solves this: one batched write every N seconds (vs. thousands), no ignored errors (visible failures only), bounded N-2N second latency, and filesystems (especially network drives) handle infrequent large writes far better than frequent small ones.

---

## Performance Characteristics

**Memory:** Normal: ~N seconds of data (tens-hundreds of KB), peak 2× during swap. Under backpressure: unbounded growth to MB/GB until OOM (intentional).

**Latency:** Write latency 0-N seconds (avg N/2), lock contention microseconds, zero I/O blocking for data threads.

**CPU:** Data formatting unchanged from direct writes (done before lock), buffer ops in microseconds, one pointer swap every N seconds (negligible), one I/O op every N seconds (vs. thousands).


---

## As an Independent Component

Can be implemented as a reusable `BufferedWriter` with `append(data)` (thread-safe, non-blocking) and `close()` (final write) methods.

**Configuration:**
- Swap interval (minimum time between writes)
- Output callback/method provided by the user

**Output Flexibility:**
The component accepts a user-provided output method/callback that receives the full buffer contents. This allows the same component to support multiple output targets:
- **File writes:** Open in append mode, write buffer, close file
- **Stdout:** Write buffer to stdout (no open/close needed)
- **Network socket:** Send buffer over TCP/UDP connection
- **Custom handlers:** Compression, encryption, remote logging services, etc.

**Usage:**
Replace direct writes (`file.write(data)`, `stdout.write(data)`, etc.) with `buffered_writer.append(data)` - component handles all buffering, swapping, and I/O via the user-provided output method.

**Benefits:**
Plug-and-play, format-agnostic (treats data as opaque bytes), output-target-agnostic (works with files, stdout, sockets, etc.), thread-safe, testable (mockable output method), reusable across logging, metrics, events, telemetry, etc.

---

## Summary

Solves the tension between high-frequency data generation, efficient filesystem I/O (prefers batched writes), and non-blocking operation (threads never wait on I/O).

**Principles:** Pre-formatted data, format-agnostic, separate concerns (memory vs. disk), fixed minimum time interval (not size-based), fail loudly (OOM) not silently, open/close per write (enables OS cleanup, critical for network drives).

**Use cases:** Logging, telemetry, event streaming, audit trails, transaction logs, data pipelines - any multi-threaded scenario needing persistent data without blocking.

**Languages:** Any language with threading and file I/O (C, C++, Java, Python, Go, Rust, JS, C#, etc.)
