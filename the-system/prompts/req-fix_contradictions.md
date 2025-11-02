# fix_req-contradictions.md -- Check for Contradictions

Check if any requirements in `./reqs/` contradict each other.

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
5. **Focus on significant issues** -- ignore minor inconsistencies; only flag clear, unambiguous contradictions

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the contradicting text)
- After: (the corrected text)
- Why: (reason for the change)

**If contradictions require README changes:**
- Output exactly: `**README_CHANGES_REQUIRED: true**` on its own line
- Explain what needs to be clarified in the README files
- Do NOT attempt to fix unfixable contradictions in reqs files

**If no significant issues found:** State that no significant contradictions were found.
