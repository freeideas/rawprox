# Lessons Learned: Windows Network Drive Challenges

## Date: 2025-10-16

This document captures critical lessons learned while implementing file output for RawProx on Windows network drives.

---

## Lesson 1: BufWriter + Append Mode + Network Drives = Silent Data Loss

### The Problem

Using `BufWriter` with a large buffer (128KB) in append mode on Windows network drives causes **complete data loss**:

```rust
// ❌ BROKEN: Data never written to network drives
let mut buffered_writer = BufWriter::with_capacity(128 * 1024, writer);
buffered_writer.write_all(data)?;
// ... data sits in buffer forever
```

### What We Observed

**Test Setup:**
- Local drive (C:\): ✅ Works perfectly, 4 NDJSON entries written
- Network drive (G:\My Drive\tmp): ❌ 0 bytes, complete data loss

**Root Cause:**
1. Small data amounts (~100-200 bytes per connection) never fill the 128KB buffer
2. Periodic `flush()` calls fail silently on network drives (errors ignored to prevent Error 87)
3. Data remains in buffer indefinitely
4. File remains at 0 bytes despite successful network traffic passing through proxy

### The Lesson

**BufWriter is incompatible with network drives in append mode when:**
- Buffer is large (relative to data volume)
- Flush errors must be tolerated
- Data loss is unacceptable

---

## Lesson 2: Frequent Flushes on Network Drives Cause Error 87

### The Problem

Flushing after every write on Windows network drives causes **"Error 87: The parameter is incorrect"**:

```rust
// ❌ FAILS on network drives with Error 87
writer.write_all(data)?;
writer.flush()?;  // Error 87 on network drives if done frequently
```

### What Causes Error 87

Windows network redirector (SMB/CIFS) becomes unstable when:
- File opened in append mode
- Flush operations occur very frequently (multiple times per second)
- Network latency + file locking + cache synchronization timing issues

### The Original "Solution" (That Failed)

Attempted fix was to:
1. Use 128KB BufWriter to reduce flush frequency
2. Flush every 2 seconds instead of every write
3. Silently ignore flush errors

**Result:** Prevented Error 87, but caused worse problem (total data loss per Lesson 1)

---

## The Fundamental Tradeoff

When writing to Windows network drives, we face contradictory requirements:

| Approach | Network Drive Behavior | Risk |
|----------|------------------------|------|
| **Flush after every write** | Error 87 crashes | Program fails with error |
| **Large buffer + delayed flush** | Flush fails silently, data lost | Silent data loss (worse!) |
| **No buffering + immediate flush** | Error 87 likely | Program fails with error |

### Key Insight

**Silent data loss is worse than a visible error.**

A program that crashes with Error 87 tells you something is wrong.
A program that runs "successfully" but silently loses all your data is catastrophic.

---

## Proposed Solutions (For Future Consideration)

### Option 1: Detect Network Drives and Warn User

```rust
if is_network_drive(&filepath) {
    eprintln!("Warning: Network drive detected. Output may be unreliable.");
    eprintln!("Recommend using shell redirection instead: rawprox ... > file.ndjson");
}
```

### Option 2: Use Different Strategy for Network Drives

- Local drives: Direct writes with immediate flush
- Network drives: Batch writes with 2-second flush, but **report flush errors** instead of ignoring

### Option 3: Don't Use Append Mode

Instead of `.append(true)`, use `.create(true).write(true)` and seek to end:
```rust
let mut file = OpenOptions::new().create(true).write(true).open(filepath)?;
file.seek(SeekFrom::End(0))?;
// Write without append mode flag
```

This *might* avoid some network drive issues (untested).

### Option 4: Document the Limitation

Be transparent in documentation:
```markdown
**Windows Network Drives:** The @file feature may not work reliably on
network drives due to Windows file system limitations. Use shell
redirection instead:

    rawprox 8080:example.com:80 > \\server\share\logs\traffic.ndjson
```

---

## Current Status

**Reverted to simple approach:**
- Removed BufWriter
- Write + flush after every line
- Report flush errors (don't ignore)

**Trade-off made:**
- May see Error 87 on network drives
- But will NOT lose data silently
- User gets clear error message instead of false success

**Workaround available:**
- Use shell redirection instead of @file argument
- Shell handles buffering/network writes differently

---

## Testing Evidence

### Reproduction Steps

1. Start echo server: `uv run --script tmp/echo_server.py`
2. Start rawprox with network drive: `rawprox 32198:127.0.0.1:32199 "@/g/My Drive/tmp/test.ndjson"`
3. Send test data: `uv run --script tmp/send_test.py`
4. Check file: `ls -lh "/g/My Drive/tmp/test.ndjson"`

**Result with BufWriter (broken):**
```
-rw-r--r-- 0 bytes  # File exists but empty!
```

**Result on local drive (works):**
```
-rw-r--r-- 380 bytes  # Contains 4 NDJSON entries
```

### Files Referenced

- Bug report: `tmp/bug-report.md`
- Test scripts: `tmp/echo_server.py`, `tmp/send_test.py`
- Source code: `src/main.rs` (log_writer_blocking function)

---

## Key Takeaways

1. **Windows network drives are fundamentally incompatible with append mode + buffering**
2. **Silent failures are worse than loud failures** - always prefer error messages over data loss
3. **Test on network drives explicitly** - local drive tests don't reveal these issues
4. **Document limitations honestly** - users need to know about network drive issues
5. **Provide workarounds** - shell redirection works when @file doesn't

---

## Related Documentation

- [SPECIFICATION.md](../SPECIFICATION.md) - §3.2.2 Output File Specifier, §9 Error Handling
- [FOUNDATION.md](../FOUNDATION.md) - Design philosophy (transparency, fail-fast)
- [Bug Report](../tmp/bug-report.md) - Original issue investigation
