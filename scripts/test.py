#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pytest",
# ]
# ///

import socket
import subprocess
import threading
import time
import json
import sys
from pathlib import Path

# Test configuration
PROXY_PORT = 18080
TARGET_PORT = 18081
TEST_MESSAGE = b"GET /test HTTP/1.1\r\nHost: localhost\r\n\r\n"
EXPECTED_RESPONSE = b"HTTP/1.1 200 OK\r\n\r\nTest passed"

def run_target_server():
    """Simple echo server that listens on TARGET_PORT"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', TARGET_PORT))
    server.listen(1)
    
    try:
        conn, addr = server.accept()
        data = conn.recv(4096)
        
        # Verify we received the test message
        assert data == TEST_MESSAGE, f"Target server received unexpected data: {data!r}"
        
        # Send response back
        conn.send(EXPECTED_RESPONSE)
        conn.close()
    finally:
        server.close()

def test_rawprox():
    # Find the rawprox binary
    binary_path = Path("target/release/rawprox")
    if not binary_path.exists():
        binary_path = Path("rawprox")
        if not binary_path.exists():
            print("ERROR: Could not find rawprox binary at target/release/rawprox or ./rawprox")
            sys.exit(1)
    
    # Start target server in background thread
    target_thread = threading.Thread(target=run_target_server)
    target_thread.daemon = True
    target_thread.start()
    
    # Give target server time to start
    time.sleep(0.5)
    
    # Start rawprox proxy
    proxy_process = subprocess.Popen(
        [str(binary_path), str(PROXY_PORT), "127.0.0.1", str(TARGET_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give proxy time to start
    time.sleep(0.5)
    
    try:
        # Connect to proxy and send test message
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', PROXY_PORT))
        client.send(TEST_MESSAGE)
        
        # Receive response through proxy
        response = client.recv(4096)
        client.close()
        
        # Verify response
        assert response == EXPECTED_RESPONSE, f"Client received unexpected response: {response!r}"
        
        # Give proxy time to log everything
        time.sleep(0.5)
        
        # Terminate proxy and get output
        proxy_process.terminate()
        stdout, stderr = proxy_process.communicate(timeout=2)
        
        # Parse and verify JSON logs
        logs = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except json.JSONDecodeError as e:
                    print(f"ERROR: Failed to parse JSON: {line}")
                    print(f"  Error: {e}")
                    sys.exit(1)
        
        # Verify we have the expected log entries
        log_types = [log.get('type') for log in logs if 'type' in log]
        assert 'local_open' in log_types, "Missing 'local_open' log entry"
        assert 'remote_open' in log_types, "Missing 'remote_open' log entry"
        assert 'local_close' in log_types, "Missing 'local_close' log entry"
        assert 'remote_close' in log_types, "Missing 'remote_close' log entry"
        
        # Verify data transfer logs
        outgoing_data = None
        incoming_data = None
        
        for log in logs:
            if log.get('direction') == '>':
                outgoing_data = log.get('data', '')
            elif log.get('direction') == '<':
                incoming_data = log.get('data', '')
        
        assert outgoing_data is not None, "Missing outgoing data log (direction: '>')"
        assert incoming_data is not None, "Missing incoming data log (direction: '<')"
        
        # Verify the logged data matches what we sent/received
        # Note: The data should be JSON-escaped in the logs (e.g., \r\n becomes \\r\\n)
        expected_outgoing = TEST_MESSAGE.decode('ascii', errors='replace').replace('\r', '\\r').replace('\n', '\\n')
        expected_incoming = EXPECTED_RESPONSE.decode('ascii', errors='replace').replace('\r', '\\r').replace('\n', '\\n')
        
        assert expected_outgoing in outgoing_data, f"Outgoing data mismatch. Expected substring: {expected_outgoing!r}, Got: {outgoing_data!r}"
        assert expected_incoming in incoming_data, f"Incoming data mismatch. Expected substring: {expected_incoming!r}, Got: {incoming_data!r}"
        
        # Verify all logs have required fields
        for log in logs:
            assert 'id' in log, f"Log entry missing 'id' field: {log}"
            assert 'stamp' in log, f"Log entry missing 'stamp' field: {log}"
            
            # Verify timestamp format (YYYY-MM-DD_HH:MM:SS.microseconds)
            stamp = log['stamp']
            assert '_' in stamp, f"Invalid timestamp format: {stamp}"
            date_part, time_part = stamp.split('_', 1)
            assert len(date_part.split('-')) == 3, f"Invalid date format in timestamp: {stamp}"
            assert '.' in time_part, f"Timestamp missing microseconds: {stamp}"
        
        print("✓ All tests passed!")
        print(f"  - Proxy forwarded data correctly")
        print(f"  - JSON logs are valid and complete")
        print(f"  - Log entries contain all required fields")
        print(f"  - Data was properly logged in both directions")
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        if stdout:
            print("\nProxy output:")
            print(stdout)
        if stderr:
            print("\nProxy errors:")
            print(stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Test error: {e}")
        if proxy_process.poll() is None:
            proxy_process.terminate()
        sys.exit(1)
    finally:
        # Ensure proxy is terminated
        if proxy_process.poll() is None:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
    
    # Wait for target thread to complete
    target_thread.join(timeout=2)

if __name__ == "__main__":
    test_rawprox()