#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Test streaming and chunking per SPECIFICATION.md §6 and §7
Tests that large messages (>32KB) are split into chunks and logged as transmitted
"""

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
PROXY_PORT = 25401
TARGET_PORT = 25402
CHUNK_SIZE = 32 * 1024  # 32KB per SPECIFICATION.md §6
LARGE_MESSAGE_SIZE = 100 * 1024  # 100KB

class EchoServer:
    """Echo server that handles large messages"""
    def __init__(self, port):
        self.port = port
        self.server = None
        self.running = False
        self.thread = None

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('127.0.0.1', self.port))
        self.server.listen(1)
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        while self.running:
            try:
                self.server.settimeout(0.5)
                conn, addr = self.server.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            # Receive large message
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                # Stop when we've received enough
                if len(data) >= LARGE_MESSAGE_SIZE:
                    break

            # Echo it back
            conn.sendall(data)
            time.sleep(0.2)
            conn.close()
        except:
            pass

    def stop(self):
        self.running = False
        if self.server:
            self.server.close()
        if self.thread:
            self.thread.join(timeout=2)

def main():
    print("=" * 60)
    print("Streaming/Chunking Test (SPECIFICATION.md §6, §7)")
    print("=" * 60)

    # Find the rawprox binary
    binary_path = Path("release/rawprox.exe")
    if not binary_path.exists():
        print("ERROR: Could not find rawprox binary at release/rawprox.exe")
        print("Run: uv run --script scripts/build.py")
        sys.exit(1)

    # Start echo server
    echo_server = EchoServer(TARGET_PORT)
    echo_server.start()
    time.sleep(0.5)

    # Start rawprox - capture output in background to avoid pipe buffer deadlock
    output_lines = []
    output_lock = threading.Lock()

    def read_output(pipe):
        """Read from pipe continuously to prevent buffer fill/deadlock"""
        try:
            for line in pipe:
                with output_lock:
                    output_lines.append(line)
        except:
            pass

    proxy_process = subprocess.Popen(
        [str(binary_path), f"{PROXY_PORT}:127.0.0.1:{TARGET_PORT}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Start thread to read stdout continuously
    stdout_thread = threading.Thread(target=read_output, args=(proxy_process.stdout,), daemon=True)
    stdout_thread.start()

    time.sleep(0.5)

    try:
        # Create a large message (100KB of repeating pattern)
        large_message = b"ABCDEFGHIJ" * (LARGE_MESSAGE_SIZE // 10)
        print(f"\nSending large message: {len(large_message):,} bytes")
        print(f"Expected chunking at: {CHUNK_SIZE:,} bytes per SPEC §6")

        # Send through proxy
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', PROXY_PORT))
        client.sendall(large_message)

        # Receive echo
        response = b""
        while len(response) < len(large_message):
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk

        client.close()

        # Verify echo worked
        assert response == large_message, "Echo failed for large message"
        print(f"  ✓ Large message echoed correctly")

        # Wait for logs to be written
        time.sleep(0.5)

        proxy_process.terminate()
        _, stderr = proxy_process.communicate(timeout=5)

        # Get captured output from background thread
        with output_lock:
            stdout = ''.join(output_lines)

        # Parse logs
        logs = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Failed to parse: {line}")
                    raise

        # Find data logs for this connection
        # Should have same ConnID for all chunks
        data_logs = [log for log in logs if 'data' in log]

        assert len(data_logs) > 0, "No data logs found"

        # Group by direction (client->server vs server->client)
        conn_id = data_logs[0]['ConnID']

        # Client to server (to contains TARGET_PORT)
        client_to_server_logs = [
            log for log in data_logs
            if log['ConnID'] == conn_id and f":{TARGET_PORT}" in log.get('to', '')
        ]

        # Server to client (from contains TARGET_PORT)
        server_to_client_logs = [
            log for log in data_logs
            if log['ConnID'] == conn_id and f":{TARGET_PORT}" in log.get('from', '')
        ]

        print(f"\nClient->Server: {len(client_to_server_logs)} data log(s)")
        print(f"Server->Client: {len(server_to_client_logs)} data log(s)")

        # Verify multiple chunks were logged (streaming, not buffered)
        # For 100KB message, we expect multiple log entries
        assert len(client_to_server_logs) >= 2, \
            f"Expected multiple chunks for {LARGE_MESSAGE_SIZE:,} byte message, got {len(client_to_server_logs)}"

        print(f"  ✓ Large message split into multiple log entries (streaming)")

        # Verify all chunks have same ConnID
        client_conn_ids = set(log['ConnID'] for log in client_to_server_logs)
        assert len(client_conn_ids) == 1, \
            f"All chunks should have same ConnID, got {client_conn_ids}"

        print(f"  ✓ All chunks have same ConnID: {conn_id}")

        # Reconstruct message from logs
        import urllib.parse
        reconstructed = ""
        for log in sorted(client_to_server_logs, key=lambda x: x['time']):
            reconstructed += log['data']

        # URL-decode the data (percent-encoding)
        # Need to handle JSON escaping first, then URL decode
        reconstructed_bytes = urllib.parse.unquote(reconstructed, encoding='latin1').encode('latin1')

        # Note: URL encoding doesn't change byte count for printable ASCII
        print(f"\nOriginal size: {len(large_message):,} bytes")
        print(f"Reconstructed size: {len(reconstructed_bytes):,} bytes")

        # They should match (accounting for URL encoding)
        assert len(reconstructed_bytes) == len(large_message), \
            "Reconstructed message size doesn't match original"

        print(f"  ✓ Message can be reconstructed from chunks")

        # Verify chunk sizes are reasonable (should be ~32KB per SPEC §6)
        print(f"\nChunk size analysis:")
        for i, log in enumerate(client_to_server_logs):
            # Each 'data' field contains encoded data
            # Count bytes in the original data (not encoded length)
            data_field = log['data']
            # Rough estimate: percent-encoded adds overhead
            # For printable ASCII (our test data), no percent-encoding
            # So data field length ~= original byte count
            print(f"  Chunk {i+1}: ~{len(data_field):,} bytes (encoded)")

        # For 100KB message, expect chunks close to 32KB
        # (Some variation is acceptable due to buffering)
        max_chunk = max(len(log['data']) for log in client_to_server_logs)
        print(f"  Largest chunk: {max_chunk:,} bytes")

        # Verify chunks are reasonably sized (not entire message in one chunk)
        assert max_chunk < len(large_message), \
            "All data should not be in a single chunk (streaming required)"

        print(f"  ✓ Data streamed in chunks (not buffered as single message)")

        print("\n" + "=" * 60)
        print("✓ Streaming/chunking test passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if proxy_process.poll() is None:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
        echo_server.stop()

if __name__ == "__main__":
    main()
