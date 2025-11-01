# fix_req-testability.md -- Check for Untestable Requirements

Check if all requirements in `./reqs/` are testable (have observable behavior).

---

## THE SIX RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)

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

---

## Untestable Requirements (Flag These)

**Constraint-only statements without observable behavior:**
- ✗ "Port number is required" -- doesn't say what happens when missing
- ✗ "At least one port rule is required" -- doesn't say error or wait
- ✗ "Configuration file must be valid JSON" -- doesn't say what happens with invalid JSON
- ✗ "Username must not be empty" -- doesn't say rejection behavior

**Key difference:**
- ✓ "System does X" or "System uses architecture Y" → testable
- ✗ "X is required" without saying what happens → untestable

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Identify requirements that state constraints without observable behavior
4. **Be precise** -- only flag constraint-only requirements, not architectural or limitation statements

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process. If issues are found, include specific $REQ_IDs, locations, problems, and recommendations.

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `GOODENUF` -- No issues found, requirements are testable
- `NEEDIMPROV` -- Found issues and fixed them (AI made changes to ./reqs/)
- `READMEBUG` -- Found issues that require human to fix README documentation

**Example outputs:**

**No issues:**
```
Analyzed all requirements in ./reqs/. All requirements specify observable behavior through one of three valid types:

1. Behavioral requirements with executable tests
2. Architectural requirements verified by code review
3. Limitation/capability statements

No untestable constraint-only requirements found.

GOODENUF
```

**Issues found requiring README fix:**
```
# Untestable Requirement Found

**$REQ_ID:** $REQ_STARTUP_005
**Location:** ./reqs/startup.md
**Source:** ./readme/LIFECYCLE.md (Section: "Configuration")

**Current text:**
Port number is required.

**Problem:**
States constraint without specifying what system does when constraint is violated.

**What's missing:**
What observable behavior occurs? What error? What action?

**Recommendation:**
Revise README to specify observable behavior.

**Example fixes:**
- Instead of: "Port number is required"
- Specify: "Must show error message and exit if port number is missing"

READMEBUG
```
