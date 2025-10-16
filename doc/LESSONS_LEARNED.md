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

## RDP Redirected Drive Compatibility

### Problem

RDP drive redirection (Remote Desktop via `\\TSCLIENT\`) uses a special Windows driver (`rdpdr.sys`) that is incompatible with file I/O in some programming languages.

### Language Compatibility

Testing showed:
- ❌ **Java**: Confirmed incompatible (fails with "The parameter is incorrect")
- ❌ **Rust**: Evidence suggests incompatibility (similar native file I/O APIs)
- ❌ **Zig**: Evidence suggests incompatibility (similar native file I/O APIs)
- ✅ **C#**: Confirmed compatible
- ✅ Bash/shell commands and cmd.exe redirection also work

### Testing Recommendation

When testing network drive functionality, verify the drive type:
```bash
net use | grep "TSCLIENT"  # Indicates RDP redirected drive
```

True SMB/CIFS network shares work with most languages; RDP redirection specifically requires runtime-level compatibility.
