#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Aggressive stress test to reproduce network drive truncation bug

Strategy: Create conditions most likely to trigger truncation:
1. Multiple large responses (128KB+) in quick succession
2. Accumulate large buffer content before flush
3. Single buffer flush with multiple 64KB+ log entries
4. Write to network drive H:
"""

import sys
import subprocess
import socket
import json
import time
import threading
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Aggressive configuration
LARGE_RESPONSE_SIZE = 150 * 1024  # 150KB per response
NUM_REQUESTS = 5  # 5 requests in quick succession
FLUSH_INTERVAL_MS = 500  # Faster than default to accumulate multiple requests

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        return s.getsockname()[1]

class StressTestServer:
    """Server that handles multiple large responses quickly"""
    def __init__(self, port, response_size):
        self.port = port
        self.response_size = response_size
        self.server = None
        self.running = False
        self.thread = None
        self.request_count = 0

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
            self.request_count += 1

            # Send large binary response
            large_data = bytes(range(256)) * (self.response_size // 256)
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
    """Validate NDJSON line is complete"""
    line = line_text.rstrip('\n')

    if not line.endswith('}'):
        return False, f"Missing closing brace"

    try:
        entry = json.loads(line)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    if 'data' in entry:
        if 'from' not in entry:
            return False, f"Missing 'from' field"
        if 'to' not in entry:
            return False, f"Missing 'to' field"

    return True, None

def main():
    print("=" * 60)
    print("Network Drive STRESS Test (Aggressive Truncation Test)")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Response size: {LARGE_RESPONSE_SIZE:,} bytes each")
    print(f"  Number of requests: {NUM_REQUESTS}")
    print(f"  Flush interval: {FLUSH_INTERVAL_MS}ms")
    print(f"  Strategy: Accumulate multiple large entries before flush")
    print()

    # Check for H: drive
    if not Path("h:/").exists():
        print("✗ H: drive not found - skipping test")
        sys.exit(0)

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    output_file = Path("h:/tmp/rawprox_stress_test.ndjson")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        output_file.unlink()

    local_port = find_free_port()
    target_port = find_free_port()

    print(f"Output: {output_file}")
    print(f"Proxy: localhost:{local_port} -> 127.0.0.1:{target_port}")

    # Start server
    server = StressTestServer(target_port, LARGE_RESPONSE_SIZE)
    server.start()
    time.sleep(0.3)

    # Start proxy with SHORT flush interval
    proxy = subprocess.Popen(
        [str(binary),
         f"{local_port}:127.0.0.1:{target_port}",
         f"@{output_file}",
         f"--flush-interval-ms={FLUSH_INTERVAL_MS}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.3)

    try:
        print(f"\nSending {NUM_REQUESTS} large requests rapidly...")

        for i in range(NUM_REQUESTS):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', local_port))
            client.sendall(f"GET /binary-data-{i} HTTP/1.1\r\n\r\n".encode())

            # Receive response
            response = b""
            while len(response) < LARGE_RESPONSE_SIZE:
                chunk = client.recv(8192)
                if not chunk:
                    break
                response += chunk

            client.close()
            print(f"  Request {i+1}/{NUM_REQUESTS}: {len(response):,} bytes")

            # Small delay between requests
            time.sleep(0.05)

        # Wait for buffer flush
        print(f"\nWaiting {(FLUSH_INTERVAL_MS/1000)*2:.1f}s for buffer flush...")
        time.sleep((FLUSH_INTERVAL_MS / 1000) * 2)

    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        server.stop()

        stdout, stderr = proxy.communicate()
        if stderr:
            print("\n[Proxy stderr]:")
            for line in stderr.strip().split('\n'):
                if line.strip():
                    print(f"  {line}")

    # Validate output file
    if not output_file.exists():
        print(f"\n✗ FAIL: Output file not created")
        sys.exit(1)

    file_size = output_file.stat().st_size
    print(f"\nOutput file: {file_size:,} bytes")

    if file_size == 0:
        print(f"✗ FAIL: File is empty")
        sys.exit(1)

    # Validate each line
    print("Validating line completeness...")
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"  Total lines: {len(lines)}")

    truncated_lines = []
    large_entries = []

    for i, line in enumerate(lines, 1):
        is_valid, error_msg = validate_line_completeness(i, line)

        if not is_valid:
            truncated_lines.append((i, len(line), error_msg))
            print(f"  ✗✗✗ Line {i} TRUNCATED: {error_msg}")
            print(f"      Line length: {len(line):,} chars")
            print(f"      Last 150 chars: ...{line[-150:]}")
        else:
            try:
                entry = json.loads(line.rstrip('\n'))
                if 'data' in entry:
                    data_len = len(entry['data'])
                    if data_len > 50000:
                        large_entries.append((i, data_len))
            except:
                pass

    if large_entries:
        print(f"\n  Large data entries: {len(large_entries)}")
        for line_num, data_len in large_entries[:10]:  # Show first 10
            print(f"    Line {line_num}: {data_len:,} chars")

    if truncated_lines:
        print("\n" + "=" * 60)
        print("✓✓✓ BUG REPRODUCED! ✓✓✓")
        print("=" * 60)
        print(f"\n{len(truncated_lines)} truncated line(s) detected!")
        print("\nTruncated lines:")
        for line_num, line_len, error in truncated_lines:
            print(f"  Line {line_num}: {line_len:,} chars - {error}")
        sys.exit(1)
    else:
        print(f"\n  ✓ All {len(lines)} lines are complete")
        print("\n" + "=" * 60)
        print("✗ Bug NOT reproduced")
        print("=" * 60)
        print("\nThe current implementation handles stress test correctly.")

if __name__ == "__main__":
    main()
