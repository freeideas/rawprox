# RawProx - Foundation

## Purpose

Network traffic is often opaque. When debugging protocols, reverse-engineering APIs, or analyzing client-server communications, developers need complete visibility into what's actually being transmitted. RawProx exists to make network traffic completely transparent.

## Core Problem

Existing network debugging tools either:
- Modify traffic (defeating their purpose for some use cases)
- Provide incomplete logs (missing timing, connection lifecycle, or binary data)
- Use complex formats requiring specialized viewers
- Cannot handle multiple concurrent connections clearly

## Solution Concept

A TCP proxy that acts as a perfect middleman: it sits between a client and server, forwards every byte unchanged, and logs all data that passes through as it's transmitted in real-time.

## Key Principles

1. **Complete Transparency**: Every byte is forwarded unchanged. The proxy is invisible to both client and server.

2. **Complete Lifecycle Tracking**: Connection open and close events logged with `from`/`to` addresses, showing exactly who initiated connections and who closed them.

3. **Streaming Capture**: Data logged as transmitted, not buffered into complete messages. Real-time visibility with minimal memory overhead.

4. **Structured Output**: NDJSON (Newline-Delimited JSON) format - one object per line for both human readability and programmatic analysis. Output can be written to stdout or directly to a file (UTF-8) to avoid platform character encoding issues.

5. **Connection Tracking**: Multiple simultaneous connections distinguished by base62-encoded connection IDs.

6. **Directional Clarity**: Each log entry includes `from` and `to` addresses, making traffic direction immediately clear without symbols.

7. **Binary-Safe Logging**: Text remains readable while binary data is URL-encoded (percent-encoded), preserving both usability and completeness.

8. **Non-Blocking I/O**: Output uses double-buffered writes with periodic flushing (minimum 2 seconds between writes), ensuring network forwarding never blocks on I/O operations whether writing to stdout or files. See [doc/DOUBLE_BUFFERING.md](doc/DOUBLE_BUFFERING.md) for the buffering architecture.

9. **Simplicity**: One tool, one purpose. No configuration files, no complex setup, no unnecessary features.

## Use Cases

- **Protocol Debugging**: See exactly what bytes your client sends/receives when communicating with servers
- **API Reverse Engineering**: Understand undocumented protocols by observing actual traffic patterns
- **Integration Testing**: Verify your application sends correct protocol messages in the right sequence
- **Performance Analysis**: Identify chatty protocols or inefficient message patterns causing slowdowns
- **Security Analysis**: Detect credential leakage, unencrypted passwords, or protocol vulnerabilities
- **Learning Protocols**: Study how real protocols work by watching live traffic (HTTP, Redis, MySQL, PostgreSQL, SMTP, etc.)

## Design Philosophy

The tool should be:
- **Minimal**: Do one thing perfectly rather than many things adequately
- **Fast**: Handle high-throughput connections without becoming a bottleneck
- **Reliable**: Never crash, never modify traffic, works on network drives and local filesystems. See [doc/LESSONS_LEARNED.md](doc/LESSONS_LEARNED.md) for Windows network drive considerations.
- **Parseable**: Output should be both human-readable and machine-processable
- **Self-Contained**: Single executable, no dependencies, no installation
- **Clear Error Messages**: When things go wrong (e.g., port already in use), provide actionable error messages

## Success Criteria

The tool succeeds when a developer can:
1. Insert it between any TCP client and server with a single command
2. Monitor multiple ports simultaneously from one proxy instance
3. See all traffic immediately in their terminal
4. Pipe the output to analysis tools for deeper inspection
5. Trust that nothing is being modified or hidden
6. Distinguish between multiple simultaneous connections effortlessly
