# fix_req-overspec.md -- Fix Over-Specification

Ensure requirements in `./reqs/` match the specificity level of README documentation.

---

## THE SIX RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)

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
- Performance numbers (unless specified)
- Output streams (unless specified)
- Specific exit codes (unless specified or logically necessary)

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. For each requirement, compare to README source
4. **Fix by removing** details not in README (keep testable, remove excess)

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process. If issues are found, include which requirements were over-specified and how they were fixed.

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `GOODENUF` -- No over-specification found, requirements match README detail level
- `NEEDIMPROV` -- Found over-specified requirements and fixed them (AI simplified ./reqs/)
- `READMEBUG` -- README documentation has unclear specifications needing clarification
