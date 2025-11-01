# fix_req-contradictions.md -- Check for Contradictions

Check if any requirements in `./reqs/` contradict each other.

---

## THE SIX RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)

---

## What Is a Contradiction?

Two or more requirements specify behavior that cannot all be true simultaneously.

**Examples:**

**Mutually exclusive behavior:**
- `$REQ_A`: "Must start immediately when launched"
- `$REQ_B`: "Must wait for user confirmation before starting"
- **Problem:** Can't both start immediately and wait

**Conflicting requirements:**
- `$REQ_A`: "At least one port rule required when starting"
- `$REQ_B`: "Can be started without port rules"
- **Problem:** If both apply to same scenario, they contradict

**Not contradictions:**
- Requirements for different scenarios
- Sequential requirements (first X, then Y)
- Requirements specifying different aspects of same feature

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Look for requirements that specify opposite or mutually exclusive behaviors
4. Verify if apparent contradictions are actually different scenarios
5. **Be conservative** -- only flag clear, unambiguous contradictions

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process.

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `GOODENUF` -- No contradictions found
- `NEEDIMPROV` -- Found contradictions and fixed them (AI made changes to ./reqs/)
- `READMEBUG` -- Found contradictions that require human to fix README documentation

**Example outputs:**

**No contradictions:**
```
Analyzed all requirements across all flow files. Checked for mutually exclusive behaviors and conflicting specifications. No contradictions found.

GOODENUF
```

**Contradictions requiring README fix:**
```
# Contradiction Found

**Requirements in conflict:**

- **$REQ_STARTUP_003** in ./reqs/startup.md
  - Source: ./readme/LIFECYCLE.md (Section: "Startup")
  - Text: Must start immediately when launched

- **$REQ_STARTUP_007** in ./reqs/startup.md
  - Source: ./readme/LIFECYCLE.md (Section: "Configuration")
  - Text: Must wait for user confirmation before starting

**Why they contradict:**
Cannot both start immediately and wait for confirmation.

**Recommendation:**
Revise README to clarify startup behavior.

READMEBUG
```
