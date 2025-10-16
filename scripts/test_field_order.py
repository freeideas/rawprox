#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test field order per SPECIFICATION.md §4.1 and §15
Field order must be: time, ConnID, event/data, from, to
"""

import socket
import subprocess
import threading
import time
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Test configuration
PROXY_PORT = 25201
TARGET_PORT = 25202

def run_echo_server():
    """Simple echo server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', TARGET_PORT))
    server.listen(1)

    try:
        conn, addr = server.accept()
        data = conn.recv(4096)
        conn.send(b"OK")
        time.sleep(0.1)
        conn.close()
    finally:
        server.close()

def main():
    print("=" * 60)
    print("Field Order Test (SPECIFICATION.md §4.1, §15)")
    print("=" * 60)

    # Find the rawprox binary
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)

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
        # Send request
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', PROXY_PORT))
        client.send(b"Test")
        response = client.recv(4096)
        client.close()

        # Get logs
        time.sleep(0.3)
        proxy_process.terminate()
        stdout, stderr = proxy_process.communicate(timeout=2)

        print("\nVerifying field order in NDJSON output...")

        # Parse raw JSON to check field order
        for line_num, line in enumerate(stdout.strip().split('\n'), 1):
            if not line.strip():
                continue

            # Parse JSON while preserving order
            # Python 3.7+ dicts preserve insertion order
            import json
            obj = json.loads(line)
            keys = list(obj.keys())

            print(f"\nLine {line_num}: {keys}")

            # Field order per SPECIFICATION.md §4.1:
            # time, ConnID, (event OR data), from, to
            assert keys[0] == 'time', f"First field must be 'time', got '{keys[0]}'"
            assert keys[1] == 'ConnID', f"Second field must be 'ConnID', got '{keys[1]}'"

            # Third field is either 'event' or 'data'
            assert keys[2] in ['event', 'data'], \
                f"Third field must be 'event' or 'data', got '{keys[2]}'"

            assert keys[3] == 'from', f"Fourth field must be 'from', got '{keys[3]}'"
            assert keys[4] == 'to', f"Fifth field must be 'to', got '{keys[4]}'"

            assert len(keys) == 5, f"Must have exactly 5 fields, got {len(keys)}"

            print(f"  ✓ Correct field order: {' → '.join(keys)}")

        print("\n" + "=" * 60)
        print("✓ Field order test passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        sys.exit(1)
    finally:
        if proxy_process.poll() is None:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
        server_thread.join(timeout=1)

if __name__ == "__main__":
    main()
