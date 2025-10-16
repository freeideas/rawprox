# Lessons Learned

## Windows Network Drive Issues

### Problems Encountered

- **BufWriter + append mode on Windows network drives causes silent data loss**
  - Large buffers (128KB) never fill with small data amounts (~200 bytes/connection)
  - Flush operations fail silently on network drives (SMB/CIFS)
  - File remains at 0 bytes despite successful traffic passing through proxy

- **Frequent flush operations on Windows network drives cause Error 87**
  - "The parameter is incorrect" when flushing after every write
  - Windows network redirector (SMB/CIFS) becomes unstable with frequent flushes
  - Happens with append mode + high flush frequency (multiple times per second)

### Testing Notes

- **Always test on network drives explicitly** - local drive tests don't reveal these issues
- Test showed 0 bytes on network drive (G:\) vs. 380 bytes on local drive (C:\) with identical code

## RDP Redirected Drive Incompatibility with Java

### Problem

**Java file I/O is fundamentally incompatible with RDP redirected drives** (Remote Desktop drive redirection via `\\TSCLIENT\`).

### Symptoms

- All Java file write operations fail with "The parameter is incorrect" error
- Files are created but remain at 0 bytes
- Affects both `FileOutputStream` and NIO `Files.write()`
- Affects all path formats: `h:/path`, `h:\path`, `\\tsclient\c\path`, `//tsclient/c/path`
- Works perfectly on local drives (C:) and real SMB network shares

### Root Cause

RDP drive redirection uses a special Windows driver (`rdpdr.sys` - Terminal Services driver) that Java's native file I/O APIs don't support. The Windows API calls that Java uses are not compatible with this driver.

### Verification

Testing showed:
- ❌ Java `FileOutputStream`: Fails with "The parameter is incorrect"
- ❌ Java NIO `Files.write()`: Fails with "The parameter is incorrect"
- ✅ Bash/shell commands: Work fine
- ✅ C# `File.AppendAllText()`: Works fine
- ✅ cmd.exe redirection: Works fine

### Likely Affected Languages

Based on the nature of this incompatibility (low-level Windows API interaction with RDP driver):
- **Java**: Confirmed affected
- **Rust**: Likely affected (uses similar native file I/O APIs)
- **Zig**: Likely affected (uses similar native file I/O APIs)
- **C#**: Confirmed working (uses different Windows API layer)

### Workaround Options

1. **Document limitation**: RDP redirected drives not supported
2. **Use actual network shares**: Map drives to real SMB shares instead of RDP redirection
3. **Use local drives**: Write to C: instead of RDP-redirected drives
4. **Shell out** (ugly): Use `ProcessBuilder` to call `cmd.exe` for file writes
5. **Rewrite in C#**: C# file I/O works with RDP drives

### Testing Recommendation

When testing network drive functionality, verify the drive type:
```bash
net use | grep "TSCLIENT"  # Indicates RDP redirected drive
```

True SMB/CIFS network shares should work; only RDP redirection is problematic.
