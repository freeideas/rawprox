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
import os
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

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
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)
    
    # Start target server in background thread
    target_thread = threading.Thread(target=run_target_server)
    target_thread.daemon = True
    target_thread.start()
    
    # Give target server time to start
    time.sleep(0.5)
    
    # Start rawprox proxy
    proxy_process = subprocess.Popen(
        [str(binary_path), f"{PROXY_PORT}:127.0.0.1:{TARGET_PORT}", "--flush-interval-ms=100"],
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
        
        # Verify we have the expected log entries (per SPECIFICATION.md v2.0)
        event_logs = [log for log in logs if 'event' in log]
        data_logs = [log for log in logs if 'data' in log]

        # Should have at least one 'open' and close events
        open_events = [log for log in event_logs if log.get('event') == 'open']
        close_events = [log for log in event_logs if log.get('event') == 'close']

        assert len(open_events) >= 1, f"Missing 'open' event. Events found: {[log.get('event') for log in event_logs]}"
        assert len(close_events) >= 1, f"Missing 'close' event. Events found: {[log.get('event') for log in event_logs]}"

        # Verify data transfer logs (using from/to addresses for direction)
        client_to_server = None
        server_to_client = None

        for log in data_logs:
            # Client->Server: to contains target port
            if f":{TARGET_PORT}" in log.get('to', ''):
                if client_to_server is None:
                    client_to_server = log.get('data', '')
            # Server->Client: from contains target port
            elif f":{TARGET_PORT}" in log.get('from', ''):
                if server_to_client is None:
                    server_to_client = log.get('data', '')

        assert client_to_server is not None, f"Missing client->server data log. Data logs: {data_logs}"
        assert server_to_client is not None, f"Missing server->client data log. Data logs: {data_logs}"

        # Verify the logged data matches what we sent/received
        # Data should use JSON escapes: \r\n in JSON becomes actual CR+LF after parsing
        assert 'GET /test HTTP/1.1' in client_to_server, f"Client data mismatch. Got: {client_to_server!r}"
        assert '\r\n' in client_to_server, f"Expected JSON-escaped CRLF in client data. Got: {client_to_server!r}"
        assert 'HTTP/1.1 200 OK' in server_to_client, f"Server data mismatch. Got: {server_to_client!r}"
        assert '\r\n' in server_to_client, f"Expected JSON-escaped CRLF in server data. Got: {server_to_client!r}"

        # Verify all logs have required fields per SPECIFICATION.md
        for i, log in enumerate(logs):
            assert 'time' in log, f"Log entry {i} missing 'time' field: {log}"
            assert 'ConnID' in log, f"Log entry {i} missing 'ConnID' field: {log}"
            assert 'from' in log, f"Log entry {i} missing 'from' field: {log}"
            assert 'to' in log, f"Log entry {i} missing 'to' field: {log}"

            # Each log should have either 'event' or 'data' (not both, not neither)
            has_event = 'event' in log
            has_data = 'data' in log
            assert has_event != has_data, f"Log entry {i} should have exactly one of 'event' or 'data': {log}"

            # Verify timestamp format (ISO 8601 with microsecond precision and Z suffix)
            time_str = log['time']
            assert time_str.endswith('Z'), f"Timestamp must end with 'Z': {time_str}"
            assert 'T' in time_str, f"Timestamp must use ISO 8601 format with 'T' separator: {time_str}"
            assert '.' in time_str, f"Timestamp must include microseconds: {time_str}"

            # Verify ConnID format (5-character base62)
            conn_id = log['ConnID']
            assert len(conn_id) == 5, f"ConnID must be 5 characters: {conn_id}"
            assert all(c in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' for c in conn_id), \
                f"ConnID must use base62 characters: {conn_id}"

            # Verify from/to format (should be address:port)
            assert ':' in log['from'], f"'from' field must be in address:port format: {log['from']}"
            assert ':' in log['to'], f"'to' field must be in address:port format: {log['to']}"
        
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