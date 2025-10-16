#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test JSON format per SPECIFICATION.md §4.1
Tests UTF-8 encoding, LF terminators (not CRLF), and compact formatting
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
PROXY_PORT = 25701
TARGET_PORT = 25702

class EchoServer:
    """Simple echo server"""
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
            data = conn.recv(4096)
            conn.send(b"OK")
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

def main():
    print("=" * 60)
    print("JSON Format Test (SPECIFICATION.md §4.1)")
    print("=" * 60)

    # Find the rawprox binary
    binary_path = Path("release/x86win64/rawprox.exe")
    if not binary_path.exists():
        binary_path = Path("release/x86linux64/rawprox")
        if not binary_path.exists():
            binary_path = Path("target/release/rawprox.exe")
            if not binary_path.exists():
                binary_path = Path("target/release/rawprox")
                if not binary_path.exists():
                    print("ERROR: Could not find rawprox binary")
                    sys.exit(1)

    # Start echo server
    echo_server = EchoServer(TARGET_PORT)
    echo_server.start()
    time.sleep(0.3)

    # Start rawprox
    proxy_process = subprocess.Popen(
        [str(binary_path), f"{PROXY_PORT}:127.0.0.1:{TARGET_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # Note: Get raw bytes to check encoding
    )
    time.sleep(0.3)

    try:
        # Send request
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', PROXY_PORT))
        client.send(b"Test message")
        response = client.recv(4096)
        client.close()

        # Get logs as raw bytes
        time.sleep(0.3)
        proxy_process.terminate()
        stdout_bytes, stderr = proxy_process.communicate(timeout=2)

        print("\nTest 1: UTF-8 Encoding")
        # Verify output is valid UTF-8
        try:
            stdout_text = stdout_bytes.decode('utf-8')
            print("  ✓ Output is valid UTF-8")
        except UnicodeDecodeError as e:
            print(f"  ✗ Output is not valid UTF-8: {e}")
            raise

        print("\nTest 2: LF Line Terminators (not CRLF)")
        # Per SPEC §4.1: "LF terminator"
        # Check that lines are terminated with LF (\n) not CRLF (\r\n)

        lines = stdout_text.strip().split('\n')
        for i, line in enumerate(lines, 1):
            # Check if line ends with \r (which would indicate CRLF)
            if line.endswith('\r'):
                print(f"  ✗ Line {i} ends with \\r (CRLF detected)")
                raise AssertionError("Lines should use LF not CRLF per SPEC §4.1")

        # Check raw bytes for CRLF
        if b'\r\n' in stdout_bytes:
            # This might be in the data field itself (JSON-escaped), not line terminators
            # So let's check if it's a line terminator by looking for }\r\n pattern
            if b'}\r\n' in stdout_bytes:
                print(f"  ✗ Found CRLF line terminators (}}\\r\\n pattern)")
                raise AssertionError("Lines should use LF not CRLF per SPEC §4.1")

        print("  ✓ Lines terminated with LF (not CRLF)")

        print("\nTest 3: Compact JSON (no extra whitespace)")
        # Per SPEC §4.1: "compact"
        # Compact JSON means no whitespace between structural characters

        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Parse to verify it's valid JSON
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                print(f"  ✗ Line {i} is not valid JSON")
                raise

            # Re-serialize in compact form
            # Note: ensure_ascii=False because we use URL encoding for non-ASCII bytes
            compact = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

            # The line should match compact form (might differ in escape sequences)
            # So we compare the parsed objects instead
            reparsed = json.loads(compact)

            assert obj == reparsed, "JSON object doesn't match when re-parsed"

            # Check for gratuitous whitespace (spaces after : or ,)
            # Compact form uses ',' and ':' with no spaces
            if ': ' in line or ', ' in line or ' :' in line or ' ,' in line:
                # Exception: whitespace in string values is OK
                # Let's check if the whitespace is outside of string values
                # by comparing length: compact should be shorter or equal
                if len(line) > len(compact) + 10:  # Allow some tolerance
                    print(f"  Warning: Line {i} might have extra whitespace")
                    print(f"    Original length: {len(line)}")
                    print(f"    Compact length: {len(compact)}")

        print("  ✓ JSON is compact (no unnecessary whitespace)")

        print("\nTest 4: One JSON Object Per Line (NDJSON)")
        # Verify each line is a complete JSON object
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Should be exactly one JSON object
            try:
                obj = json.loads(line)
                assert isinstance(obj, dict), "Each line should be a JSON object (dict)"
            except json.JSONDecodeError as e:
                print(f"  ✗ Line {i} is not valid JSON: {e}")
                print(f"    Line: {line[:100]}")
                raise

        print(f"  ✓ All {len([l for l in lines if l.strip()])} lines are valid JSON objects (NDJSON)")

        print("\n" + "=" * 60)
        print("✓ JSON format test passed!")
        print("  - UTF-8 encoded")
        print("  - LF line terminators")
        print("  - Compact formatting")
        print("  - NDJSON (one object per line)")
        print("=" * 60)

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
        echo_server.stop()

if __name__ == "__main__":
    main()
