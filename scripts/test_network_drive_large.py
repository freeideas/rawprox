#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test network drive output with large single-chunk data (>64KB per log entry)

This test combines two scenarios:
1. Writing to Windows network drives (H:, G:)
2. Large binary responses that create >64KB log entries

This is the exact scenario from tmp/BUG_REPORT.md where line 646 was truncated
at 63,938 bytes when writing to network drive H:.
"""

import sys
import subprocess
import socket
import json
import time
import threading
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Test configuration - larger than the 63,938 byte truncation point
LARGE_RESPONSE_SIZE = 256 * 1024  # 256KB

def find_free_port():
    """Find an available port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

class LargeResponseServer:
    """Server that sends a large binary response"""
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
            conn.recv(1024)

            # Send large binary response (mimics Alfresco binary download)
            # Use repeating byte pattern so we can verify data integrity
            large_data = bytes(range(256)) * (LARGE_RESPONSE_SIZE // 256)
            conn.sendall(large_data)

            time.sleep(0.1)
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
    """Validate that a NDJSON line is syntactically complete (not truncated)"""
    line = line_text.rstrip('\n')

    # Check 1: Must end with closing brace
    if not line.endswith('}'):
        return False, f"Missing closing brace - line truncated at {len(line)} chars"

    # Check 2: Must parse as valid JSON
    try:
        entry = json.loads(line)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    # Check 3: If it's a data entry, must have complete structure
    if 'data' in entry:
        if not isinstance(entry['data'], str):
            return False, "'data' field is not a string"

        # Must have from and to fields (these are after 'data' in field order)
        if 'from' not in entry:
            return False, "Missing 'from' field - likely truncated after 'data'"
        if 'to' not in entry:
            return False, "Missing 'to' field - likely truncated after 'data'"

        # Check for incomplete percent encoding (sign of truncation)
        data_value = entry['data']
        if data_value.endswith('%') or data_value.endswith('%0') or data_value.endswith('%1'):
            return False, "'data' field has incomplete percent encoding - truncated mid-byte"

    return True, None

def test_single_drive(drive_path):
    """Test output to a single network drive with large data"""
    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    output_file = Path(drive_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Remove output file if it exists
    if output_file.exists():
        output_file.unlink()

    local_port = find_free_port()
    target_port = find_free_port()

    print(f"  Output: {output_file}")
    print(f"  Proxy: localhost:{local_port} -> 127.0.0.1:{target_port}")
    print(f"  Response size: {LARGE_RESPONSE_SIZE:,} bytes")

    # Start server
    server = LargeResponseServer(target_port)
    server.start()
    time.sleep(0.3)

    # Start proxy with DEFAULT flush interval (2s) - this is the production config
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", f"@{output_file}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.3)

    try:
        # Connect and request large binary data
        print("  Requesting large binary response...")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))
        client.sendall(b"GET /binary-data HTTP/1.1\r\n\r\n")

        # Receive the large response
        response = b""
        while len(response) < LARGE_RESPONSE_SIZE:
            chunk = client.recv(8192)
            if not chunk:
                break
            response += chunk

        client.close()
        print(f"  ✓ Received {len(response):,} bytes")

        # CRITICAL: Wait for 2-second buffer swap interval + margin
        print("  Waiting 2.5 seconds for buffer swap to network drive...")
        time.sleep(2.5)

    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        server.stop()

        # Capture proxy output
        stdout, stderr = proxy.communicate()
        if stderr:
            print("  [Proxy stderr]:")
            for line in stderr.strip().split('\n'):
                if line.strip():
                    print(f"    {line}")

    # Verify file exists
    if not output_file.exists():
        print(f"  ✗ FAIL: Output file not created")
        return False

    file_size = output_file.stat().st_size
    print(f"  File size: {file_size:,} bytes")

    if file_size == 0:
        print(f"  ✗ FAIL: File is empty (0 bytes)")
        print("    This is the LESSONS_LEARNED.md silent data loss bug")
        return False

    # Read and validate each line individually
    print("  Validating line completeness...")
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"  Total lines: {len(lines)}")

    truncated_lines = []
    large_entries = []

    for i, line in enumerate(lines, 1):
        is_valid, error_msg = validate_line_completeness(i, line)

        if not is_valid:
            truncated_lines.append((i, len(line), error_msg))
            print(f"  ✗ Line {i} TRUNCATED: {error_msg}")
            print(f"    Line length: {len(line):,} chars")
            print(f"    Last 100 chars: ...{line[-100:]}")
        else:
            # Check if this is a large data entry
            try:
                entry = json.loads(line.rstrip('\n'))
                if 'data' in entry:
                    data_len = len(entry['data'])
                    if data_len > 60000:  # Approaching the 63,938 truncation point
                        large_entries.append((i, data_len))
            except:
                pass

    if large_entries:
        print(f"  Large data entries found ({len(large_entries)}):")
        for line_num, data_len in large_entries:
            status = "✓" if (line_num, data_len, None) not in [(t[0], t[1], None) for t in truncated_lines] else "✗"
            print(f"    {status} Line {line_num}: {data_len:,} chars (encoded)")

    if truncated_lines:
        print(f"\n  ✗✗✗ BUG REPRODUCED ✗✗✗")
        print(f"  {len(truncated_lines)} truncated line(s) detected!")
        print(f"  This matches tmp/BUG_REPORT.md:")
        print(f"    - Large data entries >63KB are truncated")
        print(f"    - Missing closing quote, from/to fields, closing brace")
        print(f"    - Silent failure on network drive writes")
        return False
    else:
        print(f"  ✓ All {len(lines)} lines are complete and valid")
        return True

def main():
    print("=" * 60)
    print("Network Drive + Large Data Test (Bug Reproduction)")
    print("=" * 60)
    print("\nReproduces: tmp/BUG_REPORT.md line 646 truncation")
    print("Scenario: Large binary responses (>64KB) written to network drive")
    print()

    # Check which network drives exist
    test_drives = []
    if Path("h:/").exists():
        test_drives.append(("H:", "h:/tmp/rawprox_large_test.ndjson"))
    if Path("g:/").exists():
        test_drives.append(("G:", "g:/my drive/tmp/rawprox_large_test.ndjson"))

    if not test_drives:
        print("⊘ No network drives (G: or H:) found - skipping test")
        print()
        print("Note: This test requires a Windows network drive to reproduce")
        print("      the truncation bug from tmp/BUG_REPORT.md")
        print()
        print("=" * 60)
        print("✓ Test skipped (no network drives available)")
        print("=" * 60)
        return

    print(f"Found {len(test_drives)} network drive(s): {', '.join(d[0] for d in test_drives)}")
    print()

    results = []
    for drive_name, drive_path in test_drives:
        print(f"Testing {drive_name}...")
        print("-" * 60)
        success = test_single_drive(drive_path)
        results.append((drive_name, success))
        print()

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    failed = [r for r in results if not r[1]]

    if failed:
        print(f"✗ {len(failed)} drive(s) FAILED:")
        for drive_name, _ in failed:
            print(f"  ✗ {drive_name}: Truncation detected (BUG REPRODUCED)")
        print()
        print("The bug from tmp/BUG_REPORT.md is present!")
        print("See reports/bug-remedy_report.md for fix recommendations.")
        sys.exit(1)
    else:
        print(f"✓ All {len(results)} drive(s) PASSED")
        print()
        print("No truncation detected.")
        print("Note: Bug may only occur with specific:")
        print("  - Network drive configurations (SMB/CIFS settings)")
        print("  - Very large single log entries (>100KB)")
        print("  - Buffer accumulation patterns")

if __name__ == "__main__":
    main()
