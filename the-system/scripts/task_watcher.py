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

def worker_thread(watch_dir, base_name, pending_path, original_filepath_str):
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
            "clco.bat",
            "--model", "sonnet",
            "-p",
            f"rename ./workQ/{pending_path.name} to ./workQ/{working_filename}, then follow the instructions in ./workQ/{working_filename}"
        ]

        print(f"[{base_name}] Executing clco.bat...", flush=True)

        # Create temp file for output (avoid pipe deadlock on Windows)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, suffix='.txt') as f:
            temp_output_file = f.name

        # Launch process with output redirected to file
        # Keep file handle open until process completes
        # Use line buffering (buffering=1) to ensure output is written immediately
        output_file = open(temp_output_file, 'w', encoding='utf-8', buffering=1)
        process = subprocess.Popen(
            clco_cmd,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1  # Line-buffered for subprocess
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

            # Close output file
            output_file.close()

            # Clean up temp file
            try:
                Path(temp_output_file).unlink()
            except:
                pass

            # Restore 0XP_foo.md back to T45K_foo.md for retry
            if pending_path.exists():
                task_path = watch_dir / f"T45K_{base_name}.md"
                pending_path.rename(task_path)
                print(f"[{base_name}] Restored {pending_path.name} -> {task_path.name} for retry", flush=True)

            print(f"[{base_name}] Thread exiting\n", flush=True)
            return

        # 0XW_foo.md appeared! Wait for process to complete (max 1 hour)
        print(f"[{base_name}] Waiting for clco.bat to finish (max 1 hour)...", flush=True)
        combined_output = ""
        try:
            returncode = process.wait(timeout=3600)  # 1 hour
            print(f"[{base_name}] Process completed normally (exit code: {returncode})", flush=True)
        except subprocess.TimeoutExpired:
            print(f"[{base_name}] Process exceeded 1 hour, killing...", flush=True)
            process.kill()
            process.wait()
            combined_output = "\n\n(killed after 1 hour)\n"
            print(f"[{base_name}] Process killed", flush=True)
        except Exception as e:
            print(f"[{base_name}] Exception during process.wait(): {e}", flush=True)
            try:
                process.kill()
                process.wait()
            except:
                pass
            combined_output = f"\n\n(exception during wait: {e})\n"
            print(f"[{base_name}] Process killed due to exception", flush=True)

        # Close output file now that process is done
        output_file.close()

        # Read output from temp file
        try:
            with open(temp_output_file, 'r', encoding='utf-8') as f:
                file_output = f.read()
            combined_output = file_output + combined_output
        except Exception as e:
            print(f"[{base_name}] Warning: Could not read temp output file: {e}", flush=True)

        # Clean up temp file
        try:
            Path(temp_output_file).unlink()
        except:
            pass

        # Check if output is empty -- if so, re-queue the task
        if not combined_output or not combined_output.strip():
            print(f"[{base_name}] Empty output detected, re-queueing task...", flush=True)

            # Rename 0XW_foo.md back to T45K_foo.md for retry
            if working_path.exists():
                task_path = watch_dir / f"T45K_{base_name}.md"
                working_path.rename(task_path)
                print(f"[{base_name}] Restored {working_filename} -> {task_path.name} for retry", flush=True)
            else:
                print(f"[{base_name}] Warning: {working_filename} not found, cannot re-queue", flush=True)

            print(f"[{base_name}] Thread exiting\n", flush=True)
            return

        # Write to report
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
        # Remove from processing set when done (using original T45K filepath)
        with processing_lock:
            processing.discard(original_filepath_str)

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

        # Spawn worker thread (pass original filepath string for cleanup)
        worker = threading.Thread(
            target=worker_thread,
            args=(watch_dir, base_name, pending_path, str(filepath)),
            daemon=True
        )
        worker.start()
        print(f"[*] Spawned worker thread for: {base_name}\n", flush=True)

    except Exception as e:
        print(f"[!] Error processing {filepath.name}: {e}", flush=True)
        with processing_lock:
            processing.discard(str(filepath))

def scan_and_prune(watch_dir, age_hours=2):
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
                print(f"[*] Archived: {filepath.name} -> archive/{new_name}", flush=True)
                continue

            # 3) None of the above? Keep looping (implicit)

        except Exception as e:
            print(f"[!] Error processing {filepath.name}: {e}", flush=True)

def test_monitor_thread(watch_dir, result_holder):
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
    failed = set()

    while time.time() - start_time < timeout:
        for task_name, config in test_tasks.items():
            if task_name in completed or task_name in failed:
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
                        failed.add(task_name)
                except Exception as e:
                    print(f"[TEST] ✗ {task_name}: Error reading report: {e}", flush=True)
                    failed.add(task_name)

        if len(completed) + len(failed) == len(test_tasks):
            if len(completed) == len(test_tasks):
                print(f"\n[TEST] ✓ All test tasks completed successfully!\n", flush=True)
                result_holder['success'] = True
                result_holder['reason'] = 'All test tasks passed'
            else:
                print(f"\n[TEST] ✗ Some test tasks failed: {', '.join(failed)}\n", flush=True)
                result_holder['success'] = False
                result_holder['reason'] = f'Test tasks failed: {", ".join(failed)}'
            return

        time.sleep(1)

    # Timeout
    missing = set(test_tasks.keys()) - completed - failed
    if missing:
        print(f"\n[TEST] ✗ Timeout: Tasks not completed: {', '.join(missing)}\n", flush=True)
        result_holder['success'] = False
        result_holder['reason'] = f'Timeout waiting for tasks: {", ".join(missing)}'
    else:
        if len(completed) == len(test_tasks):
            print(f"\n[TEST] ✓ All test tasks completed successfully!\n", flush=True)
            result_holder['success'] = True
            result_holder['reason'] = 'All test tasks passed'
        else:
            print(f"\n[TEST] ✗ Some test tasks failed: {', '.join(failed)}\n", flush=True)
            result_holder['success'] = False
            result_holder['reason'] = f'Test tasks failed: {", ".join(failed)}'

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
    test_result = None
    if args.test:
        result_holder = {}
        test_thread = threading.Thread(
            target=test_monitor_thread,
            args=(watch_dir, result_holder),
            daemon=False  # Not daemon - we need to wait for it
        )
        test_thread.start()
        print(f"[*] Test monitor thread started\n", flush=True)
        test_result = result_holder

    # Simple polling loop
    try:
        while True:
            # In test mode, check if test thread completed
            if args.test and test_result is not None and 'success' in test_result:
                # Test completed - exit with appropriate code
                print(f"[*] Test mode completed", flush=True)
                print(f"[*] Exit reason: {test_result['reason']}", flush=True)
                if test_result['success']:
                    print(f"\n{'=' * 60}", flush=True)
                    print(f"EXIT: SUCCESS - {test_result['reason']}", flush=True)
                    print(f"{'=' * 60}\n", flush=True)
                    sys.exit(0)
                else:
                    print(f"\n{'=' * 60}", flush=True)
                    print(f"EXIT: FAILURE - {test_result['reason']}", flush=True)
                    print(f"{'=' * 60}\n", flush=True)
                    sys.exit(1)

            # Scan directory for T45K files and archive old files
            for task_file in scan_and_prune(watch_dir):
                process_task_file(watch_dir, task_file)

            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{'=' * 60}", flush=True)
        print("[*] EXIT: User interrupted with Ctrl+C", flush=True)
        print(f"{'=' * 60}\n", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    main()
