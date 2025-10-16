# Lessons Learned

## Windows Network Drive Issues (2025-10-16)

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
