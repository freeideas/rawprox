# fix_req-overspec.md -- Fix Over-Specification

Ensure requirements in `./reqs/` match the specificity level of README documentation.

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

## What Is Over-Specification?

Requirements include details not specified in source READMEs.

**Over-specified (WRONG):**
- README: "Show error if port missing"
- REQ: "Print `ERROR: PORT REQUIRED` to STDERR and exit with code -3"
- **Problem:** Exact message text, stream, and exit code not in README

**Correctly specified (RIGHT):**
- README: "Show error if port missing"
- REQ: "Show error message if port number is missing and exit"

**When to include details:**
- README explicitly states them
- Logical necessity (e.g., "crashes" implies non-zero exit)
- Standard protocols (e.g., HTTP status codes)

**When to omit details:**
- Exact error message wording (unless specified)
- Internal implementation (unless specified)
- File formats, data structures (unless specified)
- Performance numbers (unless specified) -- these are also hard to test reliably
- Speed/throughput claims (unless specified) -- difficult to verify consistently
- Output streams (unless specified)
- Specific exit codes (unless specified or logically necessary)

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. For each requirement, compare to README source
4. **Focus on significant over-specification** -- ignore minor detail additions; only fix requirements with substantial extra details
5. **Fix by removing** details not in README (keep testable, remove excess)

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the over-specified requirement text)
- After: (the corrected requirement text, matching README detail level)
- Why: (what details were not in README)

**If no significant issues found:** State that requirements match README detail level.
