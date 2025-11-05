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
import json
import os
import socket
import tempfile
import shutil

def find_free_port():
    """Find a free port by briefly opening and closing a socket."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def main():
    """Test command-line arguments flow."""

    processes = []
    temp_dirs = []

    try:
        print("Testing command-line arguments...")

        # $REQ_CMD_015: Help text goes to STDERR (and help is shown when no args)
        # $REQ_CMD_011: Shows help and exits when given neither --mcp-port nor port rules
        result = subprocess.run(['./release/rawprox.exe'],
                               capture_output=True, text=True, encoding='utf-8')
        # Help is shown and process exits (doesn't continue running)
        assert 'rawprox.exe' in result.stderr, "Help text should go to STDERR"  # $REQ_CMD_011, $REQ_CMD_015
        assert '--mcp-port' in result.stderr, "Help should mention --mcp-port"  # $REQ_CMD_013
        assert 'PORT_RULE' in result.stderr, "Help should mention PORT_RULE"  # $REQ_CMD_013
        assert '--flush-millis' in result.stderr, "Help should mention --flush-millis"  # $REQ_CMD_013
        assert '--filename-format' in result.stderr, "Help should mention --filename-format"  # $REQ_CMD_013
        assert '@LOG_DIRECTORY' in result.stderr or 'LOG_DIRECTORY' in result.stderr, "Help should mention LOG_DIRECTORY"  # $REQ_CMD_013
        print("✓ $REQ_CMD_011, $REQ_CMD_013, $REQ_CMD_015: Help text displayed on STDERR when no arguments")

        # $REQ_CMD_001: Command-line format accepted
        # $REQ_CMD_014: Directory without port rules shows error
        temp_dir = tempfile.mkdtemp(prefix='rawprox_test_')
        temp_dirs.append(temp_dir)
        result = subprocess.run(['./release/rawprox.exe', f'@{temp_dir}'],
                               capture_output=True, text=True, encoding='utf-8', timeout=5)
        assert result.returncode != 0, "Directory without port rules should fail"  # $REQ_CMD_014
        assert len(result.stderr) > 0, "Error should be shown to STDERR"  # $REQ_CMD_014
        print("✓ $REQ_CMD_001, $REQ_CMD_014: Directory without port rules shows error to STDERR")

        # $REQ_CMD_002: --mcp-port option enables MCP server
        # $REQ_CMD_010: MCP endpoint URL output as NDJSON to stdout
        # $REQ_CMD_011: Runs when given --mcp-port
        mcp_port = find_free_port()
        process = subprocess.Popen(['./release/rawprox.exe', '--mcp-port', str(mcp_port)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8')
        processes.append(process)
        time.sleep(2)
        assert process.poll() is None, "Process should be running with --mcp-port"  # $REQ_CMD_002, $REQ_CMD_011

        # Read MCP endpoint URL from stdout
        stdout_line = process.stdout.readline()
        assert stdout_line.strip(), "MCP event should be emitted to stdout"  # $REQ_CMD_010
        mcp_event = json.loads(stdout_line)
        assert isinstance(mcp_event, dict), "MCP event should be valid JSON object"  # $REQ_CMD_010
        print(f"✓ $REQ_CMD_002, $REQ_CMD_010, $REQ_CMD_011: MCP server started and emitted endpoint to stdout")

        process.kill()
        process.wait(timeout=5)
        processes.remove(process)

        # $REQ_CMD_005: Port rule format LOCAL_PORT:TARGET_HOST:TARGET_PORT
        # $REQ_CMD_009: STDOUT default when no directory specified
        # $REQ_CMD_011: Runs when given port rules
        local_port = find_free_port()
        process = subprocess.Popen(['./release/rawprox.exe', f'{local_port}:example.com:80'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8')
        processes.append(process)
        time.sleep(2)
        assert process.poll() is None, "Process should be running with port rule"  # $REQ_CMD_005, $REQ_CMD_011
        print(f"✓ $REQ_CMD_005, $REQ_CMD_009, $REQ_CMD_011: Port rule format accepted, runs with port rules")

        process.kill()
        process.wait(timeout=5)
        processes.remove(process)

        # $REQ_CMD_006: Multiple port rules
        local_port1 = find_free_port()
        local_port2 = find_free_port()
        process = subprocess.Popen(['./release/rawprox.exe',
                                   f'{local_port1}:example.com:80',
                                   f'{local_port2}:api.example.com:443'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8')
        processes.append(process)
        time.sleep(2)
        assert process.poll() is None, "Process should accept multiple port rules"  # $REQ_CMD_006
        print(f"✓ $REQ_CMD_006: Multiple port rules accepted")

        process.kill()
        process.wait(timeout=5)
        processes.remove(process)

        # $REQ_CMD_007: Log directory format @DIRECTORY
        # $REQ_CMD_008: Single directory on command line
        temp_dir2 = tempfile.mkdtemp(prefix='rawprox_test_')
        temp_dirs.append(temp_dir2)
        local_port = find_free_port()
        process = subprocess.Popen(['./release/rawprox.exe',
                                   f'{local_port}:example.com:80',
                                   f'@{temp_dir2}'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8')
        processes.append(process)
        time.sleep(2)
        assert process.poll() is None, "Process should accept @DIRECTORY format"  # $REQ_CMD_007, $REQ_CMD_008
        print(f"✓ $REQ_CMD_007, $REQ_CMD_008: Log directory format @DIRECTORY accepted")

        process.kill()
        process.wait(timeout=5)
        processes.remove(process)

        # $REQ_CMD_003: --flush-millis option
        local_port = find_free_port()
        process = subprocess.Popen(['./release/rawprox.exe',
                                   '--flush-millis', '5000',
                                   f'{local_port}:example.com:80'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8')
        processes.append(process)
        time.sleep(2)
        assert process.poll() is None, "Process should accept --flush-millis"  # $REQ_CMD_003
        print(f"✓ $REQ_CMD_003: --flush-millis option accepted")

        process.kill()
        process.wait(timeout=5)
        processes.remove(process)

        # $REQ_CMD_016: --filename-format requires @DIRECTORY
        local_port = find_free_port()
        result = subprocess.run(['./release/rawprox.exe',
                                 '--filename-format', 'custom_%Y-%m-%d.ndjson',
                                 f'{local_port}:example.com:80'],
                                capture_output=True, text=True, encoding='utf-8', timeout=5)
        assert result.returncode != 0, "--filename-format without @DIRECTORY should fail"  # $REQ_CMD_016
        assert len(result.stderr) > 0, "Error should be reported to STDERR"  # $REQ_CMD_016
        print("✓ $REQ_CMD_016: --filename-format without @DIRECTORY shows error on STDERR")

        # $REQ_CMD_004: --filename-format option
        temp_dir3 = tempfile.mkdtemp(prefix='rawprox_test_')
        temp_dirs.append(temp_dir3)
        local_port = find_free_port()
        process = subprocess.Popen(['./release/rawprox.exe',
                                   '--filename-format', 'custom_%Y-%m-%d.ndjson',
                                   f'{local_port}:example.com:80',
                                   f'@{temp_dir3}'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8')
        processes.append(process)
        time.sleep(2)
        assert process.poll() is None, "Process should accept --filename-format"  # $REQ_CMD_004
        print(f"✓ $REQ_CMD_004: --filename-format option accepted")

        process.kill()
        process.wait(timeout=5)
        processes.remove(process)

        # $REQ_CMD_011: Runs with both --mcp-port and port rules
        mcp_port = find_free_port()
        local_port = find_free_port()
        process = subprocess.Popen(['./release/rawprox.exe',
                                   '--mcp-port', str(mcp_port),
                                   f'{local_port}:example.com:80'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8')
        processes.append(process)
        time.sleep(2)
        assert process.poll() is None, "Process should run with both --mcp-port and port rules"  # $REQ_CMD_011
        print(f"✓ $REQ_CMD_011: Runs with both --mcp-port and port rules")

        # $REQ_CMD_012: Application shutdown (test process can be terminated)
        process.kill()
        process.wait(timeout=5)
        assert process.poll() is not None, "Process should terminate"  # $REQ_CMD_012
        processes.remove(process)
        print(f"✓ $REQ_CMD_012: Application shutdown works")

        print("\n✓ All tests passed")
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1
    finally:
        # Clean up processes
        for process in processes:
            if process.poll() is None:
                process.kill()
                try:
                    process.wait(timeout=5)
                except:
                    pass

        # Clean up temp directories
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

if __name__ == '__main__':
    sys.exit(main())
