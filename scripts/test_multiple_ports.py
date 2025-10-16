#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test multiple port forwarding rules per SPECIFICATION.md §3.1 and §2.2
Tests that multiple port forwarding rules can be specified and work simultaneously
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
PROXY_PORT_1 = 25301
PROXY_PORT_2 = 25302
PROXY_PORT_3 = 25303
TARGET_PORT_1 = 25304
TARGET_PORT_2 = 25305
TARGET_PORT_3 = 25306

class EchoServer:
    """Simple echo server for testing"""
    def __init__(self, port, response_prefix):
        self.port = port
        self.response_prefix = response_prefix
        self.server = None
        self.running = False
        self.thread = None

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('127.0.0.1', self.port))
        self.server.listen(5)
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
                response = f"{self.response_prefix}:{data.decode()}".encode()
                conn.send(response)
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

def send_request(proxy_port, message, expected_prefix):
    """Send a request through the proxy and verify response"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', proxy_port))
        client.send(message.encode())
        response = client.recv(4096).decode()
        client.close()

        # Verify response has expected prefix
        assert response.startswith(expected_prefix), \
            f"Expected response starting with '{expected_prefix}', got '{response}'"
        return True
    except Exception as e:
        print(f"Client error on port {proxy_port}: {e}")
        return False

def main():
    print("=" * 60)
    print("Multiple Port Forwarding Test (SPECIFICATION.md §3.1, §2.2)")
    print("=" * 60)

    # Find the rawprox binary
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)

    # Start three echo servers on different ports
    servers = [
        EchoServer(TARGET_PORT_1, "SERVER1"),
        EchoServer(TARGET_PORT_2, "SERVER2"),
        EchoServer(TARGET_PORT_3, "SERVER3"),
    ]

    for server in servers:
        server.start()
    time.sleep(0.5)

    # Start rawprox with THREE port forwarding rules
    proxy_process = subprocess.Popen(
        [
            str(binary_path),
            f"{PROXY_PORT_1}:127.0.0.1:{TARGET_PORT_1}",
            f"{PROXY_PORT_2}:127.0.0.1:{TARGET_PORT_2}",
            f"{PROXY_PORT_3}:127.0.0.1:{TARGET_PORT_3}",
            "--flush-interval-ms=100",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(0.5)

    try:
        print("\nTesting 3 simultaneous port forwardings...")

        # Test all three ports work
        tests = [
            (PROXY_PORT_1, "test1", "SERVER1"),
            (PROXY_PORT_2, "test2", "SERVER2"),
            (PROXY_PORT_3, "test3", "SERVER3"),
        ]

        for proxy_port, message, expected_prefix in tests:
            success = send_request(proxy_port, message, expected_prefix)
            assert success, f"Failed to communicate through port {proxy_port}"
            print(f"  ✓ Port {proxy_port} forwarding works")

        # Send concurrent requests to all three ports
        print("\nSending concurrent requests to all three ports...")
        threads = []
        for proxy_port, message, expected_prefix in tests:
            thread = threading.Thread(
                target=send_request,
                args=(proxy_port, f"concurrent-{message}", expected_prefix)
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        print("  ✓ All concurrent requests completed")

        # Get logs
        time.sleep(0.5)
        proxy_process.terminate()
        stdout, stderr = proxy_process.communicate(timeout=2)

        # Parse logs
        logs = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Failed to parse: {line}")
                    raise

        # Verify we have logs from all three ports
        # Check from/to addresses contain our three target ports
        target_ports_seen = set()
        for log in logs:
            to_addr = log.get('to', '')
            from_addr = log.get('from', '')

            for port in [TARGET_PORT_1, TARGET_PORT_2, TARGET_PORT_3]:
                if f":{port}" in to_addr or f":{port}" in from_addr:
                    target_ports_seen.add(port)

        print(f"\nFound logs for target ports: {sorted(target_ports_seen)}")

        assert TARGET_PORT_1 in target_ports_seen, \
            f"Missing logs for target port {TARGET_PORT_1}"
        assert TARGET_PORT_2 in target_ports_seen, \
            f"Missing logs for target port {TARGET_PORT_2}"
        assert TARGET_PORT_3 in target_ports_seen, \
            f"Missing logs for target port {TARGET_PORT_3}"

        print("  ✓ All three port forwardings logged correctly")

        # Verify we have multiple unique ConnIDs (at least 3, one per port)
        conn_ids = set(log['ConnID'] for log in logs)
        print(f"\nFound {len(conn_ids)} unique ConnID(s): {sorted(conn_ids)}")

        assert len(conn_ids) >= 3, \
            f"Expected at least 3 unique ConnIDs (one per port), got {len(conn_ids)}"

        print("\n" + "=" * 60)
        print("✓ Multiple port forwarding test passed!")
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

        for server in servers:
            server.stop()

if __name__ == "__main__":
    main()
