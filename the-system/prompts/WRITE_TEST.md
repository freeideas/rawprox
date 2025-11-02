# WRITE_TEST.md -- Write Test for Untested Requirement

Write tests for requirements that have no test coverage.

---

## Project Philosophy

**Follow @the-system/prompts/PHILOSOPHY.md:**
- Build only what is explicitly required in `/reqs/`
- No "nice to have" features
- No undocumented edge cases
- No error handling except where required
- Keep tests simple -- prefer duplication over abstraction
- Mock only what you must

---

## Test Structure

### One Flow = One Test File

```
./reqs/startup.md → ./tests/failing/test_startup.py
./reqs/api-basic.md → ./tests/failing/test_api_basic.py
```

**File naming:** Take flow filename, remove `.md`, replace `-` with `_`, prefix with `test_`, add `.py`, place in `./tests/failing/`

### Test File Template

**IMPORTANT: Do NOT use pytest. Write standalone Python scripts.**

```python
#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   # Add test dependencies (no pytest)
# ]
# ///

import sys
# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import time

def main():
    """Test the entire flow from start to shutdown."""

    try:
        # Execute flow steps -- verify each $REQ_ID with assertions

        # Example: Start app
        process = subprocess.Popen(['./release/app.exe'])
        time.sleep(1)
        assert process.poll() is None, "Process failed to start"  # $REQ_STARTUP_001

        # More assertions for each $REQ_ID...

        print("✓ All tests passed")
        return 0

    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return 1
    finally:
        # CRITICAL: Clean up -- kill processes, close connections
        # Use kill() not terminate/signals (Windows signals propagate to parent)
        if 'process' in locals() and process.poll() is None:
            process.kill()
            process.wait(timeout=5)

if __name__ == '__main__':
    sys.exit(main())
```

---

## Context: Use-Case Documentation

For broader context about what the application does and why:
- `./README.md` -- Project overview and architectural intent
- `./readme/*.md` -- Detailed use-case documentation

These documents explain the "why" behind requirements and provide user perspective. Refer to them when you need to understand the purpose and context of what you're testing.

---

## Instructions

### Step 1: Read the Flow File

You'll be given a $REQ_ID and its flow file. Read the entire flow to understand all requirements and their sequence.

### Step 2: Determine Test File Path

Check if test file exists:
- If `./tests/failing/test_FLOWNAME.py` exists: update it
- If not: create it

### Step 3: Write the Test

Create one test function that:
1. Executes flow from start to shutdown
2. Verifies each $REQ_ID with assertions
3. Tags each assertion with `# $REQ_ID`
4. Cleans up in `finally` block

**Critical:** Tests MUST NOT leave processes running or resources locked.

**Windows warning:** Always use `process.kill()` for cleanup. Never use `terminate()`, `send_signal()`, or `CTRL_C_EVENT` -- on Windows these propagate to the parent process and kill the test runner.

### Step 4: Tag Each Assertion

```python
assert condition, "message"  # $REQ_STARTUP_001
```

**Format:** `$REQ_` followed by any combination of letters, digits, underscores, hyphens

This enables traceability from requirements to tests.

---

## Example

**Flow: ./reqs/startup.md**
```markdown
## $REQ_STARTUP_001: Launch Process
Start the server executable.

## $REQ_STARTUP_002: Bind to Port
Server must bind to port 8080.

## $REQ_STARTUP_003: Health Check
GET /health returns 200 OK.
```

**Test: ./tests/failing/test_startup.py**
```python
def main():
    """Test server startup flow."""
    import socket
    import requests

    try:
        # Launch
        process = subprocess.Popen(['./release/server.exe'])
        time.sleep(1)
        assert process.poll() is None, "Process not running"  # $REQ_STARTUP_001

        # Port binding
        sock = socket.socket()
        result = sock.connect_ex(('localhost', 8080))
        assert result == 0, "Port not bound"  # $REQ_STARTUP_002
        sock.close()

        # Health check
        response = requests.get('http://localhost:8080/health')
        assert response.status_code == 200, "Health check failed"  # $REQ_STARTUP_003

        print("✓ All tests passed")
        return 0

    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return 1
    finally:
        if 'process' in locals() and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
```

---

## Architectural Requirements (Rare)

Some requirements specify **implementation patterns** rather than behavior:
- "Logging never blocks on disk I/O"
- "Uses async/await for all network operations"

**These are rare.** For architectural requirements, write a test that invokes AI code review:

```python
def main():
    """Verify non-blocking logging (architectural requirement)."""

    prompt = """Follow instructions in @the-system/prompts/CODE_REVIEW_FOR_REQUIREMENT.md

Requirement: $REQ_LOGGING_001 - Logging never blocks on disk I/O

Check for: memory buffer, async disk writes, immediate return from log calls"""

    result = subprocess.run(
        ['uv', 'run', '--script', './the-system/scripts/prompt_agentic_coder.py'],
        input=prompt, capture_output=True, text=True, encoding='utf-8'
    )

    assert result.returncode == 0  # $REQ_LOGGING_001
    assert 'VERDICT: PASS' in result.stdout  # $REQ_LOGGING_001
```

**See @the-system/prompts/CODE_REVIEW_FOR_REQUIREMENT.md for details on architectural testing.**

---

## Important Notes

### Test All Requirements in Flow

Even if asked about one $REQ_ID, test **ALL** requirements in that flow file. One flow = one test file that executes the complete sequence.

### Tests Start in ./tests/failing/

New tests go in `./tests/failing/`. When passing, they're moved to `./tests/passing/`.

### Do NOT Test Ctrl-C/SIGINT

**Never write tests that send Ctrl-C or SIGINT to the application under test.**

On Windows, Ctrl-C signals propagate to parent processes, killing the test runner. Ctrl-C requirements (like `$REQ_SHUTDOWN_001`, `$REQ_SHUTDOWN_005`) are valid and the functionality works in normal operation, but cannot be safely tested in the automated test suite.

If a requirement mentions Ctrl-C/SIGINT:
- Accept that it's valid but untestable in automated tests
- Do NOT write assertions to verify Ctrl-C behavior
- Skip those specific requirements in your test
- Use `process.kill()` for all test cleanup instead

### Do NOT Use pytest

Write standalone scripts with `main()`, `assert` statements, return codes, and `sys.exit(main())`.

### Add Dependencies

Add packages to script metadata:
```python
# dependencies = [
#   "requests",  # For HTTP testing
# ]
```

---

## Summary

1. Read entire flow file
2. Create/update test file in `./tests/failing/`
3. Write test function verifying ALL flow requirements
4. Tag assertions with `# $REQ_ID`
5. Use `try`/`finally` for cleanup
6. Make executable with `uv run --script`

## Report Your Work

Write a brief summary of what you created:
- Test file path
- Flow being tested
- Requirements covered (list $REQ_IDs)
- Test approach (how you verify behavior)
