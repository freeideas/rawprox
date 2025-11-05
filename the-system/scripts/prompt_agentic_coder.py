#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Wrapper for agentic coder - launches clco.bat directly.

Usage:
    echo "your prompt here" | prompt-agentic-coder.py

Or from Python:
    import prompt_agentic_coder
    result = prompt_agentic_coder.run_prompt(prompt_text, report_type="my_task")
"""

import sys
import subprocess
import argparse
import threading
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def run_prompt(prompt_text, report_type="prompt", timeout=3600):
    """
    Run a prompt by launching clco.bat directly.

    Args:
        prompt_text: The prompt to send to clco.bat
        report_type: Type of report for filename (e.g., "failing_test", "write_reqs")
        timeout: Maximum seconds to wait for clco.bat (default: 3600 = 1 hour)

    Returns:
        String containing the AI response
    """
    # Create ./tmp directory if needed
    tmp_dir = Path("./tmp")
    tmp_dir.mkdir(exist_ok=True)

    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    prompt_file = tmp_dir / f"{timestamp}_prompt.md"

    print(f"DEBUG [prompt_agentic_coder]: Writing prompt to {prompt_file}", file=sys.stderr, flush=True)

    # Write prompt to file
    prompt_file.write_text(prompt_text, encoding='utf-8')

    # Build clco.bat command
    clco_cmd = [
        "clco.bat",
        "--model", "sonnet",
        "-p", f"follow the instructions in @{prompt_file}"
    ]

    print(f"DEBUG [prompt_agentic_coder]: Launching clco.bat (timeout: {timeout}s)...", file=sys.stderr, flush=True)

    # Launch clco.bat and capture output
    try:
        result = subprocess.run(
            clco_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )

        # Combine stdout and stderr
        ai_response = result.stdout
        if result.stderr:
            ai_response += f"\n\n--- stderr ---\n{result.stderr}"

        print(f"DEBUG [prompt_agentic_coder]: clco.bat completed (exit code: {result.returncode})", file=sys.stderr, flush=True)
        print(f"DEBUG [prompt_agentic_coder]: Output length: {len(ai_response)} chars", file=sys.stderr, flush=True)

        # Write structured report to ./reports/
        reports_dir = Path("./reports")
        reports_dir.mkdir(exist_ok=True)

        report_timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        final_report_path = reports_dir / f"{report_timestamp}_{report_type}.md"

        # Format report with prompt and response
        report_title = report_type.replace('_', ' ').title()
        structured_report = f"""# {report_title}
**Timestamp:** {report_timestamp}

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

    except subprocess.TimeoutExpired:
        error_msg = f"Timeout: clco.bat did not complete within {timeout}s"
        print(f"ERROR [prompt_agentic_coder]: {error_msg}", file=sys.stderr, flush=True)
        raise TimeoutError(error_msg)
    except Exception as e:
        error_msg = f"Error running clco.bat: {e}"
        print(f"ERROR [prompt_agentic_coder]: {error_msg}", file=sys.stderr, flush=True)
        raise

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

    # Spawn worker threads (each will launch its own clco.bat process)
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

    # Normal mode: read prompt from stdin, launch clco.bat, write result to stdout
    prompt = sys.stdin.read()

    if not prompt.strip():
        print("Error: No prompt provided on stdin", file=sys.stderr)
        sys.exit(1)

    # Execute via clco.bat
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
