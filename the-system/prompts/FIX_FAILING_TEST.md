# FIX_FAILING_TEST.md -- Fix Code to Make Test Pass

Fix failing tests by implementing or correcting code in `./code/`.

---

## Project Philosophy

**Follow @the-system/prompts/PHILOSOPHY.md:**
- Build only what is explicitly required in `/reqs/`
- No "nice to have" features
- No undocumented edge cases
- No error handling except where required
- Complexity is a bug -- fix it by deletion
- Implementation choices not mandated by README can change freely

---

## Context: Use-Case Documentation

For broader context about what the application does and why:
- `./README.md` -- Project overview and architectural intent
- `./readme/*.md` -- See these as needed for more detailed specifications

These documents explain the "why" behind requirements and provide architectural context. Refer to them when you need to understand the purpose and expected behavior of features you're implementing.

---

## Instructions

### Step 1: Understand the Failure

Read test output to identify the issue

### Step 2: Read the Test

Read the failing test file:
- What $REQ_IDs it tests (check `# $REQ_ID` comments)
- What behavior is expected
- What the test verifies

### Step 3: Read the Requirements

As needed, you can use `uv run --script ./the-system/scripts/reqtrace.py $REQ_ID` to see the requirement definitions, and which code files are tagged with that req id.

### Step 4: Implement or Fix Code

Create/modify files in `./code/` to make test pass.

**Code structure is flexible:**
- Organize however makes sense
- Refactor freely
- Follow @the-system/prompts/PHILOSOPHY.md

**Code organization guidance:**
- **Consider creating focused files for each requirement or requirement group**
- When implementing `$REQ_STARTUP_001` and `$REQ_STARTUP_002` for port binding, and `$REQ_STARTUP_003` for health checks, consider:
  - `startup_port_binding.cs` for the port-related requirements
  - `startup_health.cs` for the health check requirement
  - Rather than one large `startup.cs` handling everything
- **Name files to reflect their specific purpose** tied to the requirements they serve
- **Accept some duplication for clarity** -- it's often better to have similar code in separate files than to tightly couple unrelated requirements
- This makes requirement tracing clearer: each file serves specific `$REQ_ID`s
- Not a strict rule -- use judgment -- but when choosing between consolidation and separation, lean toward separation by requirement boundaries

**Tag code with $REQ_ID comments:**
```csharp
public void Start()
{
    // $REQ_STARTUP_001: Launch server process
    _process.Start();

    // $REQ_STARTUP_002: Bind to port
    _listener = new TcpListener(IPAddress.Any, _port);
    _listener.Start();
}
```

**Tagging guidelines:**
- Add above/on line implementing the requirement
- Format: `// $REQ_ID` or `// $REQ_ID: brief description`
- Not every line needs a tag -- just key implementation points

### Step 5: Fix Test If It Is Truly Incorrect

**IMPORTANT: Tests are standalone Python scripts, not pytest:**
- Use plain `assert` statements, not `pytest.assert_*`
- Use `try`/`except`/`finally` for setup/teardown, not pytest fixtures
- Return exit codes 0/1, not pytest exit codes
- Do NOT import pytest or use any pytest features

**In most cases, fix the code, not the test.**

**Valid reasons to fix a test:**
- Test misinterprets the requirement
- Test has a bug (wrong assertion logic)
- Test impossible to satisfy as written

**If you fix a test:**
- Document why in a comment
- Ensure it still verifies same $REQ_IDs
- Keep or re-apply $REQ_ID tags

**Windows warning:** Always use `process.kill()` for cleanup in tests. Never use `terminate()`, `send_signal()`, or `CTRL_C_EVENT` -- on Windows these propagate to the parent process and kill the test runner. Even on Linux we want to avoid this for cross-platform reasons

---

## Architectural Tests (Rare)

Some tests verify **implementation patterns** by invoking AI code review:

```python
def test_logging_nonblocking():
    prompt = """Follow @the-system/prompts/CODE_REVIEW_FOR_REQUIREMENT.md

Requirement: $REQ_LOGGING_001 - Logging never blocks on disk I/O"""

    result = subprocess.run(
        ['uv', 'run', '--script', './the-system/scripts/prompt_agentic_coder.py'],
        input=prompt, capture_output=True, text=True, encoding='utf-8'
    )
    assert 'VERDICT: PASS' in result.stdout  # $REQ_LOGGING_001
```

**If architectural test fails:**
1. Read AI's verdict (explains what's wrong)
2. Understand the architectural requirement (HOW to implement, not just WHAT)
3. Refactor code to match required pattern
4. Keep behavioral tests passing while refactoring

**Key difference:**
- Behavioral test fails → Implement missing functionality
- Architectural test fails → Refactor to use required pattern

---

## Report Your Work

Write a brief analysis covering:
- What the test failure indicated (root cause)
- What you implemented or fixed
- Which $REQ_IDs are now satisfied
- Test results after your changes
