#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test concurrent connections per SPECIFICATION.md §2.3 and §8
Tests that multiple simultaneous connections are handled correctly
with unique ConnIDs
"""

import socket
import subprocess
import threading
import time
import json
import sys
import os
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Test configuration
PROXY_PORT = 25101
TARGET_PORT = 25102
NUM_CONCURRENT = 5

class EchoServer:
    def __init__(self, port):
        self.port = port
        self.server = None
        self.running = False
        self.thread = None

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
            data = conn.recv(4096)
            if data:
                conn.send(data)
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

def send_request(proxy_port, message, request_id):
    """Send a request through the proxy"""
    try:
        print(f"  [Request {request_id}] Creating socket...", flush=True)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print(f"  [Request {request_id}] Connecting to proxy...", flush=True)
        client.connect(('127.0.0.1', proxy_port))

        print(f"  [Request {request_id}] Sending data...", flush=True)
        client.send(message)

        print(f"  [Request {request_id}] Waiting for response...", flush=True)
        response = client.recv(4096)

        print(f"  [Request {request_id}] Closing connection...", flush=True)
        client.close()

        print(f"  [Request {request_id}] Done! Response matches: {response == message}", flush=True)
        return response == message
    except Exception as e:
        print(f"  [Request {request_id}] ERROR: {e}", flush=True)
        return False

def main():
    print("=" * 60)
    print("Concurrent Connections Test (SPECIFICATION.md §2.3, §8)")
    print("=" * 60)

    # Find the rawprox binary
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)

    # Start echo server
    print(f"\nStarting echo server on port {TARGET_PORT}...", flush=True)
    echo_server = EchoServer(TARGET_PORT)
    echo_server.start()
    time.sleep(0.5)
    print(f"✓ Echo server started", flush=True)

    # Start rawprox
    print(f"Starting rawprox proxy on port {PROXY_PORT}...", flush=True)
    proxy_process = subprocess.Popen(
        [str(binary_path), f"{PROXY_PORT}:127.0.0.1:{TARGET_PORT}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(0.5)
    print(f"✓ Rawprox started", flush=True)

    try:
        print(f"\nSending {NUM_CONCURRENT} concurrent requests...")
        sys.stdout.flush()

        # Send multiple concurrent requests
        threads = []
        for i in range(NUM_CONCURRENT):
            message = f"Request #{i}".encode()
            print(f"Starting request {i}...", flush=True)
            thread = threading.Thread(target=send_request, args=(PROXY_PORT, message, i))
            thread.start()
            threads.append(thread)
            time.sleep(0.05)  # Slight stagger

        print(f"\nWaiting for all {NUM_CONCURRENT} requests to complete...", flush=True)
        # Wait for all requests to complete
        for i, thread in enumerate(threads):
            print(f"Waiting for thread {i}...", flush=True)
            thread.join()
            print(f"Thread {i} joined.", flush=True)

        print(f"✓ All {NUM_CONCURRENT} requests completed")

        # Get logs
        print(f"\nWaiting for proxy to flush logs...", flush=True)
        time.sleep(0.5)
        print(f"Terminating proxy process...", flush=True)
        proxy_process.terminate()
        print(f"Waiting for proxy to exit...", flush=True)
        stdout, stderr = proxy_process.communicate(timeout=2)
        print(f"✓ Proxy terminated", flush=True)

        # Parse logs
        print(f"\nParsing logs...", flush=True)
        logs = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Failed to parse: {line}")
                    raise
        print(f"✓ Parsed {len(logs)} log entries", flush=True)

        # Verify we have multiple unique ConnIDs
        conn_ids = set(log['ConnID'] for log in logs)
        print(f"\nFound {len(conn_ids)} unique ConnID(s): {sorted(conn_ids)}")

        assert len(conn_ids) >= 2, f"Expected multiple unique ConnIDs, got {len(conn_ids)}"

        # Verify all ConnIDs are 5-character base62
        for conn_id in conn_ids:
            assert len(conn_id) == 5, f"ConnID must be 5 chars: {conn_id}"
            assert all(c in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                      for c in conn_id), f"Invalid base62 ConnID: {conn_id}"

        # Verify each connection has complete lifecycle
        for conn_id in conn_ids:
            conn_logs = [log for log in logs if log['ConnID'] == conn_id]
            events = [log for log in conn_logs if 'event' in log]
            open_events = [e for e in events if e['event'] == 'open']
            close_events = [e for e in events if e['event'] == 'close']

            assert len(open_events) >= 1, f"ConnID {conn_id} missing open event"
            assert len(close_events) >= 1, f"ConnID {conn_id} missing close event"

        print(f"✓ All connections have complete lifecycle (open/close events)")
        print(f"✓ All ConnIDs are unique and properly formatted")

        print("\n" + "=" * 60)
        print("✓ Concurrent connections test passed!")
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
        echo_server.stop()

if __name__ == "__main__":
    main()
