#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

DEFAULT_AGENT = "claude"

"""
Wrapper for agentic coder - delegates to the configured agent CLI.

Usage:
    echo "your prompt here" | prompt-agentic-coder.py

Or from Python:
    import prompt_agentic_coder
    result = prompt_agentic_coder.get_ai_response_text(prompt_text, report_type="my_task")
"""

import os
import sys
import json
import subprocess
import argparse
import threading
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SUPPORTED_AGENTS = {"codex", "claude"}


def _process_codex_output(raw_stdout):
    final_agent_message = None

    for line in raw_stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
            if event.get("type") == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    final_agent_message = item.get("text", "")
        except json.JSONDecodeError:
            continue

    if final_agent_message is None:
        final_agent_message = raw_stdout.strip()

    return final_agent_message


def _process_claude_output(raw_stdout):
    stripped = raw_stdout.strip()

    if not stripped:
        return ""

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped

    result_text = payload.get("result")
    if result_text is None:
        result_text = stripped

    return result_text


def get_ai_response_text(prompt_text: str, report_type: str = "prompt", timeout: int = 3600, agent: str = DEFAULT_AGENT) -> str:
    """
    Run a prompt by delegating to the configured agent CLI using JSON output.

    Args:
        prompt_text: The prompt to send to the agent
        report_type: Type of report for filename (e.g., "failing_test", "write_reqs")
        timeout: Maximum seconds to wait for the agent (default: 3600 = 1 hour)
        agent: Name of the agent CLI to use ("claude" or "codex")

    Returns:
        str: The AI's response text (NOT a subprocess.CompletedProcess object)
    """
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(f"Unsupported agent '{agent}'. Supported agents: {', '.join(sorted(SUPPORTED_AGENTS))}")

    # Create ./tmp directory if needed
    tmp_dir = Path("./tmp")
    tmp_dir.mkdir(exist_ok=True)

    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    prompt_file = tmp_dir / f"{timestamp}_prompt.md"

    print(f"DEBUG [prompt_agentic_coder]: Writing prompt to {prompt_file}", file=sys.stderr, flush=True)

    # Write prompt to file
    prompt_file.write_text(prompt_text, encoding='utf-8')

    # Build agent CLI command
    if agent == "codex":
        agent_cmd = [
            "codex", "exec", "-",
            "--json",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox"
        ]
        model_override = os.environ.get("PROMPT_AGENTIC_MODEL")
        if model_override:
            agent_cmd.extend(["--model", model_override])
    else:  # agent == "claude"
        agent_cmd = [
            "claude",
            "-",
            "--output-format=json",
            "--dangerously-skip-permissions"
        ]
        model_override = os.environ.get("PROMPT_AGENTIC_MODEL")
        agent_cmd.extend(["--model", model_override if model_override else "sonnet"])

    print(f"DEBUG [prompt_agentic_coder]: Launching {agent} CLI (timeout: {timeout}s)...", file=sys.stderr, flush=True)

    # Launch agent CLI and capture output
    try:
        # Internal subprocess result - NOT what this function returns!
        _subprocess_result = subprocess.run(
            agent_cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )

        raw_stdout = _subprocess_result.stdout or ""
        raw_stderr = _subprocess_result.stderr or ""

        final_agent_message = None

        if agent == "codex":
            final_agent_message = _process_codex_output(raw_stdout)
        else:
            final_agent_message = _process_claude_output(raw_stdout)

        ai_response = final_agent_message or ""

        if raw_stderr:
            ai_response += f"\n\n--- stderr ---\n{raw_stderr}"

        print(f"DEBUG [prompt_agentic_coder]: {agent} CLI completed (exit code: {_subprocess_result.returncode})", file=sys.stderr, flush=True)
        print(f"DEBUG [prompt_agentic_coder]: Final message length: {len(ai_response)} chars", file=sys.stderr, flush=True)

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

        if _subprocess_result.returncode != 0:
            raise RuntimeError(f"{agent} CLI exited with {_subprocess_result.returncode}")

        return ai_response  # Returns str, not subprocess result!

    except subprocess.TimeoutExpired:
        error_msg = f"Timeout: {agent} CLI did not complete within {timeout}s"
        print(f"ERROR [prompt_agentic_coder]: {error_msg}", file=sys.stderr, flush=True)
        raise TimeoutError(error_msg)
    except Exception as e:
        error_msg = f"Error running {agent} CLI: {e}"
        print(f"ERROR [prompt_agentic_coder]: {error_msg}", file=sys.stderr, flush=True)
        raise

def test_worker(task_name, prompt, expected_answer, results, agent):
    """Worker thread for test mode"""
    try:
        print(f"[TEST] {task_name}: Submitting prompt...", file=sys.stderr, flush=True)
        result = get_ai_response_text(prompt, report_type=f"test_{task_name}", agent=agent)

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

def run_test_mode(agent):
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

    # Spawn worker threads (each will launch its own agent CLI process)
    for task_name, config in test_tasks.items():
        thread = threading.Thread(
            target=test_worker,
            args=(task_name, config["prompt"], config["expected"], results, agent),
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
    parser.add_argument(
        "--agent",
        choices=sorted(SUPPORTED_AGENTS),
        default=DEFAULT_AGENT,
        help="Agent CLI to use for prompts (default: claude)"
    )
    args = parser.parse_args()

    # Test mode: run concurrent tests and exit
    if args.test:
        run_test_mode(args.agent)
        return

    # Normal mode: read prompt from stdin, launch agent CLI, write result to stdout
    prompt = sys.stdin.read()

    if not prompt.strip():
        print("Error: No prompt provided on stdin", file=sys.stderr)
        sys.exit(1)

    # Execute via selected agent CLI
    try:
        result = get_ai_response_text(prompt, report_type="stdin_prompt", agent=args.agent)
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
