#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
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
import threading
import re
from urllib.parse import unquote_to_bytes

def main():
    """
    Tests that every byte from 0 to 255 is correctly escaped in traffic data events.
    """

    def get_expected_encodings_list():
        """
        Generates a list of expected escaped strings, one for each byte from 0 to 255.
        """
        parts = []
        for i in range(256):
            if i == 9: parts.append('\t')
            elif i == 10: parts.append('\n')
            elif i == 13: parts.append('\r')
            elif i == 34: parts.append('"')
            elif i == 92: parts.append('\\')
            elif i == 37: parts.append('%25')
            elif 32 <= i <= 126:
                parts.append(chr(i))
            else:
                parts.append(f'%{i:02X}')
        return parts

    def parse_escaped_string(s: str):
        """
        Parses the URL-encoded string from the 'data' field into a list of tokens.
        e.g., "A%01B" -> ['A', '%01', 'B']
        """
        tokens = []
        i = 0
        while i < len(s):
            char = s[i]
            if char == '%':
                if i + 2 < len(s):
                    tokens.append(s[i:i+3])
                    i += 3
                else: # Malformed % at the end
                    tokens.append(s[i:])
                    i = len(s)
            else:
                tokens.append(char)
                i += 1
        return tokens

    all_bytes_payload = bytes(range(256))
    target_port = 19979
    proxy_port = 19978

    target_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    target_server.bind(('localhost', target_port))
    target_server.listen(1)

    def target_handler():
        """Sends the payload of all 256 bytes."""
        try:
            conn, addr = target_server.accept()
            conn.recv(1024)
            conn.sendall(all_bytes_payload)
            conn.close()
        except socket.error:
            pass
        except Exception as e:
            print(f"Target server error: {e}", file=sys.stderr)

    target_thread = threading.Thread(target=target_handler, daemon=True)
    target_thread.start()
    time.sleep(0.2)

    process = None
    try:
        process = subprocess.Popen(
            ['./release/rawprox.exe', f'{proxy_port}:localhost:{target_port}', '--flush-millis', '200'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        time.sleep(1)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        received_data = b''
        try:
            client.connect(('localhost', proxy_port))
            client.sendall(b'send payload')
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                received_data += chunk
        finally:
            client.close()

        time.sleep(0.5)

    finally:
        if process and process.poll() is None:
            process.kill()
        target_server.close()

    assert received_data == all_bytes_payload, "Client should receive the exact payload"

    stdout, stderr = process.communicate(timeout=5)
    if stderr:
        print(f"STDERR:\n{stderr}", file=sys.stderr)

    data_event_line = None
    data_field = None
    all_events = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            all_events.append(obj)
            if 'data' in obj and (f'localhost:{target_port}' in obj.get('from', '') or f'127.0.0.1:{target_port}' in obj.get('from', '')):
                data_event_line = line
                data_field = obj['data']
                break
        except json.JSONDecodeError:
            print(f"Warning: Could not parse line as JSON: {line}", file=sys.stderr)

    if data_field is None:
        print("Failed to find the data event from the target server.", file=sys.stderr)
        print("All captured events:", file=sys.stderr)
        for event in all_events:
            print(event, file=sys.stderr)
        assert False, "Could not find the traffic event with the test payload in stdout"

    restored_bytes = unquote_to_bytes(data_field)
    assert restored_bytes == all_bytes_payload, \
        f"Restored bytes do not match original payload.\nExpected: {all_bytes_payload.hex()}\nGot:      {restored_bytes.hex()}"

    unicode_escape_pattern = r'\\u[0-9a-fA-F]{4}'
    assert not re.search(unicode_escape_pattern, data_event_line), \
        f"Found forbidden Unicode escape sequence in NDJSON output: {data_event_line}"

    expected_tokens = get_expected_encodings_list()
    actual_tokens = parse_escaped_string(data_field)

    assert len(actual_tokens) == len(expected_tokens), \
        f"Mismatch in number of encoded tokens. Expected 256, got {len(actual_tokens)}."

    for i in range(256):
        expected = expected_tokens[i]
        actual = actual_tokens[i]
        assert actual == expected, \
            f"Encoding mismatch for byte {i} (0x{i:02X}).\nExpected: {repr(expected)}\nGot:      {repr(actual)}"

    print("✓ All byte escaping tests passed")
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"✗ Test failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)