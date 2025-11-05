# req-check_readmes.md -- Check README Quality

Check if README documentation in `./README.md` and `./readme/` has quality issues.

---

## Purpose

Validate that documentation clearly describes what the software does with correct usage, without being pedantic about error handling.

**This prompt:**
- Reads all README documentation
- Identifies significant quality issues (contradictions, vagueness, untestable claims)
- Does NOT demand exhaustive error specifications or wrong-input handling
- Reports problems that must be fixed

**Philosophy:** READMEs should focus on what the software DOES, not exhaustively document every way it can fail.

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

### 2. Vague or Unobservable Specifications

**Check:** Are specifications too vague to implement or verify?

**Examples of problems:**
- "Handle errors appropriately" -- no indication what "appropriately" means
- "Secure connection" -- which protocol? which version? what validation?
- "Process requests efficiently" -- what does this mean in observable terms?
- "User-friendly interface" -- completely subjective

**Good examples (specific enough to implement):**
- "Accept connections on port 8080"
- "Use TLS 1.2 or higher for HTTPS"
- "Log each request to stdout"

**Note:** Statements like "accepts one directory argument" or "port number is required" are NOT vague - they clearly describe correct usage. Don't flag these.

### 3. Performance/Load Claims Without Observable Behavior

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

## What NOT to Flag

**DO NOT flag as problems:**
- **Statements of correct usage** -- "Accepts one directory argument", "Port number is required", "Configuration file must be valid JSON" are all fine. READMEs don't need to specify what happens with every wrong input.
- **Error examples without exhaustive detail** -- If README says "show error if port in use" without specifying exact error message format, that's fine. We don't need exact error text specifications.
- **Happy path focus** -- If README documents what the software does with correct input but doesn't exhaustively document all error cases, that's acceptable. Focus on happy paths is good.
- **Absence of features** -- "Does not support UDP" is just documentation of what's not included; it's not a quality issue.
- **Build documentation** -- It's fine for READMEs to include build instructions, development prerequisites, or compilation steps. These won't generate requirements, but they're not quality problems.

**The philosophy:** READMEs should clearly document what the software DOES with correct usage. They don't need to exhaustively specify every possible error condition, wrong input, or edge case.

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Check for the three categories of problems listed above
3. **Focus on significant issues** -- ignore minor unclear wording; only flag clear problems
4. **Don't be pedantic** -- if something describes correct usage clearly, don't demand error handling specifications
5. Report problems that must be fixed

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
Problem: Vague or unobservable specification
Location: Section "Error Handling"
Issue: States "handle errors appropriately" without indicating what appropriate means - log? exit? retry?

File: ./readme/API.md
Problem: Internal contradiction
Location: Sections "Startup" and "Error Handling"
Issue: "Startup" says port defaults to 8080, but "Error Handling" says missing port causes error exit

File: ./readme/PERFORMANCE.md
Problem: Performance/load claims without observable behavior
Location: Section "Throughput"
Issue: Claims "handles 10,000 requests per second" which is difficult to test reliably. Instead, document architectural decisions like "uses non-blocking I/O"
```

**If no significant issues found:**

State: "README documentation has no significant quality issues."
