# req-check_readmes.md -- Check README Quality

Check if README documentation in `./README.md` and `./readme/` has quality issues.

---

## Purpose

Validate that documentation is clear, complete, and unambiguous.

**This prompt:**
- Reads all README documentation
- Identifies quality issues
- Reports problems that must be fixed

---

## What to Check

### 1. Internal Contradictions

**Check:** Do READMEs contradict themselves?

**Examples:**
- README says "port defaults to 8080" in one section, "port is required" in another
- README says "starts immediately" in one place, "waits for confirmation" elsewhere
- Mutually exclusive behaviors described without clarifying when each applies

**Not contradictions:**
- Different scenarios (e.g., "with config file" vs "without config file")
- Sequential behaviors (e.g., "first X, then Y")
- Different aspects of same feature

### 2. Constraint-Only Statements

**Check:** Are there constraints without observable behavior?

**Examples of problems:**
- "Port number is required" -- doesn't say what happens when missing
- "At least one rule must be configured" -- doesn't say error or wait or default
- "Configuration file must be valid JSON" -- doesn't say what happens with invalid JSON
- "Username must not be empty" -- doesn't say rejection behavior

**Good examples:**
- "Show error and exit if port number is missing"
- "Wait for configuration if no rules are provided"
- "Log error and use defaults if JSON is invalid"

### 3. Ambiguous Specifications

**Check:** Are specifications unclear or open to multiple interpretations?

**Examples:**
- "Handle errors appropriately" -- what does "appropriately" mean?
- "Fast startup" -- how fast? what's observable?
- "Secure connection" -- which protocol? what validation?
- "Process requests efficiently" -- what does this mean in practice?

### 4. Performance/Load Claims Without Observable Behavior

**Check:** Are there performance claims that can't be tested?

**Examples of problems:**
- "Handles 10,000 requests per second" -- hard to test reliably
- "Low latency response" -- subjective and environment-dependent
- "Fast startup time" -- relative, not observable
- "Scales to high traffic" -- load characteristics difficult to verify

**Good examples (observable behavior):**
- "Uses non-blocking I/O for all network operations"
- "Buffers in memory when logging falls behind"
- "Never blocks network I/O on disk writes"

**Key distinction:** Architecture/design decisions are testable (via code review), performance numbers are not.

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Check for the four categories of problems listed above
3. **Focus on significant issues** -- ignore minor unclear wording; only flag clear problems
4. Report problems that must be fixed

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:**

Output exactly: `**README_CHANGES_REQUIRED: true**` on its own line

Then for each issue, list:
- File: (which README file)
- Problem: (what category of problem)
- Location: (section or quote)
- Issue: (what needs to be fixed)

**Example:**
```
**README_CHANGES_REQUIRED: true**

File: ./readme/LIFECYCLE.md
Problem: Constraint-only statement
Location: Section "Configuration"
Issue: States "port number is required" but doesn't specify what happens when missing (error message? exit? default value?)

File: ./readme/API.md
Problem: Internal contradiction
Location: Sections "Startup" and "Error Handling"
Issue: "Startup" says port defaults to 8080, but "Error Handling" says missing port causes error exit
```

**If no significant issues found:**

State: "README documentation has no significant quality issues."
