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
import socket
import json
import time
import os
import re
import threading
from pathlib import Path

def send_jsonrpc_request(host, port, method, params=None):
    """Send JSON-RPC 2.0 request over TCP."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    # MCP server expects line-delimited JSON (newline-terminated)
    sock.sendall((json.dumps(request) + '\n').encode('utf-8'))

    response_data = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response_data += chunk
        # Try to parse JSON
        try:
            response = json.loads(response_data.decode('utf-8'))
            sock.close()
            return response
        except json.JSONDecodeError:
            continue

    sock.close()
    return json.loads(response_data.decode('utf-8'))

def main():
    """Test MCP dynamic control flow."""

    process = None
    test_server = None

    try:
        # First, test $REQ_MCP_023: Start with --mcp AND port rules
        # Should start logging immediately and make MCP available
        process_with_rules = subprocess.Popen(
            ['./release/rawprox.exe', '--mcp', '45123:localhost:45124'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=0  # Unbuffered (bufsize=1 doesn't work reliably on Windows)
        )

        time.sleep(1)

        # $REQ_MCP_023: Should start logging immediately when --mcp has port rules
        line = process_with_rules.stdout.readline().strip()
        if not line:
            # Check if process crashed
            stderr_output = process_with_rules.stderr.read() if process_with_rules.poll() is not None else ""
            raise AssertionError(f"No output from process. Return code: {process_with_rules.poll()}, stderr: {stderr_output}")
        event = json.loads(line)
        assert event['event'] == 'start-logging', f"Should immediately start logging with port rules, got {event}"  # $REQ_MCP_023

        # Then should emit start-mcp event
        line = process_with_rules.stdout.readline().strip()
        if not line:
            stderr_output = process_with_rules.stderr.read() if process_with_rules.poll() is not None else ""
            raise AssertionError(f"No second line from process. Return code: {process_with_rules.poll()}, stderr: {stderr_output}")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Failed to parse JSON from second line: {repr(line)}, error: {e}")
        assert event.get('event') == 'start-mcp', f"Should emit start-mcp event, got event={event.get('event')}, full={event}"  # $REQ_MCP_023

        mcp_port_test = event['port']

        # Verify MCP server is available for dynamic control
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = test_sock.connect_ex(('localhost', mcp_port_test))
        test_sock.close()
        assert result == 0, "MCP server should be available with port rules"  # $REQ_MCP_023

        # Clean up this test process
        process_with_rules.kill()
        process_with_rules.wait(timeout=5)

        # Now run main test: $REQ_MCP_026, $REQ_ARGS_002: Start with --mcp flag, no port rules
        # Should NOT show usage message and should wait for MCP commands
        process = subprocess.Popen(
            ['./release/rawprox.exe', '--mcp'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=0  # Unbuffered (bufsize=1 doesn't work reliably on Windows)
        )

        time.sleep(0.5)

        # Process should still be running
        assert process.poll() is None, "Process should be running"  # $REQ_MCP_026

        # First, read the start-logging event (even without port rules, logging starts)
        line = process.stdout.readline().strip()
        if not line:
            stderr_data = process.stderr.read() if process.poll() is not None else ""
            raise AssertionError(f"Should emit start-logging event. poll={process.poll()}, stderr={stderr_data}")
        event = json.loads(line)
        assert event['event'] == 'start-logging', f"Should emit start-logging first, got {event}"

        # Then read the start-mcp event from STDOUT
        line = process.stdout.readline().strip()
        if not line:
            stderr_data = process.stderr.read() if process.poll() is not None else ""
            raise AssertionError(f"Should emit start-mcp event. poll={process.poll()}, stderr={stderr_data}")  # $REQ_MCP_028

        event = json.loads(line)
        assert event['event'] == 'start-mcp', f"Should emit start-mcp event, got {event}"  # $REQ_MCP_028
        assert 'time' in event, "start-mcp event must have timestamp"  # $REQ_MCP_004
        assert 'port' in event, "start-mcp event must have port"  # $REQ_MCP_004

        mcp_port = event['port']
        assert 10000 <= mcp_port <= 65500, "Port should be in range 10000-65500"  # $REQ_MCP_027

        # Verify MCP server is listening on localhost
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = test_sock.connect_ex(('localhost', mcp_port))
        test_sock.close()
        assert result == 0, "MCP server should be listening on localhost"  # $REQ_MCP_021

        # Test start-logging to STDOUT via JSON-RPC
        response = send_jsonrpc_request('localhost', mcp_port, 'start-logging', {
            'directory': None
        })
        assert 'result' in response, "Should return result"  # $REQ_MCP_006, $REQ_MCP_029, $REQ_MCP_022
        assert response['result'] == 'success', "Should return success"  # $REQ_MCP_019

        # Read start-logging event
        line = process.stdout.readline().strip()
        event = json.loads(line)
        assert event['event'] == 'start-logging', "Should emit start-logging event"  # $REQ_STDOUT_011
        assert event['directory'] is None, "Should have directory: null"  # $REQ_STDOUT_011
        assert 'filename_format' not in event, "Should not have filename_format for STDOUT"  # $REQ_STDOUT_011

        # Test add-port-rule via JSON-RPC
        # First, start a simple TCP echo server to forward to
        test_port = 54321

        def echo_server():
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('localhost', test_port))
            server_sock.listen(1)
            server_sock.settimeout(10)
            try:
                conn, addr = server_sock.accept()
                data = conn.recv(1024)
                conn.sendall(data)  # Echo back
                conn.close()
            except:
                pass
            finally:
                server_sock.close()

        test_thread = threading.Thread(target=echo_server, daemon=True)
        test_thread.start()
        time.sleep(0.2)

        # Add port rule
        local_port = 54322
        response = send_jsonrpc_request('localhost', mcp_port, 'add-port-rule', {
            'local_port': local_port,
            'target_host': 'localhost',
            'target_port': test_port
        })
        assert response['result'] == 'success', "Should add port rule"  # $REQ_MCP_030, $REQ_MCP_031

        time.sleep(0.2)

        # Test that proxy accepts connections and forwards traffic
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', local_port))  # $REQ_PROXY_015

        # Wait for open event
        line = process.stdout.readline().strip()
        event = json.loads(line)
        assert event['event'] == 'open', "Should emit open event"  # $REQ_STDOUT_014
        assert 'ConnID' in event, "Should have ConnID"  # $REQ_STDOUT_014
        assert 'time' in event, "Should have time"  # $REQ_STDOUT_014
        assert 'from' in event, "Should have from address"  # $REQ_STDOUT_014
        assert 'to' in event, "Should have to address"  # $REQ_STDOUT_014

        conn_id = event['ConnID']

        # Send data through proxy
        test_data = b'Hello RawProx'
        client.sendall(test_data)

        # Read traffic event (client -> target)
        line = process.stdout.readline().strip()
        event = json.loads(line)
        # Traffic events have event: 'data' per LOG_FORMAT.md
        assert event.get('event') == 'data', "Should emit data event"  # $REQ_STDOUT_019
        assert event['ConnID'] == conn_id, "Should have same ConnID"  # $REQ_STDOUT_019
        assert 'time' in event, "Should have time"  # $REQ_STDOUT_019
        assert 'data' in event, "Should have data"  # $REQ_STDOUT_019
        assert 'from' in event, "Should have from address"  # $REQ_STDOUT_019
        assert 'to' in event, "Should have to address"  # $REQ_STDOUT_019

        # Receive echo back
        response_data = client.recv(1024)
        assert response_data == test_data, "Should forward data bidirectionally"  # $REQ_PROXY_020

        # Read traffic event (target -> client)
        line = process.stdout.readline().strip()
        event = json.loads(line)
        assert event.get('event') == 'data', "Should emit return traffic event"  # $REQ_STDOUT_019

        client.close()

        # Test start-logging to directory (before stopping STDOUT so we can see the event)
        log_dir = './tmp/mcp-test-logs'
        os.makedirs(log_dir, exist_ok=True)

        response = send_jsonrpc_request('localhost', mcp_port, 'start-logging', {
            'directory': log_dir,
            'filename_format': 'test-{timestamp}.jsonl'
        })
        assert response['result'] == 'success', "Should start directory logging"  # $REQ_MCP_007, $REQ_MCP_008

        # Read start-logging event for directory
        line = process.stdout.readline().strip()
        event = json.loads(line)
        assert event['event'] == 'start-logging', "Should emit start-logging event"  # $REQ_FILE_023
        assert event['directory'] == log_dir, "Should have directory path"  # $REQ_FILE_023
        assert event['filename_format'] == 'test-{timestamp}.jsonl', "Should have filename_format"  # $REQ_FILE_023

        time.sleep(0.2)

        # Test stop-logging specific directory
        response = send_jsonrpc_request('localhost', mcp_port, 'stop-logging', {
            'directory': log_dir
        })
        assert response['result'] == 'success', "Should stop directory logging"  # $REQ_MCP_012

        # Read stop-logging event for directory
        line = process.stdout.readline().strip()
        event = json.loads(line)
        assert event['event'] == 'stop-logging', "Should emit stop-logging event"  # $REQ_FILE_024
        assert event['directory'] == log_dir, "Should have directory path"  # $REQ_FILE_024

        # Test stop-logging to STDOUT
        response = send_jsonrpc_request('localhost', mcp_port, 'stop-logging', {
            'directory': None
        })
        assert response['result'] == 'success', "Should stop logging"  # $REQ_MCP_009, $REQ_MCP_011

        # Read stop-logging event for STDOUT
        line = process.stdout.readline().strip()
        event = json.loads(line)
        assert event['event'] == 'stop-logging', "Should emit stop-logging event"  # $REQ_STDOUT_012
        assert event['directory'] is None, "Should have directory: null"  # $REQ_STDOUT_012

        # Start logging again to both destinations to test stop-all
        response = send_jsonrpc_request('localhost', mcp_port, 'start-logging', {
            'directory': None
        })
        assert response['result'] == 'success', "Should restart STDOUT logging"  # $REQ_MCP_007
        line = process.stdout.readline().strip()  # Read start-logging event

        response = send_jsonrpc_request('localhost', mcp_port, 'start-logging', {
            'directory': log_dir,
            'filename_format': 'test2-{timestamp}.jsonl'
        })
        assert response['result'] == 'success', "Should restart directory logging"  # $REQ_MCP_007
        line = process.stdout.readline().strip()  # Read start-logging event

        # Test stop-logging with empty params (stop ALL destinations)
        response = send_jsonrpc_request('localhost', mcp_port, 'stop-logging', {})
        assert response['result'] == 'success', "Should stop all logging"  # $REQ_MCP_009, $REQ_MCP_010

        # Should receive two stop-logging events (one for each destination)
        events = []
        for _ in range(2):
            line = process.stdout.readline().strip()
            event = json.loads(line)
            assert event['event'] == 'stop-logging', "Should emit stop-logging events"  # $REQ_MCP_010
            events.append(event)

        # Verify we got events for both STDOUT and directory
        dirs = [e.get('directory') for e in events]
        assert None in dirs, "Should stop STDOUT logging"  # $REQ_MCP_010
        assert log_dir in dirs, "Should stop directory logging"  # $REQ_MCP_010

        # Test remove-port-rule
        response = send_jsonrpc_request('localhost', mcp_port, 'remove-port-rule', {
            'local_port': local_port
        })
        assert response['result'] == 'success', "Should remove port rule"  # $REQ_MCP_015, $REQ_MCP_016

        time.sleep(0.2)

        # Verify port is no longer accepting connections
        test_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_client.settimeout(1)
        try:
            test_client.connect(('localhost', local_port))
            test_client.close()
            assert False, "Port should not accept connections after removal"  # $REQ_MCP_025
        except (ConnectionRefusedError, socket.timeout):
            pass  # Expected -- port no longer listening  # $REQ_MCP_025

        # Test error response for invalid method
        response = send_jsonrpc_request('localhost', mcp_port, 'invalid-method', {})
        assert 'error' in response, "Should return error for invalid method"  # $REQ_MCP_034
        assert 'code' in response['error'], "Error should have code"  # $REQ_MCP_034
        assert 'message' in response['error'], "Error should have message"  # $REQ_MCP_034

        # Test shutdown via MCP
        response = send_jsonrpc_request('localhost', mcp_port, 'shutdown', {})
        assert response['result'] == 'success', "Should shutdown"  # $REQ_MCP_032, $REQ_SHUTDOWN_006

        # Process should terminate
        process.wait(timeout=5)
        assert process.returncode is not None, "Process should terminate on shutdown"  # $REQ_MCP_033

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
        # Clean up
        if 'process_with_rules' in locals() and process_with_rules and process_with_rules.poll() is None:
            process_with_rules.kill()
            process_with_rules.wait(timeout=5)

        if process and process.poll() is None:
            process.kill()
            process.wait(timeout=5)

        # Clean up test logs
        import shutil
        if os.path.exists('./tmp/mcp-test-logs'):
            shutil.rmtree('./tmp/mcp-test-logs')

if __name__ == '__main__':
    sys.exit(main())
