#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import subprocess
import socket
import json
import time
import threading
import os
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def find_free_port():
    """Find an available port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def test_bidirectional_concurrent():
    """Test simultaneous bidirectional data flow (SPEC §8.2)"""
    print("TEST: Concurrent bidirectional data transfer")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server (but we'll control it manually for bidirectional test)
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))
        client_addr = client.getsockname()

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send data in BOTH directions simultaneously
        client_data = b"Client->Server data AAAA"
        server_data = b"Server->Client data BBBB"

        # Send from both ends at once
        client.send(client_data)
        server_conn.send(server_data)

        # Receive from both ends
        server_received = server_conn.recv(1024)
        client_received = client.recv(1024)

        # Verify data integrity
        assert server_received == client_data, \
            f"Server received incorrect data: {server_received}"
        assert client_received == server_data, \
            f"Client received incorrect data: {client_received}"

        # Close
        client.close()
        server_conn.close()
        # Wait for at least one flush cycle (100ms interval + buffer)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find data entries for both directions
    client_to_server = []
    server_to_client = []

    for e in events:
        if 'data' in e:
            # Check direction based on from/to
            if str(client_addr[1]) in e['from']:
                client_to_server.append(e)
            elif str(target_port) in e['from']:
                server_to_client.append(e)

    assert len(client_to_server) > 0, "No client->server data logged"
    assert len(server_to_client) > 0, "No server->client data logged"

    # Verify data content (may be split across multiple entries)
    c2s_data = ''.join(e['data'] for e in client_to_server)
    s2c_data = ''.join(e['data'] for e in server_to_client)

    assert "Client->Server" in c2s_data, \
        f"Client->Server data not logged correctly: {c2s_data}"
    assert "Server->Client" in s2c_data, \
        f"Server->Client data not logged correctly: {s2c_data}"

    print("✓ Bidirectional data transferred correctly")
    print(f"✓ Client->Server entries: {len(client_to_server)}")
    print(f"✓ Server->Client entries: {len(server_to_client)}")

def test_rapid_bidirectional():
    """Test rapid alternating bidirectional traffic"""
    print("\nTEST: Rapid alternating bidirectional traffic")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send multiple messages rapidly in both directions
        for i in range(5):
            # Client sends
            msg = f"C{i}".encode()
            client.send(msg)
            assert server_conn.recv(1024) == msg

            # Server sends
            msg = f"S{i}".encode()
            server_conn.send(msg)
            assert client.recv(1024) == msg

        # Close
        client.close()
        server_conn.close()
        # Wait for at least one flush cycle (100ms interval + buffer)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Count data entries
    data_entries = [e for e in events if 'data' in e]

    # Should have at least 10 entries (5 client->server, 5 server->client)
    assert len(data_entries) >= 10, \
        f"Expected at least 10 data entries, got {len(data_entries)}"

    print(f"✓ Rapid bidirectional traffic: {len(data_entries)} data entries")

def main():
    print("=" * 60)
    print("Testing Bidirectional Concurrent Traffic")
    print("=" * 60)

    test_bidirectional_concurrent()
    test_rapid_bidirectional()

    print("\n" + "=" * 60)
    print("✓ All bidirectional traffic tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
