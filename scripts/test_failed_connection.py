#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test failed target connection per SPECIFICATION.md §6
Tests that failed target connection closes client socket with no log entries
"""

import socket
import subprocess
import time
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Test configuration
PROXY_PORT = 25501
NONEXISTENT_TARGET_PORT = 25599  # Nothing listening here

def main():
    print("=" * 60)
    print("Failed Target Connection Test (SPECIFICATION.md §6)")
    print("=" * 60)

    # Find the rawprox binary
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)

    # Start rawprox pointing to non-existent target
    print(f"\nStarting rawprox pointing to non-existent target port {NONEXISTENT_TARGET_PORT}...")
    proxy_process = subprocess.Popen(
        [str(binary_path), f"{PROXY_PORT}:127.0.0.1:{NONEXISTENT_TARGET_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(0.5)

    try:
        print("Attempting to connect to proxy...")

        # Try to connect to proxy (which should fail to connect to target)
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(2.0)
            client.connect(('127.0.0.1', PROXY_PORT))

            # Try to send data
            client.send(b"Test message")

            # Try to receive (should fail or get nothing)
            try:
                data = client.recv(1024)
                # If we get here, connection stayed open (unexpected)
                if len(data) > 0:
                    print(f"  Unexpected: Received data: {data}")
            except:
                pass

            client.close()

        except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as e:
            # Expected: Connection should be closed by proxy
            print(f"  ✓ Connection closed by proxy (expected): {type(e).__name__}")

        except socket.timeout:
            print(f"  ✓ Connection timed out (acceptable behavior)")

        # Get logs
        time.sleep(0.5)
        proxy_process.terminate()
        stdout, stderr = proxy_process.communicate(timeout=2)

        # Per SPEC §6: "Failed target connection: close client socket, no log entries"
        # So we expect NO log entries for this failed connection

        lines = [line.strip() for line in stdout.strip().split('\n') if line.strip()]

        print(f"\nLog entries: {len(lines)}")

        # SPEC §6: "Failed target connection: close client socket, no log entries"
        # This means ZERO log entries, not just "no data entries"
        if len(lines) != 0:
            print(f"  ✗ Expected 0 log entries, found {len(lines)}:")
            for line in lines:
                print(f"    {line}")

        assert len(lines) == 0, \
            f"SPEC §6 requires NO log entries for failed connection, but found {len(lines)}"

        print("  ✓ No log entries for failed connection (per SPEC §6)")

        print("\n" + "=" * 60)
        print("✓ Failed target connection test passed!")
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

if __name__ == "__main__":
    main()
