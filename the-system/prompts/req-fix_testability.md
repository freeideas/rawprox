# fix_req-testability.md -- Check for Untestable Requirements

Check if all requirements in `./reqs/` are testable (have observable behavior).

---

## THE SEVEN RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)
7. **Reasonably Testable** -- Requirements must have observable behavior that can be verified

---

## What Makes Requirements Testable?

**Three types of valid testable requirements:**

### 1. Behavioral (executable tests)
- "Must exit with error message when port number is missing"
- "Must return HTTP 404 for missing resources"
- "Must log when ready to accept connections"

### 2. Architectural (code review tests)
- "Network I/O operations must never block on disk writes"
- "TCP reads and writes must be non-blocking"
- "Uses async/await for all I/O operations"

**How to test:** Write a test that invokes AI to review code architecture:
```python
# Test calls prompt_agentic_coder.py with CODE_REVIEW_FOR_REQUIREMENT.md
# AI examines code and outputs VERDICT: PASS or FAIL
prompt = """Please follow the instructions in @the-system/prompts/CODE_REVIEW_FOR_REQUIREMENT.md

Requirement to verify:
$REQ_ARCH_001: [requirement text]
"""
result = subprocess.run(['uv', 'run', '--script', './the-system/scripts/prompt_agentic_coder.py'],
                       input=prompt, capture_output=True, text=True, encoding='utf-8')
assert 'VERDICT: PASS' in result.stdout  # $REQ_ARCH_001
```

### 3. Limitation/Capability (informational, no test needed)
- "TCP only" / "No UDP support"
- "Windows only"
- "Pre-built binaries available in ./release/"
- "Supports Ctrl-C to stop" / "Responds to SIGINT" / "Can be stopped with Ctrl-C"

**Note on Ctrl-C/SIGINT:** These requirements are valid and the functionality works in normal operation, but cannot be safely tested on Windows because Ctrl-C signals propagate to parent processes, killing the test runner.

---

## Untestable Requirements (Flag These)

**Constraint-only statements without observable behavior:**
- ✗ "Port number is required" -- doesn't say what happens when missing
- ✗ "At least one port rule is required" -- doesn't say error or wait
- ✗ "Configuration file must be valid JSON" -- doesn't say what happens with invalid JSON
- ✗ "Username must not be empty" -- doesn't say rejection behavior

**Performance and load characteristics (difficult to test reliably):**
- ✗ "Handles 10,000 requests per second" -- hard to test consistently
- ✗ "Low latency" -- subjective and environment-dependent
- ✗ "Fast startup" -- relative and unreliable to verify
- ✗ "Scales to high traffic" -- difficult to test consistently

**Key difference:**
- ✓ "System does X" or "System uses architecture Y" → testable
- ✗ "X is required" without saying what happens → untestable
- ✓ "Use non-blocking I/O" → testable (architectural requirement)
- ✗ "Fast performance" → untestable (performance claim)

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Identify requirements that state constraints without observable behavior
4. **Focus on significant issues** -- ignore minor testability concerns; only flag clear constraint-only requirements
5. **Be precise** -- only flag constraint-only requirements, not architectural or limitation statements

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the untestable requirement text, including $REQ_ID)
- After: (the corrected requirement text, or note if deleted)
- Why: (what made it untestable and how it was fixed)

**If issues require README changes:**
- Output exactly: `**README_CHANGES_REQUIRED: true**` on its own line
- Explain what needs to be specified in the README files
- Do NOT invent observable behaviors not documented in READMEs

**If no significant issues found:** State that requirements are testable.
