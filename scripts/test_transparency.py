#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test data transparency per FOUNDATION.md and SPECIFICATION.md §1
Tests that every byte is forwarded unchanged - proxy is invisible to both ends
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
PROXY_PORT = 25601
TARGET_PORT = 25602

class VerifyingEchoServer:
    """Echo server that verifies exact bytes received"""
    def __init__(self, port):
        self.port = port
        self.server = None
        self.running = False
        self.thread = None
        self.received_data = None
        self.sent_data = None

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
            # Receive data
            data = conn.recv(4096)
            self.received_data = data

            # Send back a different pattern
            response = b"SERVER_RESPONSE:" + data[::-1]  # Reverse the data
            conn.send(response)
            self.sent_data = response

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
    print("Data Transparency Test (FOUNDATION.md, SPEC §1)")
    print("=" * 60)

    # Find the rawprox binary
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)

    # Test with various binary patterns
    test_cases = [
        b"Simple ASCII text",
        b"\x00\x01\x02\x03\x04\x05\xFF\xFE\xFD",  # Binary with nulls and high bytes
        b"\r\n\t\x00\\\"'<>{}[]",  # Special characters
        bytes(range(256)),  # All possible byte values
        b"A" * 1000,  # Repeated pattern
    ]

    for i, test_data in enumerate(test_cases, 1):
        print(f"\nTest {i}: {len(test_data)} bytes")
        print(f"  Pattern: {test_data[:50]!r}{'...' if len(test_data) > 50 else ''}")

        # Start echo server
        echo_server = VerifyingEchoServer(TARGET_PORT)
        echo_server.start()
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
            # Send data through proxy
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', PROXY_PORT))
            client.send(test_data)

            # Receive response
            response = client.recv(4096)
            client.close()

            # Wait for server to record what it received
            time.sleep(0.2)

            # Verify transparency: server should receive EXACT same bytes
            assert echo_server.received_data == test_data, \
                f"Server received different data!\n  Sent: {test_data!r}\n  Received: {echo_server.received_data!r}"

            print(f"  ✓ Server received exact bytes (client->server transparent)")

            # Verify transparency: client should receive EXACT same bytes server sent
            assert response == echo_server.sent_data, \
                f"Client received different data!\n  Server sent: {echo_server.sent_data!r}\n  Client received: {response!r}"

            print(f"  ✓ Client received exact bytes (server->client transparent)")

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            raise
        finally:
            if proxy_process.poll() is None:
                proxy_process.terminate()
                try:
                    proxy_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proxy_process.kill()
            echo_server.stop()

    print("\n" + "=" * 60)
    print("✓ All transparency tests passed!")
    print("  Every byte forwarded unchanged - proxy is invisible")
    print("=" * 60)

if __name__ == "__main__":
    main()
