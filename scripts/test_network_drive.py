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

def test_network_drive_with_default_interval():
    """Test output to Windows network drive using DEFAULT 2-second interval (LESSONS_LEARNED.md)

    This test verifies the fix for the Windows network drive bug where:
    - BufWriter + append mode caused silent data loss (0 bytes written)
    - Frequent flushes caused Error 87 on SMB/CIFS

    The fix uses 2-second minimum swap interval to avoid these issues.
    """
    print("=" * 60)
    print("Testing Network Drive Output (LESSONS_LEARNED.md)")
    print("=" * 60)
    print("\nThis test uses the DEFAULT 2-second flush interval.")
    print("Purpose: Verify Windows network drive bug is fixed.")
    print()

    try:
        print("Using DEFAULT flush interval (2 seconds per SPEC §8.1)")
        print()

        project_root = Path(__file__).parent.parent
        binary = project_root / "release" / "rawprox.exe"

        # Use network drive path
        output_file = Path("g:/my drive/tmp/rawprox_network_test.ndjson")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Remove output file if it exists
        if output_file.exists():
            output_file.unlink()

        local_port = find_free_port()
        target_port = find_free_port()

        print(f"Starting test on network drive: {output_file}")
        print(f"Proxy: localhost:{local_port} -> 127.0.0.1:{target_port}")

        # Start echo server
        echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        echo_server.bind(('127.0.0.1', target_port))
        echo_server.listen(1)

        # Start proxy WITHOUT specifying flush interval (test the default)
        proxy = subprocess.Popen(
            [str(binary), f"{local_port}:127.0.0.1:{target_port}", f"@{output_file}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        time.sleep(0.2)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', local_port))
            server_conn, _ = echo_server.accept()

            # Send data
            print("Sending test data...")
            client.send(b"Network Drive Test - Default 2s Interval")
            data = server_conn.recv(1024)
            assert data == b"Network Drive Test - Default 2s Interval", "Data not forwarded correctly"

            client.close()
            server_conn.close()

            # CRITICAL: Wait for 2-second buffer swap interval + margin
            print("Waiting 2.5 seconds for buffer swap (SPEC §8.1)...")
            time.sleep(2.5)

        finally:
            proxy.terminate()
            proxy.wait(timeout=2)
            echo_server.close()

        # Verify file exists and is NOT empty (this was the bug)
        assert output_file.exists(), f"Output file not created on network drive: {output_file}"

        file_size = output_file.stat().st_size
        assert file_size > 0, \
            f"Output file on network drive is EMPTY ({file_size} bytes) - LESSONS_LEARNED.md bug reproduced!"

        # Verify content is valid NDJSON
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) > 0, "No lines in network drive output file"

        # Parse all lines to verify valid JSON
        events = []
        for line in lines:
            entry = json.loads(line)  # Should not raise
            events.append(entry)

        # Verify we have expected events
        assert any(e.get('event') == 'open' for e in events), "No 'open' event found"
        assert any('data' in e for e in events), "No data entries found"
        assert any(e.get('event') == 'close' for e in events), "No 'close' event found"

        print(f"\n✓ Network drive output works correctly!")
        print(f"  File size: {file_size} bytes")
        print(f"  NDJSON entries: {len(lines)}")
        print(f"  Events: {sum(1 for e in events if 'event' in e)} events, {sum(1 for e in events if 'data' in e)} data entries")
        print()
        print("=" * 60)
        print("✓ LESSONS_LEARNED.md network drive bug is FIXED!")
        print("=" * 60)

    finally:
        pass

if __name__ == "__main__":
    test_network_drive_with_default_interval()
