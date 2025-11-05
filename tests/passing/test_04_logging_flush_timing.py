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
import os
import shutil
import socket
import glob

def main():
    """Test that log events appear in files only after flush intervals, not immediately."""

    process = None
    test_log_dir = "./tmp/test_flush_logs"

    try:
        # Clean up any existing test directory
        if os.path.exists(test_log_dir):
            shutil.rmtree(test_log_dir)

        # Create test log directory
        os.makedirs(test_log_dir, exist_ok=True)

        # Start RawProx with:
        # - A proxy port that forwards to a real destination (we'll use example.com:80)
        # - A log directory
        # - A flush interval of 3000ms (3 seconds) so we can observe the delay
        flush_interval_ms = 3000

        process = subprocess.Popen(
            ['./release/rawprox.exe',
             '8899:example.com:80',  # Proxy port 8899 to example.com:80
             f'@{test_log_dir}',
             '--flush-millis', str(flush_interval_ms)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1
        )

        # Wait for process to start
        time.sleep(0.5)
        assert process.poll() is None, "Process failed to start"

        # Generate a connection event by connecting to the proxy port
        # We don't need to send data, just open and close a connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('localhost', 8899))
            sock.close()
        except Exception as e:
            print(f"Note: Connection attempt resulted in: {e}")
            # Connection may fail (example.com unreachable, etc.) but that's ok -
            # RawProx should still log the connection attempt

        # $REQ_LOG_011: Events After Flush Only
        # Immediately after the connection, check that log files are empty or don't exist
        time.sleep(0.5)  # Brief pause to ensure event is buffered

        log_files = glob.glob(os.path.join(test_log_dir, '*.ndjson'))

        # Check that either no files exist, or if they do, they're empty
        immediate_file_size = 0
        if log_files:
            for log_file in log_files:
                immediate_file_size += os.path.getsize(log_file)

        assert immediate_file_size == 0, f"Log files contain data immediately after event (expected 0 bytes, got {immediate_file_size})"  # $REQ_LOG_011

        # Now wait for the flush interval to pass
        # Add a small buffer to ensure flush has completed
        time.sleep((flush_interval_ms / 1000.0) + 1.0)

        # After flush interval, check that log files now contain data
        log_files = glob.glob(os.path.join(test_log_dir, '*.ndjson'))

        assert len(log_files) > 0, "No log files created after flush interval"  # $REQ_LOG_011

        total_size = 0
        for log_file in log_files:
            total_size += os.path.getsize(log_file)

        assert total_size > 0, "Log files are empty after flush interval (expected connection events)"  # $REQ_LOG_011

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

        # Clean up test directory
        if os.path.exists(test_log_dir):
            shutil.rmtree(test_log_dir)

if __name__ == '__main__':
    sys.exit(main())
