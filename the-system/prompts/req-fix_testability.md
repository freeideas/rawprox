# fix_req-testability.md -- Check for Untestable Requirements

Check if all requirements in `./reqs/` are testable (have observable behavior).

---

## THE SEVEN RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every reasonably testable behavior in READMEs must have a $REQ_ID
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

Whenever you create or update these tests, aim to keep each run under a minute; if the script exceeds that, split the checks across multiple test files.

### 3. Limitation/Capability (informational, no test needed)
- "TCP only" / "No UDP support"
- "Windows only"
- "Pre-built binaries available in ./release/"
- "Supports Ctrl-C to stop" / "Responds to SIGINT" / "Can be stopped with Ctrl-C"

**Note on Ctrl-C/SIGINT:** These requirements are valid and the functionality works in normal operation, but cannot be safely tested on Windows because Ctrl-C signals propagate to parent processes, killing the test runner.

---

## Untestable Requirements (Flag These)

**Performance and load characteristics (difficult to test reliably):**
- ✗ "Handles 10,000 requests per second" -- hard to test consistently
- ✗ "Low latency" -- subjective and environment-dependent
- ✗ "Fast startup" -- relative and unreliable to verify
- ✗ "Scales to high traffic" -- difficult to test consistently

**Vague statements without observable behavior:**
- ✗ "Should be user-friendly" -- subjective, not verifiable
- ✗ "Must be reliable" -- vague, no observable criteria
- ✗ "Good error messages" -- subjective without specific requirements

**Key difference:**
- ✓ "System accepts X and does Y" → testable (happy path)
- ✓ "System uses architecture Y" → testable (architectural requirement)
- ✗ "Fast performance" → untestable (performance claim)
- ✗ "User-friendly interface" → untestable (subjective)

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Identify requirements that are truly untestable (performance claims, vague subjective statements)
4. **Focus on significant issues** -- ignore minor testability concerns; only flag clearly untestable requirements
5. **Happy path focus** -- Requirements like "accepts one directory argument" or "port number is required" are fine; they describe correct usage. Don't flag them as untestable just because they don't specify every possible wrong input.

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the untestable requirement text, including $REQ_ID)
- After: (the corrected requirement text, or note if deleted)
- Why: (what made it untestable and how it was fixed)

**If no significant issues found:** State that requirements are testable.
