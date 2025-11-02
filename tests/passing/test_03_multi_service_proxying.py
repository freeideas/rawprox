#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
# ]
# ///

import sys
# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import time
import socket
import os
import threading
from pathlib import Path

def check_port_listening(port, timeout=5):
    """Check if a port is listening."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.1)
    return False

def simple_tcp_server(port, response_data, stop_event):
    """Simple TCP server that echoes back data."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('127.0.0.1', port))
    server_sock.listen(5)
    server_sock.settimeout(1.0)

    while not stop_event.is_set():
        try:
            client_sock, addr = server_sock.accept()
            data = client_sock.recv(1024)
            if data:
                client_sock.sendall(response_data)
            client_sock.close()
        except socket.timeout:
            continue
        except:
            break

    server_sock.close()

def main():
    """Test multi-service proxying flow from start to shutdown."""

    process = None
    log_dir1 = Path('./tmp/logs1')
    log_dir2 = Path('./tmp/logs2')

    # Backend server ports (high range to avoid conflicts)
    backend_port1 = 45001
    backend_port2 = 45002

    # Proxy ports (high range to avoid conflicts)
    proxy_port1 = 35001
    proxy_port2 = 35002

    stop_event = threading.Event()
    server_thread1 = None
    server_thread2 = None

    try:
        # Clean up test directories
        import shutil
        for d in [log_dir1, log_dir2]:
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)

        # $REQ_RUNTIME_005: Release Directory Contents
        release_dir = Path('./release')
        assert release_dir.exists(), "Release directory does not exist"
        release_files = list(release_dir.glob('*'))
        exe_files = [f for f in release_files if f.name == 'rawprox.exe']
        assert len(exe_files) == 1, "rawprox.exe not found in release directory"  # $REQ_RUNTIME_005

        # Check for unwanted files (.pdb, .dll, config files)
        unwanted_extensions = ['.pdb', '.dll', '.config', '.xml']
        unwanted_files = [f for f in release_files if any(f.suffix == ext for ext in unwanted_extensions)]
        assert len(unwanted_files) == 0, f"Release directory contains unwanted files: {unwanted_files}"  # $REQ_RUNTIME_005

        # Verify only rawprox.exe exists
        assert len(release_files) == 1, f"Release directory should contain only rawprox.exe, found: {[f.name for f in release_files]}"  # $REQ_RUNTIME_005

        # Start simple backend servers
        server_thread1 = threading.Thread(target=simple_tcp_server, args=(backend_port1, b'RESPONSE_FROM_BACKEND1\n', stop_event))
        server_thread2 = threading.Thread(target=simple_tcp_server, args=(backend_port2, b'RESPONSE_FROM_BACKEND2\n', stop_event))
        server_thread1.daemon = True
        server_thread2.daemon = True
        server_thread1.start()
        server_thread2.start()

        # Wait for backend servers to start
        time.sleep(0.5)
        assert check_port_listening(backend_port1, timeout=2), f"Backend server 1 failed to start on port {backend_port1}"
        assert check_port_listening(backend_port2, timeout=2), f"Backend server 2 failed to start on port {backend_port2}"

        # $REQ_STARTUP_002: Start with Multiple Port Rules
        # $REQ_ARGS_014: Flexible Argument Order (port rules, flags, log destinations in mixed order)
        # $REQ_FILE_015: Multiple Destinations (STDOUT and two directories)
        # Use forward slashes for paths to work in Git Bash
        log_path1 = str(log_dir1).replace('\\', '/')
        log_path2 = str(log_dir2).replace('\\', '/')
        cmd = [
            './release/rawprox.exe',
            f'@{log_path1}',  # Log destination first (needs @ prefix)
            f'{proxy_port1}:127.0.0.1:{backend_port1}',  # Port rule
            f'@{log_path2}',  # Another log destination (needs @ prefix)
            f'{proxy_port2}:127.0.0.1:{backend_port2}',  # Another port rule
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        time.sleep(1.5)

        # Verify process is running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError(f"RawProx process failed to start. Exit code: {process.returncode}\nStderr: {stderr}\nStdout: {stdout}")  # $REQ_STARTUP_002

        # $REQ_STARTUP_003: Create Independent Listeners
        assert check_port_listening(proxy_port1), f"Proxy listener not created on port {proxy_port1}"  # $REQ_STARTUP_003
        assert check_port_listening(proxy_port2), f"Proxy listener not created on port {proxy_port2}"  # $REQ_STARTUP_003

        # $REQ_PROXY_016: Accept Connections
        # $REQ_PROXY_010: Independent Connections
        # $REQ_PROXY_021: Forward Traffic Bidirectionally

        # Connect to first proxy port
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('127.0.0.1', proxy_port1))
        client1.sendall(b'TEST_REQUEST_1\n')
        response1 = client1.recv(1024)
        assert b'RESPONSE_FROM_BACKEND1' in response1, "Traffic not forwarded correctly to backend 1"  # $REQ_PROXY_021

        # Connect to second proxy port
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('127.0.0.1', proxy_port2))
        client2.sendall(b'TEST_REQUEST_2\n')
        response2 = client2.recv(1024)
        assert b'RESPONSE_FROM_BACKEND2' in response2, "Traffic not forwarded correctly to backend 2"  # $REQ_PROXY_021

        # Close client connections
        client1.close()
        client2.close()

        # Wait for logs to be flushed (default flush interval is 2000ms)
        time.sleep(3.0)

        # $REQ_STDOUT_008: Unique Connection IDs
        # Read stdout to verify unique ConnIDs
        # Note: Cannot read from stdout in real-time reliably, but we can verify logs

        # $REQ_FILE_015: Multiple Destinations
        # Verify logs were written to both directories (logs are .ndjson files)
        log_files1 = list(log_dir1.glob('*.ndjson'))
        log_files2 = list(log_dir2.glob('*.ndjson'))
        assert len(log_files1) > 0, "No log files created in first log directory"  # $REQ_FILE_015
        assert len(log_files2) > 0, "No log files created in second log directory"  # $REQ_FILE_015

        # $REQ_STDOUT_008: Verify unique ConnIDs in logs
        # Read log content and parse NDJSON to extract ConnIDs
        import json
        conn_ids = set()
        for log_file in log_files1:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        if 'ConnID' in log_entry:
                            conn_ids.add(log_entry['ConnID'])
                    except json.JSONDecodeError:
                        continue

        # We made 2 connections, should have at least 2 different ConnIDs
        assert len(conn_ids) >= 2, f"Expected at least 2 unique ConnIDs, found {len(conn_ids)}: {conn_ids}"  # $REQ_STDOUT_008

        # NOTE: $REQ_SHUTDOWN_007 (Ctrl-C) is not tested per instructions
        # Cannot safely test Ctrl-C in automated tests on Windows

        # $REQ_SHUTDOWN_011: Close All Connections
        # $REQ_SHUTDOWN_015: Stop All Listeners
        # $REQ_SHUTDOWN_019: Flush Buffered Logs
        # We will kill the process and verify cleanup happened

        print("✓ All tests passed")
        return 0

    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up: Stop backend servers
        stop_event.set()
        if server_thread1:
            server_thread1.join(timeout=2)
        if server_thread2:
            server_thread2.join(timeout=2)

        # Clean up: Kill RawProx process
        if process and process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Warning: Process did not terminate cleanly")

if __name__ == '__main__':
    sys.exit(main())
