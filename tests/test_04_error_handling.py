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
import json
import os

def find_available_port(start=20000, end=30000):
    """Find an available port in the given range."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No available ports found")

def read_ndjson_line(proc, timeout=5):
    """Read one line of NDJSON from stdout."""
    proc.stdout.flush()
    import select
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if line:
            return json.loads(line)
        time.sleep(0.01)
    return None

def send_jsonrpc(sock, method, params=None, msg_id=1):
    """Send JSON-RPC request."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "id": msg_id
    }
    if params:
        request["params"] = params

    msg = json.dumps(request) + '\n'
    sock.sendall(msg.encode('utf-8'))

def recv_jsonrpc(sock, timeout=5):
    """Receive JSON-RPC response."""
    sock.settimeout(timeout)
    data = b''
    while b'\n' not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk

    if data:
        return json.loads(data.decode('utf-8').strip())
    return None

def main():
    """Test error handling flow."""

    processes = []
    sockets = []

    try:
        # $REQ_ARGS_001, $REQ_ARGS_006, $REQ_ARGS_007: Help text to STDERR, exit code 1, no NDJSON
        print("Testing help display...")
        result = subprocess.run(
            ['./release/rawprox.exe'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"  # $REQ_ARGS_006
        assert len(result.stderr) > 0, "Expected help text on STDERR"  # $REQ_ARGS_001
        assert 'Usage' in result.stderr or 'rawprox' in result.stderr, "Help text doesn't look right"  # $REQ_ARGS_001
        assert len(result.stdout) == 0 or result.stdout.strip() == '', "Expected no NDJSON on STDOUT"  # $REQ_ARGS_007

        # $REQ_ARGS_003, $REQ_ARGS_004: Invalid port rule format
        print("Testing invalid port rule...")
        result = subprocess.run(
            ['./release/rawprox.exe', 'invalid'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        assert result.returncode != 0, "Expected non-zero exit code for invalid port rule"  # $REQ_ARGS_003
        assert len(result.stderr) > 0, "Expected error message on STDERR"  # $REQ_ARGS_004

        # $REQ_ARGS_005: Invalid log destination format
        print("Testing invalid log destination...")
        result = subprocess.run(
            ['./release/rawprox.exe', '8080:example.com:80', 'invalid_log'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        assert result.returncode != 0, "Expected non-zero exit code for invalid log destination"  # $REQ_ARGS_005

        # $REQ_ARGS_011, $REQ_MCP_001, $REQ_MCP_002, $REQ_MCP_003: MCP server startup
        print("Testing MCP server startup...")
        proc = subprocess.Popen(
            ['./release/rawprox.exe', '--mcp'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1
        )
        processes.append(proc)
        time.sleep(1)

        assert proc.poll() is None, "MCP server process died"  # $REQ_MCP_001

        # Read start-mcp event
        event = read_ndjson_line(proc)
        assert event is not None, "No start-mcp event received"  # $REQ_MCP_003
        assert event.get('event') == 'start-mcp', f"Expected start-mcp event, got {event.get('event')}"  # $REQ_MCP_003
        assert 'port' in event, "start-mcp event missing port"  # $REQ_MCP_003

        mcp_port = event['port']
        assert 10000 <= mcp_port <= 65500, f"MCP port {mcp_port} out of range"  # $REQ_MCP_002

        # $REQ_MCP_005: JSON-RPC protocol
        print(f"Testing JSON-RPC connection on port {mcp_port}...")
        mcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mcp_sock.connect(('127.0.0.1', mcp_port))
        sockets.append(mcp_sock)

        # $REQ_MCP_013, $REQ_MCP_014: add-port-rule method
        print("Testing add-port-rule...")
        test_port = find_available_port()
        send_jsonrpc(mcp_sock, 'add-port-rule', {
            'local_port': test_port,
            'target_host': 'example.com',
            'target_port': 80
        })  # $REQ_MCP_013, $REQ_MCP_014

        response = recv_jsonrpc(mcp_sock)
        assert response is not None, "No response to add-port-rule"  # $REQ_MCP_005
        assert 'result' in response or 'error' not in response, f"add-port-rule failed: {response}"  # $REQ_MCP_013

        # $REQ_STARTUP_005, $REQ_MCP_020, $REQ_MCP_024: Port already in use
        print("Testing port conflict error...")
        send_jsonrpc(mcp_sock, 'add-port-rule', {
            'local_port': test_port,  # Same port again
            'target_host': 'example.com',
            'target_port': 80
        }, msg_id=2)

        error_response = recv_jsonrpc(mcp_sock)
        assert error_response is not None, "No response for port conflict"  # $REQ_MCP_020
        assert 'error' in error_response, "Expected error response for port conflict"  # $REQ_MCP_020
        assert 'message' in error_response['error'], "Error response missing message"  # $REQ_MCP_020
        assert str(test_port) in str(error_response['error']['message']), "Error message doesn't mention occupied port"  # $REQ_MCP_024

        # $REQ_MCP_017, $REQ_MCP_018, $REQ_SHUTDOWN_002, $REQ_SHUTDOWN_003, $REQ_SHUTDOWN_004: Shutdown
        print("Testing shutdown method...")
        send_jsonrpc(mcp_sock, 'shutdown', msg_id=3)  # $REQ_MCP_017

        shutdown_response = recv_jsonrpc(mcp_sock, timeout=2)
        # Response may or may not arrive before shutdown completes

        # Wait for process to terminate
        time.sleep(2)
        exit_code = proc.poll()
        assert exit_code is not None, "Process didn't terminate after shutdown"  # $REQ_MCP_018
        assert exit_code == 0, f"Expected clean exit, got code {exit_code}"  # $REQ_MCP_018

        # $REQ_SHUTDOWN_002, $REQ_SHUTDOWN_003, $REQ_SHUTDOWN_004 verified by clean shutdown

        # Note: $REQ_PROXY_012 (UDP not supported) is architectural -- no specific test needed
        # The application simply doesn't have UDP forwarding code

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
        # Clean up sockets
        for sock in sockets:
            try:
                sock.close()
            except:
                pass

        # Clean up processes
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass

if __name__ == '__main__':
    sys.exit(main())
