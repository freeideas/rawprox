#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test that stdout redirection and @filespec produce identical output
Uses DEFAULT 2-second flush interval (appropriate for network drives)
"""

import sys
import subprocess
import socket
import json
import time
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

def send_test_traffic(local_port, target_port):
    """Send identical test traffic through proxy"""
    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))
        server_conn, _ = echo_server.accept()

        # Send test data
        test_data = b"Test traffic for comparison"
        client.send(test_data)
        received = server_conn.recv(1024)
        assert received == test_data, "Echo server didn't receive data correctly"

        # Close connections
        client.close()
        server_conn.close()

        # CRITICAL: Wait for 2-second buffer swap + margin
        print("  Waiting 2.5 seconds for buffer flush...")
        time.sleep(2.5)

    finally:
        echo_server.close()

def extract_data_payloads(entries):
    """Extract just the data payloads from log entries"""
    return [e.get('data') for e in entries if 'data' in e]

def extract_event_sequence(entries):
    """Extract the sequence of events (open/close)"""
    return [e.get('event') for e in entries if 'event' in e]

def test_stdout_vs_filespec():
    """Test that stdout redirect and @filespec produce identical output"""
    print("=" * 60)
    print("Testing STDOUT vs @filespec (DEFAULT 2s flush)")
    print("=" * 60)
    print()

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    # Output files
    stdout_file = project_root / "tmp" / "test_local_STDOUT.ndjson"
    filespec_file = project_root / "tmp" / "test_local.ndjson"
    stdout_file.parent.mkdir(parents=True, exist_ok=True)

    # Remove files if they exist
    if stdout_file.exists():
        stdout_file.unlink()
    if filespec_file.exists():
        filespec_file.unlink()

    # Test 1: STDOUT redirection
    print("Test 1: Using stdout redirect > file")
    print("-" * 60)

    local_port = find_free_port()
    target_port = find_free_port()

    print(f"  Starting proxy: localhost:{local_port} -> 127.0.0.1:{target_port}")
    print(f"  Output: stdout redirect to {stdout_file.name}")

    with open(stdout_file, 'w') as stdout_redirect:
        proxy = subprocess.Popen(
            [str(binary), f"{local_port}:127.0.0.1:{target_port}"],
            stdout=stdout_redirect,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            send_test_traffic(local_port, target_port)
        finally:
            proxy.terminate()
            proxy.wait(timeout=2)

    # Verify stdout file
    assert stdout_file.exists(), "STDOUT file not created"
    stdout_size = stdout_file.stat().st_size
    print(f"  ✓ STDOUT file created: {stdout_size} bytes")

    with open(stdout_file, 'r', encoding='utf-8') as f:
        stdout_lines = f.readlines()

    assert len(stdout_lines) > 0, "STDOUT file is empty"
    stdout_entries = [json.loads(line) for line in stdout_lines]
    print(f"  ✓ STDOUT entries: {len(stdout_entries)}")

    # Test 2: @filespec
    print()
    print("Test 2: Using @filespec")
    print("-" * 60)

    local_port = find_free_port()
    target_port = find_free_port()

    print(f"  Starting proxy: localhost:{local_port} -> 127.0.0.1:{target_port}")
    print(f"  Output: @{filespec_file.name}")

    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", f"@{filespec_file}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        send_test_traffic(local_port, target_port)
    finally:
        proxy.terminate()
        proxy.wait(timeout=2)

    # Verify @filespec file
    assert filespec_file.exists(), "@filespec file not created"
    filespec_size = filespec_file.stat().st_size
    print(f"  ✓ @filespec file created: {filespec_size} bytes")

    with open(filespec_file, 'r', encoding='utf-8') as f:
        filespec_lines = f.readlines()

    assert len(filespec_lines) > 0, "@filespec file is empty"
    filespec_entries = [json.loads(line) for line in filespec_lines]
    print(f"  ✓ @filespec entries: {len(filespec_entries)}")

    # Test 3: Compare outputs
    print()
    print("Test 3: Comparing outputs")
    print("-" * 60)

    # Compare number of entries
    assert len(stdout_entries) == len(filespec_entries), \
        f"Entry count mismatch: stdout={len(stdout_entries)}, @filespec={len(filespec_entries)}"
    print(f"  ✓ Same number of entries: {len(stdout_entries)}")

    # Compare event sequences
    stdout_events = extract_event_sequence(stdout_entries)
    filespec_events = extract_event_sequence(filespec_entries)
    assert stdout_events == filespec_events, \
        f"Event sequence mismatch: stdout={stdout_events}, @filespec={filespec_events}"
    print(f"  ✓ Same event sequence: {stdout_events}")

    # Compare data payloads
    stdout_data = extract_data_payloads(stdout_entries)
    filespec_data = extract_data_payloads(filespec_entries)
    assert stdout_data == filespec_data, \
        f"Data payload mismatch: stdout={stdout_data}, @filespec={filespec_data}"
    print(f"  ✓ Same data payloads: {len(stdout_data)} data entries")

    # Verify structure
    for entry in stdout_entries + filespec_entries:
        assert 'time' in entry, "Missing 'time' field"
        assert 'ConnID' in entry, "Missing 'ConnID' field"
        assert 'from' in entry, "Missing 'from' field"
        assert 'to' in entry, "Missing 'to' field"
        assert ('event' in entry) or ('data' in entry), "Missing 'event' or 'data' field"

    print(f"  ✓ All entries have correct structure")

    print()
    print("=" * 60)
    print("✓ STDOUT and @filespec produce identical output!")
    print("=" * 60)

if __name__ == "__main__":
    test_stdout_vs_filespec()
