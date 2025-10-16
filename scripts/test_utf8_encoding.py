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

def test_utf8_cafe():
    """Test UTF-8 multi-byte sequence: café → caf%C3%A9 (SPEC §5.2)"""
    print("TEST: UTF-8 encoding - café")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send UTF-8 encoded "café" (bytes: 0x63 0x61 0x66 0xC3 0xA9)
        client.send("café".encode('utf-8'))
        data = server_conn.recv(1024)
        assert data == "café".encode('utf-8'), "Data not forwarded correctly"

        # Close
        client.close()
        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find data entry with "café"
    data_entries = [e for e in events if 'data' in e]
    cafe_entry = None
    for entry in data_entries:
        if 'caf' in entry['data']:
            cafe_entry = entry
            break

    assert cafe_entry is not None, "No data entry containing 'caf' found"

    # SPEC §5.2: café (UTF-8: 0x63 0x61 0x66 0xC3 0xA9) → caf%C3%A9
    # 'c', 'a', 'f' are printable ASCII → preserved
    # 0xC3, 0xA9 are non-ASCII → percent-encoded
    expected = "caf%C3%A9"
    actual = cafe_entry['data']

    assert actual == expected, \
        f"UTF-8 encoding incorrect: expected '{expected}', got '{actual}'"

    print(f"✓ café encoded correctly: {actual}")

def test_utf8_emoji():
    """Test UTF-8 multi-byte sequence: emoji (4 bytes)"""
    print("\nTEST: UTF-8 encoding - emoji 🔥 (4-byte sequence)")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send emoji (UTF-8: 0xF0 0x9F 0x94 0xA5)
        emoji_bytes = "🔥".encode('utf-8')
        client.send(emoji_bytes)
        data = server_conn.recv(1024)
        assert data == emoji_bytes, "Data not forwarded correctly"

        # Close
        client.close()
        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find data entry
    data_entries = [e for e in events if 'data' in e]
    assert len(data_entries) > 0, "No data entries found"

    # All 4 bytes should be percent-encoded
    expected = "%F0%9F%94%A5"
    actual = data_entries[0]['data']

    assert actual == expected, \
        f"Emoji encoding incorrect: expected '{expected}', got '{actual}'"

    print(f"✓ Emoji encoded correctly: {actual}")

def test_utf8_chinese():
    """Test UTF-8 multi-byte sequence: Chinese characters"""
    print("\nTEST: UTF-8 encoding - Chinese 你好 (3-byte sequences)")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send Chinese characters (UTF-8: 你=0xE4 0xBD 0xA0, 好=0xE5 0xA5 0xBD)
        chinese_bytes = "你好".encode('utf-8')
        client.send(chinese_bytes)
        data = server_conn.recv(1024)
        assert data == chinese_bytes, "Data not forwarded correctly"

        # Close
        client.close()
        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find data entry
    data_entries = [e for e in events if 'data' in e]
    assert len(data_entries) > 0, "No data entries found"

    # All bytes should be percent-encoded
    expected = "%E4%BD%A0%E5%A5%BD"
    actual = data_entries[0]['data']

    assert actual == expected, \
        f"Chinese encoding incorrect: expected '{expected}', got '{actual}'"

    print(f"✓ Chinese characters encoded correctly: {actual}")

def test_utf8_mixed():
    """Test mixed ASCII and UTF-8: Hello 世界"""
    print("\nTEST: UTF-8 encoding - mixed ASCII and UTF-8")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send mixed content
        mixed_bytes = "Hello 世界".encode('utf-8')
        client.send(mixed_bytes)
        data = server_conn.recv(1024)
        assert data == mixed_bytes, "Data not forwarded correctly"

        # Close
        client.close()
        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find data entry
    data_entries = [e for e in events if 'data' in e and 'Hello' in e['data']]
    assert len(data_entries) > 0, "No data entry with 'Hello' found"

    # "Hello " is ASCII (preserved), "世界" is UTF-8 (percent-encoded)
    # 世 = 0xE4 0xB8 0x96, 界 = 0xE7 0x95 0x8C
    expected = "Hello %E4%B8%96%E7%95%8C"
    actual = data_entries[0]['data']

    assert actual == expected, \
        f"Mixed encoding incorrect: expected '{expected}', got '{actual}'"

    print(f"✓ Mixed ASCII/UTF-8 encoded correctly: {actual}")

def test_utf8_bom():
    """Test UTF-8 BOM (Byte Order Mark): 0xEF 0xBB 0xBF"""
    print("\nTEST: UTF-8 BOM encoding")

    project_root = Path(__file__).parent.parent
    binary = project_root / "release" / "rawprox.exe"

    local_port = find_free_port()
    target_port = find_free_port()

    # Start echo server
    echo_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    echo_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    echo_server.bind(('127.0.0.1', target_port))
    echo_server.listen(1)

    # Start proxy
    proxy = subprocess.Popen(
        [str(binary), f"{local_port}:127.0.0.1:{target_port}", "--flush-interval-ms=100"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.2)

    try:
        # Connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', local_port))

        # Accept on server
        server_conn, _ = echo_server.accept()

        # Send UTF-8 BOM
        bom_bytes = b'\xEF\xBB\xBF'
        client.send(bom_bytes)
        data = server_conn.recv(1024)
        assert data == bom_bytes, "Data not forwarded correctly"

        # Close
        client.close()
        server_conn.close()
        # Wait for flush cycle to complete (100ms interval + margin)
        time.sleep(0.25)

    finally:
        proxy.terminate()
        stdout, _ = proxy.communicate(timeout=2)
        echo_server.close()

    # Parse output
    lines = [line for line in stdout.strip().split('\n') if line]
    events = [json.loads(line) for line in lines]

    # Find data entry
    data_entries = [e for e in events if 'data' in e]
    assert len(data_entries) > 0, "No data entries found"

    # All bytes are non-ASCII → percent-encoded
    expected = "%EF%BB%BF"
    actual = data_entries[0]['data']

    assert actual == expected, \
        f"BOM encoding incorrect: expected '{expected}', got '{actual}'"

    print(f"✓ UTF-8 BOM encoded correctly: {actual}")

def main():
    print("=" * 60)
    print("Testing UTF-8 Multi-Byte Encoding")
    print("=" * 60)

    test_utf8_cafe()
    test_utf8_emoji()
    test_utf8_chinese()
    test_utf8_mixed()
    test_utf8_bom()

    print("\n" + "=" * 60)
    print("✓ All UTF-8 encoding tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
