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
import requests
import shutil

def main():
    """Test logging control flow with MCP server."""

    process = None
    test_log_dir = "./tmp/test_logs"
    test_log_dir2 = "./tmp/test_logs2"

    try:
        # Clean up any existing test directories
        if os.path.exists(test_log_dir):
            shutil.rmtree(test_log_dir)
        if os.path.exists(test_log_dir2):
            shutil.rmtree(test_log_dir2)

        # Single Executable
        # Start RawProx with MCP server enabled
        # $REQ_LOG_009: Flush Interval Configuration - Test that --flush-millis is accepted
        process = subprocess.Popen(
            ['./release/rawprox.exe', '--mcp-port', '0', '--flush-millis', '1000'],  # $REQ_LOG_009
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1
        )

        # MCP Ready Event
        # Wait for mcp-ready event
        mcp_endpoint = None
        for _ in range(50):  # 5 second timeout
            line = process.stdout.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    if event.get('event') == 'mcp-ready':
                        assert 'time' in event, "mcp-ready missing time field"
                        assert event['event'] == 'mcp-ready', "Wrong event type"
                        assert 'endpoint' in event, "mcp-ready missing endpoint"
                        mcp_endpoint = event['endpoint']
                        break
                except json.JSONDecodeError:
                    pass
            time.sleep(0.1)

        assert mcp_endpoint is not None, "MCP server did not emit mcp-ready event"
        assert process.poll() is None, "Process failed with --flush-millis argument"  # $REQ_LOG_009

        # Initialize MCP connection
        init_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 1,
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            }
        )
        assert init_response.status_code == 200, "MCP initialize failed"

        # $REQ_LOG_018: Start Logging Tool Arguments
        # $REQ_LOG_001: Start Logging Event
        # $REQ_LOG_016: Start Logging Event Filename Format
        # Start logging to directory
        start_log_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 2,
                "params": {
                    "name": "start-logging",
                    "arguments": {
                        "directory": test_log_dir,
                        "filename_format": "rawprox_%Y-%m-%d-%H.ndjson"
                    }
                }
            }
        )
        assert start_log_response.status_code == 200, "start-logging tool call failed"

        # Read stdout to find start-logging event
        start_logging_found = False
        for _ in range(50):  # 5 second timeout
            line = process.stdout.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    if event.get('event') == 'start-logging':
                        assert 'time' in event, "start-logging missing time field"  # $REQ_LOG_001
                        assert event['event'] == 'start-logging', "Wrong event type"  # $REQ_LOG_001
                        assert event['directory'] == test_log_dir, "Wrong directory in event"  # $REQ_LOG_001
                        assert event['filename_format'] == 'rawprox_%Y-%m-%d-%H.ndjson', "Missing or wrong filename_format"  # $REQ_LOG_016
                        start_logging_found = True
                        break
                except json.JSONDecodeError:
                    pass
            time.sleep(0.1)

        assert start_logging_found, "start-logging event not emitted"  # $REQ_LOG_001

        # $REQ_LOG_003: Directory Null for STDOUT
        # Start logging to STDOUT
        start_stdout_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 3,
                "params": {
                    "name": "start-logging",
                    "arguments": {
                        "directory": None
                    }
                }
            }
        )
        assert start_stdout_response.status_code == 200, "start-logging to STDOUT failed"

        # Read stdout to find start-logging event with directory: null
        stdout_logging_found = False
        for _ in range(50):
            line = process.stdout.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    if event.get('event') == 'start-logging' and event.get('directory') is None:
                        assert event['directory'] is None, "STDOUT logging should have directory: null"  # $REQ_LOG_003
                        assert 'filename_format' not in event, "STDOUT logging should not have filename_format"  # $REQ_LOG_016
                        stdout_logging_found = True
                        break
                except json.JSONDecodeError:
                    pass
            time.sleep(0.1)

        assert stdout_logging_found, "start-logging event for STDOUT not emitted"  # $REQ_LOG_003

        # $REQ_LOG_004: Multiple Log Destinations via MCP
        # Start logging to second directory
        start_log2_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 4,
                "params": {
                    "name": "start-logging",
                    "arguments": {
                        "directory": test_log_dir2
                    }
                }
            }
        )
        assert start_log2_response.status_code == 200, "start-logging to second directory failed"  # $REQ_LOG_004

        # $REQ_LOG_007: Stop Specific Directory Logging
        # $REQ_LOG_002: Stop Logging Event
        # $REQ_LOG_019: Stop Logging Tool Optional Directory
        # Stop logging to first directory
        stop_log_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 5,
                "params": {
                    "name": "stop-logging",
                    "arguments": {
                        "directory": test_log_dir
                    }
                }
            }
        )
        assert stop_log_response.status_code == 200, "stop-logging for directory failed"  # $REQ_LOG_007

        # Read stdout to find stop-logging event
        stop_logging_found = False
        for _ in range(50):
            line = process.stdout.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    if event.get('event') == 'stop-logging' and event.get('directory') == test_log_dir:
                        assert 'time' in event, "stop-logging missing time field"  # $REQ_LOG_002
                        assert event['event'] == 'stop-logging', "Wrong event type"  # $REQ_LOG_002
                        assert event['directory'] == test_log_dir, "Wrong directory in stop event"  # $REQ_LOG_002
                        stop_logging_found = True
                        break
                except json.JSONDecodeError:
                    pass
            time.sleep(0.1)

        assert stop_logging_found, "stop-logging event not emitted"  # $REQ_LOG_002

        # $REQ_LOG_006: Stop STDOUT Logging
        # Stop logging to STDOUT
        stop_stdout_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 6,
                "params": {
                    "name": "stop-logging",
                    "arguments": {
                        "directory": None
                    }
                }
            }
        )
        assert stop_stdout_response.status_code == 200, "stop-logging for STDOUT failed"  # $REQ_LOG_006

        # Read stdout to find stop-logging event for STDOUT
        stop_stdout_found = False
        for _ in range(50):
            line = process.stdout.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    if event.get('event') == 'stop-logging' and event.get('directory') is None:
                        assert event['directory'] is None, "STDOUT stop should have directory: null"  # $REQ_LOG_006
                        stop_stdout_found = True
                        break
                except json.JSONDecodeError:
                    pass
            time.sleep(0.1)

        assert stop_stdout_found, "stop-logging event for STDOUT not emitted"  # $REQ_LOG_006

        # $REQ_LOG_005: Stop All Logging
        # Stop all logging (directory argument omitted)
        stop_all_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 7,
                "params": {
                    "name": "stop-logging",
                    "arguments": {}
                }
            }
        )
        assert stop_all_response.status_code == 200, "stop-logging for all destinations failed"  # $REQ_LOG_005

        # Application Shutdown
        # Shutdown via MCP
        shutdown_response = requests.post(
            mcp_endpoint,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 8,
                "params": {
                    "name": "shutdown",
                    "arguments": {}
                }
            }
        )
        assert shutdown_response.status_code == 200, "shutdown tool call failed"

        # Wait for process to exit
        for _ in range(50):  # 5 second timeout
            if process.poll() is not None:
                break
            time.sleep(0.1)

        assert process.poll() is not None, "Process did not exit after shutdown"

        # $REQ_LOG_013: Batched File Writes (architectural requirement)
        # Verify implementation pattern: accumulate in buffer, flush at interval, open-write-close cycle
        print("Verifying architectural requirement $REQ_LOG_013...")
        prompt = """Follow instructions in @the-system/prompts/CODE_REVIEW_FOR_REQUIREMENT.md

Requirement: $REQ_LOG_013 - Batched File Writes

Source: ./readme/PERFORMANCE.md (Section: "Batched File I/O")

Requirement text: Files are written in batches: accumulate events in memory buffer, wait for flush interval, open file, write entire buffer, close file, clear buffer.

Check for:
1. Events are accumulated in a memory buffer (not written immediately)
2. Buffer flush happens at intervals (controlled by --flush-millis)
3. File open-write-close cycle happens during flush
4. Buffer is cleared after write
5. One buffer per destination file"""

        review_result = subprocess.run(
            ['uv', 'run', '--script', './the-system/scripts/prompt_agentic_coder.py'],
            input=prompt,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        assert review_result.returncode == 0, f"Code review process failed: {review_result.stderr}"  # $REQ_LOG_013
        assert 'VERDICT: PASS' in review_result.stdout, f"Architectural requirement not satisfied:\n{review_result.stdout}"  # $REQ_LOG_013

        # Note: Performance requirements ($REQ_LOG_008, $REQ_LOG_010, $REQ_LOG_012, $REQ_LOG_014, $REQ_LOG_015)
        # require architectural review as they specify implementation patterns.
        # $REQ_LOG_009 is tested above by verifying --flush-millis argument is accepted.
        # $REQ_LOG_013 is tested above via AI code review.

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
        # CRITICAL: Clean up
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)

        # Clean up test directories
        if os.path.exists(test_log_dir):
            shutil.rmtree(test_log_dir)
        if os.path.exists(test_log_dir2):
            shutil.rmtree(test_log_dir2)

if __name__ == '__main__':
    sys.exit(main())
