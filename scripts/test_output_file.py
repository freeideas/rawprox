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

def test_output_to_file():
    """Test @FILEPATH writes output to file instead of stdout (SPEC §3.2.2, §4.1)"""
    print("TEST: Output to file with @FILEPATH argument")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    # Use tmp directory for test output
    output_file = project_root / "tmp" / "test_output.ndjson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Remove output file if it exists
    if output_file.exists():
        output_file.unlink()

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy with @FILEPATH argument
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", f"@{output_file}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))

        # Accept on echo server
        server_conn, _ = echo_server.accept()

        # Send data
        client.send(b"Hello File")
        data = server_conn.recv(1024)
        assert data == b"Hello File", "Data not forwarded correctly"

        # Close connections
        client.close()
        server_conn.close()

        time.sleep(0.3)

    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        echo_server.close()

    # Verify stdout is empty (output should go to file)
    stdout_output = proxy.stdout.read()
    assert stdout_output == "", f"Expected empty stdout, got: {stdout_output}"

    # Verify file exists and contains output
    assert output_file.exists(), f"Output file not created: {output_file}"

    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    assert len(lines) > 0, "Output file is empty"

    # Verify NDJSON format
    for line in lines:
        entry = json.loads(line)
        assert 'time' in entry, "Missing 'time' field"
        assert 'ConnID' in entry, "Missing 'ConnID' field"

    # Verify we have open, data, and close events
    events = [json.loads(line) for line in lines]
    assert any(e.get('event') == 'open' for e in events), "No 'open' event found"
    assert any('data' in e for e in events), "No data entries found"
    assert any(e.get('event') == 'close' for e in events), "No 'close' event found"

    print("✓ Output written to file instead of stdout")
    print(f"✓ File contains {len(lines)} NDJSON entries")

def test_append_mode():
    """Test @FILEPATH uses append mode (SPEC §3.2.2, §4.1)"""
    print("\nTEST: Append mode - multiple runs append to file")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    output_file = project_root / "tmp" / "test_append.ndjson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Remove output file if it exists
    if output_file.exists():
        output_file.unlink()

    local_port = find_free_port()
    target_port = find_free_port()

    # Run 1: First connection
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", f"@{output_file}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))
        server_conn, _ = echo_server.accept()
        client.send(b"First")
        server_conn.recv(1024)
        client.close()
        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)
    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        echo_server.close()

    # Count lines after first run
    with open(output_file, 'r', encoding='utf-8') as f:
        lines_after_run1 = len(f.readlines())

    assert lines_after_run1 > 0, "No output after first run"

    # Run 2: Second connection (should append)
    local_port = find_free_port()
    target_port = find_free_port()

    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", f"@{output_file}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))
        server_conn, _ = echo_server.accept()
        client.send(b"Second")
        server_conn.recv(1024)
        client.close()
        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)
    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        echo_server.close()

    # Count lines after second run
    with open(output_file, 'r', encoding='utf-8') as f:
        lines_after_run2 = len(f.readlines())

    assert lines_after_run2 > lines_after_run1, \
        f"File not appended: {lines_after_run1} lines before, {lines_after_run2} lines after"

    print(f"✓ Append mode works: {lines_after_run1} entries → {lines_after_run2} entries")

def test_multiple_at_arguments():
    """Test multiple @FILEPATH arguments - last one wins (SPEC §3.2.2)"""
    print("\nTEST: Multiple @ arguments - last one takes precedence")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    file1 = project_root / "tmp" / "test_multi_1.ndjson"
    file2 = project_root / "tmp" / "test_multi_2.ndjson"
    file1.parent.mkdir(parents=True, exist_ok=True)

    # Remove files if they exist
    if file1.exists():
        file1.unlink()
    if file2.exists():
        file2.unlink()

    local_port = find_free_port()
    target_port = find_free_port()

    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy with TWO @FILEPATH arguments (last should win)
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", f"@{file1}", f"@{file2}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))
        server_conn, _ = echo_server.accept()
        client.send(b"Multi")
        server_conn.recv(1024)
        client.close()
        server_conn.close()
        time.sleep(0.3)
    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        echo_server.close()

    # Verify file2 has output, file1 doesn't
    assert not file1.exists() or file1.stat().st_size == 0, \
        f"First @file should not be used, but has {file1.stat().st_size} bytes"

    assert file2.exists() and file2.stat().st_size > 0, \
        "Second @file should have output"

    print("✓ Last @ argument wins")

def test_at_argument_position_independence():
    """Test @ argument can appear at any position (SPEC §3.2.2)"""
    print("\nTEST: @ argument position independence")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    output_file = project_root / "tmp" / "test_position.ndjson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        output_file.unlink()

    local_port = find_free_port()
    target_port = find_free_port()

    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Put @ argument BEFORE port forwarding rule
    proxy = subprocess.Popen(
        [str(binary), f"@{output_file}", f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))
        server_conn, _ = echo_server.accept()
        client.send(b"Position")
        server_conn.recv(1024)
        client.close()
        server_conn.close()
        time.sleep(0.3)
    finally:
        proxy.terminate()
        proxy.wait(timeout=2)
        echo_server.close()

    # Verify file has output
    assert output_file.exists() and output_file.stat().st_size > 0, \
        "@ argument before port rule should still work"

    print("✓ @ argument works at any position")

def main():
    print("=" * 60)
    print("Testing @FILEPATH Output File Functionality")
    print("=" * 60)

    test_output_to_file()
    test_append_mode()
    test_multiple_at_arguments()
    test_at_argument_position_independence()

    print("\n" + "=" * 60)
    print("✓ All output file tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
