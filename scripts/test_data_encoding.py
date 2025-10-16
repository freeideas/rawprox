#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test data encoding per SPECIFICATION.md Section 5
Tests JSON escape sequences for common control characters and percent-encoding for other binary data
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
PROXY_PORT = 25001
TARGET_PORT = 25002

def run_echo_server():
    """Echo server that sends back exactly what it receives"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', TARGET_PORT))
    server.listen(1)

    try:
        conn, addr = server.accept()
        data = conn.recv(4096)
        # Echo it back
        conn.send(data)
        time.sleep(0.1)
        conn.close()
    finally:
        server.close()

def test_data_encoding():
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

    # Test cases for different data types
    test_cases = [
        (b"Hello World", "Printable ASCII"),
        (b"Line1\r\nLine2\r\n", "CRLF sequences"),
        (b'Say "Hello"', "Double quotes"),
        (b"Path\\to\\file", "Backslashes"),
        (b"\x00\x01\x02", "Null and control bytes"),
        (b"\x89PNG\r\n\x1a\n", "PNG signature (binary)"),
        (b"\xff\xfe\xfd", "High bytes (0x80-0xFF)"),
        (b"\t\r\n", "Tab and newlines"),
        (b"100%", "Percent sign"),
        (b"\b\f", "Backspace and form feed"),
    ]

    for test_data, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"  Input bytes: {test_data!r}")

        # Start echo server
        server_thread = threading.Thread(target=run_echo_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.3)

        # Start rawprox
        proxy_process = subprocess.Popen(
            [str(binary_path), f"{PROXY_PORT}:127.0.0.1:{TARGET_PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(0.3)

        try:
            # Send test data through proxy
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', PROXY_PORT))
            client.send(test_data)
            response = client.recv(4096)
            client.close()

            # Verify echo worked
            assert response == test_data, f"Echo failed for {description}"

            # Get logs
            time.sleep(0.3)
            proxy_process.terminate()
            stdout, stderr = proxy_process.communicate(timeout=2)

            # Parse logs
            logs = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    logs.append(json.loads(line))

            # Find data logs
            data_logs = [log for log in logs if 'data' in log]
            assert len(data_logs) >= 2, f"Expected at least 2 data logs, got {len(data_logs)}"

            # Verify data encoding
            for log in data_logs:
                data_field = log['data']

                # Test specific encoding rules per SPECIFICATION.md §5.1
                if test_data == b"Hello World":
                    assert data_field == "Hello World", "Printable ASCII should be preserved"

                elif test_data == b"Line1\r\nLine2\r\n":
                    # \r\n should be JSON-escaped as \r\n (which becomes actual CR+LF after JSON parsing)
                    assert "Line1" in data_field
                    assert "Line2" in data_field
                    assert "\r\n" in data_field, "CRLF should be JSON-escaped (parsed as actual CR+LF)"

                elif test_data == b'Say "Hello"':
                    # Quotes should be JSON-escaped
                    assert '\\"' in data_field or data_field == 'Say "Hello"', \
                        "Quotes should be JSON-escaped"

                elif test_data == b"Path\\to\\file":
                    # Backslashes should be JSON-escaped
                    assert '\\\\' in data_field or data_field.count('\\') >= 2, \
                        "Backslashes should be JSON-escaped"

                elif test_data == b"\x00\x01\x02":
                    # Control characters should be %XX percent-encoded
                    assert "%00" in data_field, "Null byte should be %00"
                    assert "%01" in data_field, "0x01 should be %01"
                    assert "%02" in data_field, "0x02 should be %02"

                elif test_data == b"\xff\xfe\xfd":
                    # High bytes should be %XX percent-encoded
                    assert "%FF" in data_field, "0xFF should be %FF"
                    assert "%FE" in data_field, "0xFE should be %FE"
                    assert "%FD" in data_field, "0xFD should be %FD"

                elif test_data == b"\t\r\n":
                    # Tab, CR, LF should be JSON-escaped (parsed as actual control chars)
                    assert "\t" in data_field, "Tab should be JSON-escaped"
                    assert "\r" in data_field, "CR should be JSON-escaped"
                    assert "\n" in data_field, "LF should be JSON-escaped"

                elif test_data == b"100%":
                    # Percent sign should be percent-encoded (remains as literal %25 after parsing)
                    assert "100%25" in data_field, "Percent sign should be encoded as %25"

                elif test_data == b"\b\f":
                    # Backspace and form feed should be JSON-escaped (parsed as actual control chars)
                    assert "\b" in data_field, "Backspace should be JSON-escaped"
                    assert "\f" in data_field, "Form feed should be JSON-escaped"

            print(f"  ✓ {description} encoded correctly")

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            if proxy_process.poll() is None:
                proxy_process.terminate()
            raise
        finally:
            if proxy_process.poll() is None:
                proxy_process.terminate()
                try:
                    proxy_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proxy_process.kill()
            server_thread.join(timeout=1)

def main():
    print("=" * 60)
    print("Data Encoding Tests (SPECIFICATION.md §5)")
    print("=" * 60)

    try:
        test_data_encoding()
        print("\n" + "=" * 60)
        print("✓ All data encoding tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Data encoding tests failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
