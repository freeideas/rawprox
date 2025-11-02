# fix_req-coverage.md -- Fix Coverage Gaps

Ensure all testable behaviors from READMEs are represented in `./reqs/`.

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

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Identify testable behaviors in READMEs missing from flows
4. **Distinguish requirements from illustrations** -- if README says "it will crash with OOM instead of blocking", the requirement is "don't block", not "crash with OOM"
5. **Focus on significant gaps** -- ignore minor omissions; only address important missing behaviors
6. **Fix by adding missing requirements** to appropriate flow files
7. **Fix by splitting** requirements that combine multiple distinct behaviors

**Testable behaviors:**
- Actions users take
- System responses
- Observable outputs
- Error conditions
- Success criteria
- State changes
- Network behavior
- File operations
- Process lifecycle

**Skip (do NOT create requirements for these):**
- Background information
- Installation instructions (unless they specify behavior)
- General descriptions without testable outcomes
- **Explanatory text about design trade-offs** ("we chose X over Y because...")
- **Illustrative examples of consequences** (e.g., "it will crash with OOM instead of blocking" is illustrating non-blocking behavior, not requiring OOM)
- **Natural consequences of other requirements** (e.g., OOM from unbounded buffering, data loss on crash)
- **OS/runtime behavior** (e.g., process termination, signal handling by OS)
- **Redundant restatements with consequence details**
- **Performance/speed characteristics** (e.g., "handles 10k requests/sec", "low latency", "fast startup") -- difficult to test reliably
- **Load-handling claims** (e.g., "scales to high traffic", "efficient under load") -- hard to verify consistently

**Critical distinction:**
- ✓ "Never block I/O" → this IS a requirement (add it if missing)
- ✗ "Will crash with OOM instead of blocking" → this is an ILLUSTRATION of non-blocking (don't add OOM as requirement)
- ✓ "Use non-blocking I/O" → this IS a requirement (architectural, testable via code review)
- ✗ "Fast performance" → this is NOT testable (skip it)

---

## How to Fix

**Add missing requirements:**
- For each missing testable behavior, add a $REQ_ID to the appropriate flow file
- Use proper format and source attribution
- Maintain flow sequence (start to shutdown)

**Split combined requirements:**
- If one requirement describes multiple distinct testable behaviors, split into separate $REQ_IDs
- Each behavior gets its own requirement

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (what was missing, quote relevant README text)
- After: (the new requirement(s) added)
- Why: (why this was missing coverage)

**If README is unclear or incomplete:**
- Output exactly: `**README_CHANGES_REQUIRED: true**` on its own line
- Explain what needs clarification in the README files
- Do NOT create requirements for behaviors not clearly documented

**If no significant issues found:** State that all important testable behaviors are covered.
