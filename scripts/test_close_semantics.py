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

def test_client_initiated_close():
    """Test close event from=client when client closes first (SPEC §4.3)"""
    print("TEST: Client-initiated close (from=client, to=server)")

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
        client_addr = client.getsockname()

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send some data
        client.send(b"Data")
        server_conn.recv(1024)

        # CLIENT closes first
        client.close()

        # Give server time to notice close
        time.sleep(0.2)

        # Server tries to recv - should get 0 bytes (EOF)
        data = server_conn.recv(1024)
        assert data == b"", "Server should receive EOF"

        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find close event
    close_events = [e for e in events if e.get('event') == 'close']
    assert len(close_events) > 0, "No close event found"

    close_event = close_events[0]

    # Verify from=client (the side that closed)
    from_addr = close_event['from']
    assert str(client_addr[1]) in from_addr, \
        f"Close event 'from' should be client address, got: {from_addr}"

    # Verify to=server
    to_addr = close_event['to']
    assert '127.0.0.1' in to_addr and str(target_port) in to_addr, \
        f"Close event 'to' should be server address, got: {to_addr}"

    print(f"✓ Client-initiated close: from={from_addr}, to={to_addr}")

def test_server_initiated_close():
    """Test close event from=server when server closes first (SPEC §4.3)"""
    print("\nTEST: Server-initiated close (from=server, to=client)")

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
        client_addr = client.getsockname()

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send some data
        client.send(b"Data")
        server_conn.recv(1024)

        # SERVER closes first
        server_conn.close()

        # Give client time to notice close
        time.sleep(0.2)

        # Client tries to recv - should get 0 bytes (EOF)
        data = client.recv(1024)
        assert data == b"", "Client should receive EOF"

        client.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find close event
    close_events = [e for e in events if e.get('event') == 'close']
    assert len(close_events) > 0, "No close event found"

    close_event = close_events[0]

    # Verify from=server (the side that closed)
    from_addr = close_event['from']
    assert '127.0.0.1' in from_addr and str(target_port) in from_addr, \
        f"Close event 'from' should be server address, got: {from_addr}"

    # Verify to=client
    to_addr = close_event['to']
    assert str(client_addr[1]) in to_addr, \
        f"Close event 'to' should be client address, got: {to_addr}"

    print(f"✓ Server-initiated close: from={from_addr}, to={to_addr}")

def test_simultaneous_close():
    """Test both sides can close independently (SPEC §6)"""
    print("\nTEST: Both directions can close independently")

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

        # Send data both ways
        client.send(b"Client->Server")
        server_conn.recv(1024)

        server_conn.send(b"Server->Client")
        client.recv(1024)

        # Close both ends (order doesn't matter for this test)
        client.close()
        server_conn.close()

        time.sleep(0.3)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Should have at least one close event
    # (Both directions might generate close events, or just one if simultaneous)
    close_events = [e for e in events if e.get('event') == 'close']
    assert len(close_events) >= 1, "At least one close event should be logged"

    print(f"✓ Close events logged: {len(close_events)} close event(s)")

def main():
    print("=" * 60)
    print("Testing Close Event Semantics")
    print("=" * 60)

    test_client_initiated_close()
    test_server_initiated_close()
    test_simultaneous_close()

    print("\n" + "=" * 60)
    print("✓ All close semantics tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
