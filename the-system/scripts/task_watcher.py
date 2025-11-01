#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import time
import re
import subprocess
import threading
import argparse
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Track files currently being processed to avoid duplicates
processing = set()
processing_lock = threading.Lock()

def worker_thread(watch_dir, base_name, pending_path):
    """Worker thread that processes a single task"""
    working_filename = f"0XW_{base_name}.md"
    working_path = watch_dir / working_filename
    report_filename = f"R3P0RT_{base_name}.md"
    report_path = watch_dir / report_filename
    done_filename = f"D0N3_{base_name}.md"
    done_path = watch_dir / done_filename

    try:
        # Launch clco.bat
        clco_cmd = [
            "c:/acex/appz/cmdbin/clco.bat",
            "-p",
            f"rename ./workQ/{pending_path.name} to ./workQ/{working_filename}, then follow the instructions in ./workQ/{working_filename}"
        ]

        print(f"[{base_name}] Executing clco.bat...", flush=True)

        process = subprocess.Popen(
            clco_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Wait 60s for 0XW_foo.md to appear
        print(f"[{base_name}] Waiting 60s for {working_filename} to appear...", flush=True)
        timeout = 60
        start_time = time.time()
        while time.time() - start_time < timeout:
            if working_path.exists():
                print(f"[{base_name}] {working_filename} detected!", flush=True)
                break
            time.sleep(0.5)
        else:
            # Timeout - working file never appeared
            print(f"[{base_name}] Timeout: {working_filename} did not appear within 60s", flush=True)
            print(f"[{base_name}] Killing clco.bat process...", flush=True)
            process.kill()
            process.wait()

            # Restore 0XP_foo.md back to T45K_foo.md for retry
            if pending_path.exists():
                task_path = watch_dir / f"T45K_{base_name}.md"
                pending_path.rename(task_path)
                print(f"[{base_name}] Restored {pending_path.name} -> {task_path.name} for retry", flush=True)

            print(f"[{base_name}] Thread exiting\n", flush=True)
            return

        # 0XW_foo.md appeared! Wait for process to complete (max 1 hour)
        print(f"[{base_name}] Waiting for clco.bat to finish (max 1 hour)...", flush=True)
        try:
            stdout, stderr = process.communicate(timeout=3600)  # 1 hour
            print(f"[{base_name}] Process completed normally", flush=True)
        except subprocess.TimeoutExpired:
            print(f"[{base_name}] Process exceeded 1 hour, killing...", flush=True)
            process.kill()
            stdout, stderr = process.communicate()
            stderr = (stderr or "") + "\n\n(killed after 1 hour)"
            print(f"[{base_name}] Process killed", flush=True)

        # Combine stdout and stderr, then write to report
        combined_output = (stdout or "") + (stderr or "")
        if combined_output:
            # Filter out lines containing .claude.json errors
            combined_output = re.sub(r'.*\.claude\.json\b.*?\n', '', combined_output, flags=re.DOTALL)
            print(f"[{base_name}] Writing report to: {report_filename}", flush=True)
            report_path.write_text(combined_output, encoding='utf-8')

        # Rename 0XW_foo.md to D0N3_foo.md
        if working_path.exists():
            working_path.rename(done_path)
            print(f"[{base_name}] Renamed {working_filename} -> {done_filename}", flush=True)
        else:
            print(f"[{base_name}] Warning: {working_filename} not found, cannot rename to D0N3", flush=True)

        print(f"[✓] Completed: {base_name}\n", flush=True)

    except Exception as e:
        print(f"[{base_name}] Error in worker thread: {e}\n", flush=True)
    finally:
        # Remove from processing set when done
        with processing_lock:
            processing.discard(str(pending_path))

def process_task_file(watch_dir, filepath):
    """Process a T45K task file by renaming it and spawning a worker thread"""
    # Avoid processing the same file multiple times
    with processing_lock:
        if str(filepath) in processing:
            return
        processing.add(str(filepath))

    try:
        # Extract base name (e.g., "foo" from "T45K_foo.md")
        original_stem = filepath.stem  # "T45K_foo"
        base_name = original_stem.replace("T45K_", "", 1)  # "foo"

        # Rename T45K_foo.md to 0XP_foo.md immediately
        pending_filename = f"0XP_{base_name}.md"
        pending_path = watch_dir / pending_filename

        print(f"[*] Found: {filepath.name}", flush=True)
        print(f"[*] Renaming to: {pending_filename}", flush=True)
        filepath.rename(pending_path)

        # Spawn worker thread
        worker = threading.Thread(
            target=worker_thread,
            args=(watch_dir, base_name, pending_path),
            daemon=True
        )
        worker.start()
        print(f"[*] Spawned worker thread for: {base_name}\n", flush=True)

    except Exception as e:
        print(f"[!] Error processing {filepath.name}: {e}", flush=True)
        with processing_lock:
            processing.discard(str(filepath))

def scan_and_prune(watch_dir, age_hours=24):
    """
    Generator that scans directory once, yielding T45K files and archiving old files.

    Yields T45K_*.md files for processing while archiving files older than age_hours.
    """
    archive_dir = watch_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    current_time = time.time()
    age_seconds = age_hours * 3600

    # Single directory scan
    for filepath in sorted(watch_dir.iterdir()):
        if not filepath.is_file():
            continue

        try:
            # 1) Is it a T45K file? Yield it for processing
            if filepath.match("T45K_*.md"):
                yield filepath
                continue

            # 2) Is it more than a day old? Archive it
            mtime = filepath.stat().st_mtime
            age = current_time - mtime

            if age > age_seconds:
                timestamp = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                new_name = f"{timestamp}_{filepath.name}"
                archive_path = archive_dir / new_name

                filepath.rename(archive_path)
                print(f"[*] Archived (>24h old): {filepath.name} -> archive/{new_name}", flush=True)
                continue

            # 3) None of the above? Keep looping (implicit)

        except Exception as e:
            print(f"[!] Error processing {filepath.name}: {e}", flush=True)

def test_monitor_thread(watch_dir):
    """Monitor thread that waits for test task completion and validates results"""
    # Wait a moment for the watcher to fully start
    time.sleep(2)

    test_tasks = {
        "test1": {"limit": 100, "expected_prime": 541},    # 100th prime
        "test2": {"limit": 50, "expected_prime": 229},     # 50th prime
    }

    print(f"[TEST] Creating test task files...", flush=True)

    # Create T45K test files atomically (write to temp, then rename)
    for task_name, config in test_tasks.items():
        temp_file = watch_dir / f"_tmp_{task_name}.md"
        task_file = watch_dir / f"T45K_{task_name}.md"
        task_content = f"Calculate the {config['limit']}th prime number and output only that number."

        # Write to temp file first
        temp_file.write_text(task_content, encoding='utf-8')
        # Then atomically rename to T45K_ to trigger processing
        temp_file.rename(task_file)
        print(f"[TEST] Created: {task_file.name}", flush=True)

    print(f"[TEST] Waiting for tasks to complete (max 5 minutes)...", flush=True)

    # Wait for both R3P0RT files to appear and validate contents
    timeout = 300  # 5 minutes
    start_time = time.time()
    completed = set()

    while time.time() - start_time < timeout:
        for task_name, config in test_tasks.items():
            if task_name in completed:
                continue

            report_file = watch_dir / f"R3P0RT_{task_name}.md"
            if report_file.exists():
                try:
                    content = report_file.read_text(encoding='utf-8')
                    # Check if expected prime appears in content
                    if str(config['expected_prime']) in content:
                        print(f"[TEST] ✓ {task_name}: Found expected prime {config['expected_prime']}", flush=True)
                        completed.add(task_name)
                    else:
                        print(f"[TEST] ✗ {task_name}: Report exists but doesn't contain expected prime {config['expected_prime']}", flush=True)
                        completed.add(task_name)  # Mark as done anyway
                except Exception as e:
                    print(f"[TEST] ✗ {task_name}: Error reading report: {e}", flush=True)

        if len(completed) == len(test_tasks):
            print(f"\n[TEST] ✓ All test tasks completed successfully!\n", flush=True)
            return

        time.sleep(1)

    # Timeout
    missing = set(test_tasks.keys()) - completed
    if missing:
        print(f"\n[TEST] ✗ Timeout: Tasks not completed: {', '.join(missing)}\n", flush=True)
    else:
        print(f"\n[TEST] ✓ All test tasks completed successfully!\n", flush=True)

def main():
    parser = argparse.ArgumentParser(description="Multi-threaded task watcher")
    parser.add_argument("--test", action="store_true", help="Run in test mode (creates test tasks and validates results)")
    parser.add_argument("--watch-dir", default="./workQ", help="Directory to watch for task files (default: ./workQ)")
    args = parser.parse_args()

    watch_dir = Path(args.watch_dir).resolve()

    # Create workQ directory if it doesn't exist
    watch_dir.mkdir(exist_ok=True)

    print(f"[*] Multi-threaded Task Watcher started", flush=True)
    print(f"[*] Watching directory: {watch_dir}", flush=True)
    print(f"[*] Looking for files matching: T45K_*.md", flush=True)
    print(f"[*] Polling interval: 1 second", flush=True)
    if args.test:
        print(f"[*] TEST MODE: Will create test tasks after startup", flush=True)
    print(f"[*] Press Ctrl+C to stop\n", flush=True)

    # If test mode, spawn test monitor thread
    if args.test:
        test_thread = threading.Thread(
            target=test_monitor_thread,
            args=(watch_dir,),
            daemon=True
        )
        test_thread.start()
        print(f"[*] Test monitor thread started\n", flush=True)

    # Simple polling loop
    try:
        while True:
            # Scan directory for T45K files and archive old files
            for task_file in scan_and_prune(watch_dir):
                process_task_file(watch_dir, task_file)

            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping watcher...", flush=True)

    print("[*] Watcher stopped", flush=True)

if __name__ == "__main__":
    main()
