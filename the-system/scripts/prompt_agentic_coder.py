#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Wrapper for agentic coder - uses task_watcher.py workQ system.

This script creates tasks in the workQ with compact timestamp IDs and waits for results.
Task IDs are the last 8 base62 digits of microseconds since epoch.

Usage:
    echo "your prompt here" | prompt-agentic-coder.py

Or from Python:
    import prompt_agentic_coder
    result = prompt_agentic_coder.run_prompt(prompt_text)
"""

import sys
import os
import time
import argparse
import threading
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configuration
WORKQ_DIR = Path("./workQ")

def get_compact_timestamp():
    """Generate a compact timestamp using base62 encoding of microseconds since epoch.

    Returns the last 8 base62 digits for compactness.
    Guarantees uniqueness even in tight loops by incrementing if timestamp hasn't changed.
    """
    import time

    # Base62 alphabet: 0-9, a-z, A-Z
    BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Get microseconds since epoch
    microseconds = int(time.time() * 1_000_000)

    # Check if we've returned this timestamp before
    if hasattr(get_compact_timestamp, '_last_microseconds'):
        if microseconds <= get_compact_timestamp._last_microseconds:
            # Collision! Increment the last one
            microseconds = get_compact_timestamp._last_microseconds + 1

    # Save for next call
    get_compact_timestamp._last_microseconds = microseconds

    # Convert to base62
    if microseconds == 0:
        return "00000000"

    result = []
    temp = microseconds
    while temp > 0:
        result.append(BASE62[temp % 62])
        temp //= 62

    # Reverse to get correct order
    base62_str = ''.join(reversed(result))

    # Take last 8 digits
    return base62_str[-8:].rjust(8, '0')

def run_prompt(prompt_text, report_type, timeout=3600):
    """
    Submit a task to the workQ and wait for the result.

    Args:
        prompt_text: The prompt to send to the task watcher
        report_type: Type of report for filename (e.g., "failing_test", "write_reqs")
        timeout: Maximum seconds to wait for result (default: 3600 = 1 hour)

    Returns:
        String containing the AI response
    """
    # Handle @file references in the prompt
    import re

    def replace_file_ref(match):
        filepath = match.group(1)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"[Error reading {filepath}: {e}]"

    # Find all @filepath patterns and replace with file contents
    processed_prompt = re.sub(r'@([^\s]+)', replace_file_ref, prompt_text)

    # Ensure workQ directory exists
    WORKQ_DIR.mkdir(exist_ok=True)

    # Get compact timestamp for task ID
    task_id = get_compact_timestamp()

    temp_file = WORKQ_DIR / f"{task_id}.md"
    task_file = WORKQ_DIR / f"T45K_{task_id}.md"
    report_file = WORKQ_DIR / f"R3P0RT_{task_id}.md"

    print(f"DEBUG [prompt_agentic_coder]: Creating task: {task_file.name}", file=sys.stderr, flush=True)
    print(f"DEBUG [prompt_agentic_coder]: Processed prompt length: {len(processed_prompt)} chars", file=sys.stderr, flush=True)

    # Write to temp file first, then atomically rename to avoid race condition
    temp_file.write_text(processed_prompt, encoding='utf-8')
    temp_file.rename(task_file)

    # Wait for the report file to appear
    print(f"DEBUG [prompt_agentic_coder]: Waiting for {report_file.name}...", file=sys.stderr, flush=True)
    start_time = time.time()

    while True:
        if report_file.exists():
            # Report file appeared, read it
            ai_response = report_file.read_text(encoding='utf-8')
            print(f"DEBUG [prompt_agentic_coder]: Report received ({len(ai_response)} chars)", file=sys.stderr, flush=True)

            # Write structured report to ./reports/
            from datetime import datetime
            from pathlib import Path

            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            reports_dir = Path("./reports")
            reports_dir.mkdir(exist_ok=True)

            final_report_path = reports_dir / f"{timestamp}_{report_type}.md"

            # Format report with prompt and response
            report_title = report_type.replace('_', ' ').title()
            structured_report = f"""# {report_title}
**Timestamp:** {timestamp}

---

## Prompt

{prompt_text}

---

## Response

{ai_response}
"""

            final_report_path.write_text(structured_report, encoding='utf-8')
            print(f"DEBUG [prompt_agentic_coder]: Wrote report to {final_report_path}", file=sys.stderr, flush=True)

            return ai_response

        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout:
            error_msg = f"Timeout: Report file {report_file.name} did not appear within {timeout}s"
            print(f"ERROR [prompt_agentic_coder]: {error_msg}", file=sys.stderr, flush=True)
            raise TimeoutError(error_msg)

        # Sleep briefly before checking again
        time.sleep(0.5)

def test_worker(task_name, prompt, expected_answer, results):
    """Worker thread for test mode"""
    try:
        print(f"[TEST] {task_name}: Submitting prompt...", file=sys.stderr, flush=True)
        result = run_prompt(prompt, report_type=f"test_{task_name}")

        # Check if expected answer is in the result
        if str(expected_answer) in result:
            print(f"[TEST] {task_name}: ✓ Got expected answer: {expected_answer}", file=sys.stderr, flush=True)
            results[task_name] = True
        else:
            print(f"[TEST] {task_name}: ✗ Expected {expected_answer} not found in result", file=sys.stderr, flush=True)
            print(f"[TEST] {task_name}: Result was: {result[:200]}...", file=sys.stderr, flush=True)
            results[task_name] = False
    except Exception as e:
        print(f"[TEST] {task_name}: ✗ Error: {e}", file=sys.stderr, flush=True)
        results[task_name] = False

def run_test_mode():
    """Run test mode with two concurrent prime number tasks"""
    test_tasks = {
        "test1": {
            "prompt": "Calculate the 100th prime number and output only that number.",
            "expected": 541
        },
        "test2": {
            "prompt": "Calculate the 50th prime number and output only that number.",
            "expected": 229
        }
    }

    print("[TEST] Starting test mode with 2 concurrent tasks...", file=sys.stderr, flush=True)

    results = {}
    threads = []

    # Spawn worker threads
    for task_name, config in test_tasks.items():
        thread = threading.Thread(
            target=test_worker,
            args=(task_name, config["prompt"], config["expected"], results),
            daemon=False
        )
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check results
    all_passed = all(results.values())

    if all_passed:
        print("\n[TEST] ✓ All tests passed!", file=sys.stderr, flush=True)
        sys.exit(0)
    else:
        print("\n[TEST] ✗ Some tests failed", file=sys.stderr, flush=True)
        sys.exit(1)

def main():
    """Main entry point - handles both test mode and normal stdin mode."""
    parser = argparse.ArgumentParser(description="Agentic coder prompt wrapper")
    parser.add_argument("--test", action="store_true", help="Run in test mode with concurrent prime number tasks")
    args = parser.parse_args()

    # Test mode: run concurrent tests and exit
    if args.test:
        run_test_mode()
        return

    # Normal mode: read prompt from stdin, submit to workQ, write result to stdout
    prompt = sys.stdin.read()

    if not prompt.strip():
        print("Error: No prompt provided on stdin", file=sys.stderr)
        sys.exit(1)

    # Execute via workQ
    try:
        result = run_prompt(prompt, report_type="stdin_prompt")
        # Write output to stdout
        sys.stdout.write(result)
        sys.exit(0)
    except TimeoutError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
