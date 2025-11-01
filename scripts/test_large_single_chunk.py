#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test for large single-chunk data logging (>64KB per log entry)

This test reproduces the bug reported in tmp/BUG_REPORT.md where large
binary HTTP responses (64KB+) are truncated when logged to network drives.

The bug occurs when:
1. A single read() returns >64KB of data
2. This creates a single NDJSON log line >64KB
3. File.AppendAllText() on network drives silently truncates the line
4. No exception is thrown, but the JSON line is incomplete
"""

import socket
import subprocess
import threading
import time
import json
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Test configuration
PROXY_PORT = 25501
TARGET_PORT = 25502

# Create large message (128KB) to trigger single large log entry
# This mimics the Alfresco binary response scenario
LARGE_RESPONSE_SIZE = 128 * 1024  # 128KB

class LargeResponseServer:
    """Server that sends a large response in one chunk"""
    def __init__(self, port):
        self.port = port
        self.server = None
        self.running = False
        self.thread = None

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('127.0.0.1', self.port))
        self.server.listen(1)
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
            # Read request
            request = conn.recv(1024)
            if not request:
                return

            # Send large response (128KB) in a SINGLE send()
            # This ensures the proxy receives it in large chunks (potentially 64KB+ per read)
            large_data = bytes(range(256)) * (LARGE_RESPONSE_SIZE // 256)

            # Send all at once - the proxy's 32KB buffer may still chunk this,
            # but with network buffering, it might receive 64KB+ in a single read
            conn.sendall(large_data)

            time.sleep(0.2)
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
    """Validate that a NDJSON line is syntactically complete"""
    line = line_text.rstrip('\n')

    # Check 1: Must end with closing brace
    if not line.endswith('}'):
        return False, f"Line {line_num} missing closing brace (truncated?)"

    # Check 2: Must parse as valid JSON
    try:
        entry = json.loads(line)
    except json.JSONDecodeError as e:
        return False, f"Line {line_num} invalid JSON: {e}\nLast 200 chars: {line[-200:]}"

    # Check 3: If it's a data entry, must have complete structure
    if 'data' in entry:
        if not isinstance(entry['data'], str):
            return False, f"Line {line_num} 'data' field is not a string"

        # Must have from and to fields
        if 'from' not in entry:
            return False, f"Line {line_num} missing 'from' field (truncated?)"
        if 'to' not in entry:
            return False, f"Line {line_num} missing 'to' field (truncated?)"

        # Verify data field is properly closed (no unterminated string)
        # The data field value should not end with escape or look truncated
        data_value = entry['data']
        # If data ends with incomplete percent encoding, it's likely truncated
        if data_value.endswith('%') or data_value.endswith('%0') or data_value.endswith('%1'):
            return False, f"Line {line_num} 'data' field appears truncated (incomplete percent encoding)"

    return True, None

def main():
    print("=" * 60)
    print("Large Single-Chunk Data Test (Bug Reproduction)")
    print("=" * 60)
    print("\nReproduces: tmp/BUG_REPORT.md truncation bug")
    print(f"Approach: Send {LARGE_RESPONSE_SIZE:,} byte response to trigger >64KB log entries")
    print()

    # Find the rawprox binary
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)

    # Use file output to reproduce the bug (it's a file I/O issue)
    output_file = Path("tmp/test_large_chunk.ndjson")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if output_file.exists():
        output_file.unlink()

    # Start response server
    response_server = LargeResponseServer(TARGET_PORT)
    response_server.start()
    time.sleep(0.5)

    # Start rawprox with file output and fast flush
    proxy_process = subprocess.Popen(
        [str(binary_path),
         f"{PROXY_PORT}:127.0.0.1:{TARGET_PORT}",
         f"@{output_file}",
         "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.5)

    try:
        print("Sending request through proxy...")

        # Connect and send small request
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', PROXY_PORT))
        client.sendall(b"GET /large-binary HTTP/1.1\r\n\r\n")

        # Receive large response
        print(f"Receiving large response ({LARGE_RESPONSE_SIZE:,} bytes)...")
        response = b""
        while len(response) < LARGE_RESPONSE_SIZE:
            chunk = client.recv(8192)
            if not chunk:
                break
            response += chunk

        client.close()

        print(f"  ✓ Received {len(response):,} bytes")

        # Wait for logs to be written
        time.sleep(0.5)

        proxy_process.terminate()
        _, stderr = proxy_process.communicate(timeout=5)

        if not output_file.exists():
            print(f"✗ Output file not created: {output_file}")
            sys.exit(1)

        file_size = output_file.stat().st_size
        print(f"\n  Output file: {file_size:,} bytes")

        # Read and validate each line
        print("\nValidating NDJSON line completeness...")
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"  Total lines: {len(lines)}")

        # Validate each line individually
        truncated_lines = []
        data_entry_sizes = []

        for i, line in enumerate(lines, 1):
            is_valid, error_msg = validate_line_completeness(i, line)

            if not is_valid:
                truncated_lines.append((i, error_msg))
                print(f"  ✗ Line {i}: {error_msg}")
            else:
                # Parse to get details
                entry = json.loads(line.rstrip('\n'))
                if 'data' in entry:
                    data_field_len = len(entry['data'])
                    data_entry_sizes.append(data_field_len)

                    # Check if this is a large entry (>64KB encoded)
                    if data_field_len > 64000:
                        print(f"  • Line {i}: Large data entry ({data_field_len:,} chars encoded)")

        # Report any truncated lines
        if truncated_lines:
            print("\n" + "=" * 60)
            print("❌ BUG REPRODUCED: Truncated lines detected!")
            print("=" * 60)
            print(f"\nTruncated lines: {len(truncated_lines)}")
            for line_num, error_msg in truncated_lines:
                print(f"  Line {line_num}: {error_msg}")
            print("\nThis matches the bug in tmp/BUG_REPORT.md:")
            print("  - Large data entries (>64KB) are truncated")
            print("  - Missing closing quote, from/to fields, closing brace")
            print("  - Invalid JSON cannot be parsed")
            sys.exit(1)
        else:
            print("\n  ✓ All lines are syntactically complete")

        # Analyze data entry sizes
        if data_entry_sizes:
            print(f"\nData entry size analysis:")
            print(f"  Total data entries: {len(data_entry_sizes)}")
            print(f"  Largest entry: {max(data_entry_sizes):,} chars (encoded)")
            print(f"  Average entry: {sum(data_entry_sizes)//len(data_entry_sizes):,} chars (encoded)")

            large_entries = [s for s in data_entry_sizes if s > 64000]
            if large_entries:
                print(f"  Entries >64KB: {len(large_entries)}")

        # Verify we can reconstruct the data
        print("\nReconstructing data from logs...")
        data_logs = []
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line.rstrip('\n'))
                if 'data' in entry:
                    data_logs.append(entry)

        # Server->client data
        server_to_client = [e for e in data_logs if f":{TARGET_PORT}" in e.get('from', '')]
        print(f"  Server->Client entries: {len(server_to_client)}")

        # Reconstruct
        import urllib.parse
        reconstructed = ""
        for entry in sorted(server_to_client, key=lambda x: x['time']):
            reconstructed += entry['data']

        # Decode (handle percent encoding and JSON escaping)
        reconstructed_bytes = urllib.parse.unquote(reconstructed, encoding='latin1').encode('latin1')

        print(f"  Original size: {len(response):,} bytes")
        print(f"  Reconstructed size: {len(reconstructed_bytes):,} bytes")

        if len(reconstructed_bytes) == len(response):
            print(f"  ✓ Data reconstruction successful!")
        else:
            print(f"  ✗ Size mismatch (possible data loss)")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("✓ Large single-chunk test PASSED")
        print("=" * 60)
        print("\nNo truncation detected with current implementation.")
        print("Note: This bug may be specific to network drives.")
        print("Run test_network_drive_large.py to test on H: drive.")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if proxy_process.poll() is None:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
        response_server.stop()

if __name__ == "__main__":
    main()
