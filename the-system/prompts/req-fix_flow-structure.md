# fix_req-flow-structure.md -- Fix Flow Structure

Ensure flow documents in `./reqs/` tell complete use-case stories from start to shutdown.

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

## Good Flow Structure

Each flow document must tell a complete, testable story. Include startup/shutdown requirements ONLY if there are actual requirements about startup or shutdown behavior.

**Organization:**
- Flow documents can be organized by use case OR technical category
- **What matters:** Each document contains a logical, testable sequence

**Good examples:**

*Use-case organization:*
- `startup-to-shutdown.md` -- Explicit startup/shutdown requirements (because that's what it's about)
- `install.md` -- Installation steps from scratch to ready state
- `client-usage.md` -- Connect, perform operations, disconnect

*Technical category organization (also valid):*
- `network-requirements.md` -- Network setup, network operations (startup/shutdown implied)
- `logging-requirements.md` -- Log operations, log formatting (startup/shutdown implied)
- `api-endpoints.md` -- API usage, request/response handling (startup/shutdown implied)

**Bad (incomplete or over-specified):**
- `logging-requirements.md` -- Adding generic "app starts" and "app stops" when there are no requirements about startup/shutdown
- `network-requirements.md` -- Missing the actual network operation requirements
- `api-endpoints.md` -- Only API definitions without usage requirements

---

## What to Check

**Completeness:**
- No gaps in the logical sequence
- If startup/shutdown have observable requirements, include them
- If no startup/shutdown requirements exist, don't add generic ones

**Testability:**
- Can be tested (unit, integration, or end-to-end depending on scope)
- Independently verifiable (doesn't depend on other flows)
- Has observable behavior

**Organization:**
- By use case OR technical category (both acceptable)
- Must describe actual requirements, not generic lifecycle steps

**Sequence:**
- Steps follow logical order
- Dependencies are clear

---

## What to Add (and What NOT to Add)

When completing flows, **only add requirements documented in READMEs**.

**Skip (do NOT add these when completing sequences):**
- **OS/runtime behavior** (e.g., "Process terminates on SIGKILL", "Connections close when process exits")
- **Natural consequences** (e.g., "OOM crash when memory exhausted", "Data loss on crash")
- **Explanatory text about design trade-offs** ("We chose X over Y because...")
- **Performance claims** (e.g., "Fast startup", "Handles 10k requests/sec")
- **Redundant restatements** with consequence details
- **Constraint-only statements** without observable behavior (e.g., "Port number is required" without saying what happens)

**DO add when documented in READMEs:**
- Application behavior you implement
- User actions and system responses
- Observable startup/shutdown steps
- Error handling with observable outcomes

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Verify each flow contains a logical, testable sequence
4. **Focus on significant structural problems** -- ignore minor ordering issues; only fix major structure gaps
5. **Fix by adding** missing requirements that are documented in READMEs
6. **Fix by removing** generic startup/shutdown steps that have no actual requirements
7. **Fix by reordering** steps to follow logical sequence
8. **Fix by splitting/merging** flows to make them independently testable

**Important:** Only include startup/shutdown requirements if the READMEs document specific observable behavior about startup or shutdown. Don't add generic "app starts" and "app stops" steps.

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the problematic flow structure)
- After: (the corrected flow structure)
- Why: (what structural problem was fixed - missing requirements, unnecessary generic steps, illogical ordering, etc.)

**If no significant issues found:** State that all flows contain logical, testable sequences appropriate to their scope.
