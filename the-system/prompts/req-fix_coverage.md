# fix_req-coverage.md -- Fix Coverage Gaps

Ensure all reasonably testable behaviors from READMEs are represented in `./reqs/`.

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

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Identify reasonably testable behaviors in READMEs missing from flows
4. **Distinguish requirements from illustrations** -- if README says "it will crash with OOM instead of blocking", the requirement is "don't block", not "crash with OOM"
5. **Focus on significant gaps** -- ignore minor omissions; only address important missing behaviors
6. **Fix by adding missing requirements** to appropriate flow files
7. **Fix by splitting** requirements that combine multiple distinct behaviors

**Reasonably testable behaviors:**
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
- General descriptions without reasonably testable outcomes
- **Explanatory text about design trade-offs** ("we chose X over Y because...")
- **Illustrative examples of consequences** (e.g., "it will crash with OOM instead of blocking" is illustrating non-blocking behavior, not requiring OOM)
- **Natural consequences of other requirements** (e.g., OOM from unbounded buffering, data loss on crash)
- **OS/runtime behavior** (e.g., process termination, signal handling by OS)
- **Redundant restatements with consequence details**
- **Performance/speed characteristics** (e.g., "handles 10k requests/sec", "low latency", "fast startup") -- difficult to test reliably
- **Load-handling claims** (e.g., "scales to high traffic", "efficient under load") -- hard to verify consistently
- **Negative capabilities** (e.g., "does not support UDP", "doesn't handle IPv6") -- absence of functionality is not testable unless there's specific error behavior when attempted
- **Wrong inputs and edge cases** (e.g., what happens with 2 directory arguments when README says "accepts one directory argument", what happens when port is missing) -- ONLY add these if README explicitly documents the error behavior. Focus on happy paths.

**Critical distinction:**
- ✓ "Never block I/O" → this IS a requirement (add it if missing)
- ✗ "Will crash with OOM instead of blocking" → this is an ILLUSTRATION of non-blocking (don't add OOM as requirement)
- ✓ "Use non-blocking I/O" → this IS a requirement (architectural, testable via code review)
- ✗ "Fast performance" → this is NOT testable (skip it)
- ✗ "Does not support UDP" → this is NOT a requirement (absence of feature, nothing to test)
- ✓ "Returns error 'UDP not supported' if UDP attempted" → this IS a requirement (observable error behavior)
- ✓ "Accepts one directory argument" → this IS a requirement (describes happy path)
- ✗ "Error if two directory arguments provided" → skip unless README explicitly documents this error
- ✓ "Port number is required" → this IS a requirement (describes correct usage)
- ✗ "Exit with error if port missing" → skip unless README explicitly documents this error behavior

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

**If no significant issues found:** State that all important testable behaviors are covered.
