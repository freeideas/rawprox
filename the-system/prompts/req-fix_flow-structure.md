# fix_req-flow-structure.md -- Fix Flow Structure

Ensure flow documents in `./reqs/` tell complete use-case stories from start to shutdown.

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

## Good Flow Structure

Each flow document must tell a complete story from application start to shutdown, testable end-to-end.

**Organization:**
- Flow documents can be organized by use case OR technical category
- **What matters:** Each document contains a complete sequence from app start to app exit

**Good examples:**

*Use-case organization:*
- `startup-to-shutdown.md` -- Start server, verify ready, use it, shutdown
- `install.md` -- Install from scratch to ready state
- `client-usage.md` -- Connect, perform operations, disconnect

*Technical category organization (also valid):*
- `network-requirements.md` -- Start app, network setup, network operations, shutdown
- `logging-requirements.md` -- Start app, logging initialization, log operations, shutdown
- `api-endpoints.md` -- Start app, API setup, API usage, shutdown

**Bad (incomplete sequences):**
- `network-requirements.md` -- Only network aspects without start/shutdown steps
- `logging-requirements.md` -- Only logging operations, missing app lifecycle
- `api-endpoints.md` -- Only API definitions, no executable flow

---

## What to Check

**Completeness:**
- Clear beginning state
- Clear ending/shutdown state
- No gaps in sequence

**Testability:**
- Can execute as single test
- End-to-end testable

**Organization:**
- By use case OR technical category (both acceptable)
- Must tell a complete story from app start to exit, not just list features

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
3. Verify each flow contains a complete sequence from app start to app exit
4. **Focus on significant structural problems** -- ignore minor ordering issues; only fix major structure gaps
5. **Fix by adding** missing startup/shutdown steps documented in READMEs to make flows complete
6. **Fix by reordering** steps to follow logical sequence (start → operations → exit)
7. **Fix by splitting/merging** flows to make them independently testable

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the incomplete flow structure, describe what was missing)
- After: (the complete flow structure, what was added/reordered)
- Why: (what structural problem was fixed)

**If README lacks information for complete sequences:**
- Output exactly: `**README_CHANGES_REQUIRED: true**` on its own line
- Explain what's missing from the README files
- Do NOT invent startup/shutdown steps not documented in READMEs

**If no significant issues found:** State that all flows contain complete sequences from app start to exit.
