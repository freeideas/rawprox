#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test to reproduce the exact truncation pattern from netlog_new.ndjson

Pattern observed:
- Lines 640-643: ~75KB each (4 lines × 75KB = ~300KB accumulated)
- Line 644: 3KB
- Line 645: 21KB
- Line 646: 63,938 bytes TRUNCATED (should be much larger)

Strategy: Create a massive buffer with 300KB+ of data, then write to H: drive
"""

import sys
import subprocess
import socket
import json
import time
import threading
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Match the pattern: multiple 75KB+ responses
RESPONSE_SIZES = [
    200 * 1024,  # 200KB - will create multiple 75KB log entries
    200 * 1024,
    200 * 1024,
    200 * 1024,
]

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        return s.getsockname()[1]

class MassiveResponseServer:
    def __init__(self, port, response_sizes):
        self.port = port
        self.response_sizes = response_sizes
        self.server = None
        self.running = False
        self.thread = None
        self.request_index = 0

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('127.0.0.1', self.port))
        self.server.listen(10)
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        while self.running:
            try:
                self.server.settimeout(0.5)
                conn, addr = self.server.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            conn.recv(1024)

            size = self.response_sizes[self.request_index % len(self.response_sizes)]
            self.request_index += 1

            # Binary data (will create percent-encoded log entries)
            large_data = bytes(range(256)) * (size // 256)
            conn.sendall(large_data)
            conn.close()
        except:
            pass

    def stop(self):
        self.running = False
        if self.server:
            self.server.close()
        if self.thread:
            self.thread.join(timeout=2)

def validate_line_completeness(line_num, line_text):
    line = line_text.rstrip('\n')

    if not line.endswith('}'):
        return False, f"Missing closing brace - ends with: ...{line[-50:]}"

    try:
        entry = json.loads(line)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if 'data' in entry:
        if 'from' not in entry:
            return False, "Missing 'from' field"
        if 'to' not in entry:
            return False, "Missing 'to' field"

        data_val = entry['data']
        if data_val.endswith('%'):
            return False, "Data ends with incomplete percent encoding: '%'"

    return True, None

def main():
    print("=" * 60)
    print("Massive Buffer Test (Exact Bug Pattern Reproduction)")
    print("=" * 60)
    print("\nReproducing pattern from H:/acex/prjx/AlfConn/tmp/netlog_new.ndjson:")
    print("  - Lines 640-643: ~75KB each")
    print("  - Line 646: Truncated at 63,938 bytes")
    print("\nStrategy: Accumulate 300KB+ buffer, then flush to H: drive")
    print()

    if not Path("h:/").exists():
        print("✗ H: drive not found - skipping test")
        sys.exit(0)

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    output_file = Path("h:/tmp/rawprox_massive_buffer.ndjson")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        output_file.unlink()

    local_port = find_free_port()
    target_port = find_free_port()

    print(f"Output: {output_file}")
    print(f"Proxy: localhost:{local_port} -> 127.0.0.1:{target_port}")

    server = MassiveResponseServer(target_port, RESPONSE_SIZES)
    server.start()
    time.sleep(0.3)

    # Use LONG flush interval (5 seconds) to accumulate massive buffer
    FLUSH_INTERVAL = 5000
    print(f"Flush interval: {FLUSH_INTERVAL}ms (accumulate large buffer)")

    proxy = subprocess.Popen(
        [str(binary),
         f"{local_port}:127.0.0.1:{target_port}",
         f"@{output_file}",
         f"--flush-interval-ms={FLUSH_INTERVAL}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.3)

    try:
        print(f"\nSending {len(RESPONSE_SIZES)} large requests rapidly...")

        total_sent = 0
        for i, size in enumerate(RESPONSE_SIZES):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', local_port))
            client.sendall(f"GET /data-{i} HTTP/1.1\r\n\r\n".encode())

            response = b""
            while len(response) < size:
                chunk = client.recv(8192)
                if not chunk:
                    break
                response += chunk

            client.close()
            total_sent += len(response)
            print(f"  Request {i+1}: {len(response):,} bytes received")

            # NO delay - send rapidly to accumulate buffer

        print(f"\nTotal data: {total_sent:,} bytes")
        print(f"Expected buffer: ~{total_sent * 2.5 / 1024:.0f}KB (with percent encoding)")

        # Wait for flush
        print(f"\nWaiting {FLUSH_INTERVAL/1000 + 0.5:.1f}s for buffer flush...")
        time.sleep(FLUSH_INTERVAL / 1000 + 0.5)

    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        server.stop()

        stdout, stderr = proxy.communicate()

    if not output_file.exists():
        print(f"\n✗ Output file not created")
        sys.exit(1)

    file_size = output_file.stat().st_size
    print(f"\nOutput file: {file_size:,} bytes")

    if file_size == 0:
        print("✗ File is empty")
        sys.exit(1)

    # Validate
    print("Validating line completeness...")
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"  Total lines: {len(lines)}")

    # Show line sizes
    print("\n  Line sizes:")
    large_lines = []
    for i, line in enumerate(lines, 1):
        line_len = len(line)
        if line_len > 20000:  # Large entries
            large_lines.append((i, line_len))
            print(f"    Line {i}: {line_len:,} chars")

    # Validate each line
    truncated_lines = []
    for i, line in enumerate(lines, 1):
        is_valid, error_msg = validate_line_completeness(i, line)
        if not is_valid:
            truncated_lines.append((i, len(line), error_msg))

    if truncated_lines:
        print("\n" + "=" * 60)
        print("✓✓✓ BUG REPRODUCED! ✓✓✓")
        print("=" * 60)
        print(f"\nTruncated lines found: {len(truncated_lines)}")
        for line_num, line_len, error in truncated_lines:
            print(f"\n  Line {line_num}: {line_len:,} chars")
            print(f"  Error: {error}")

        # Show details of truncated line
        if truncated_lines:
            trunc_line_num = truncated_lines[0][0]
            trunc_line = lines[trunc_line_num - 1]
            print(f"\n  Truncated line {trunc_line_num} details:")
            print(f"    First 100 chars: {trunc_line[:100]}")
            print(f"    Last 100 chars: ...{trunc_line[-100:]}")

        sys.exit(1)
    else:
        print(f"\n  ✓ All {len(lines)} lines complete")
        print("\n✗ Bug NOT reproduced with this pattern")

if __name__ == "__main__":
    main()
