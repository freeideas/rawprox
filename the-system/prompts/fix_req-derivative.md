# fix_req-derivative.md -- Remove Derivative Requirements

Remove requirements that are natural consequences of other requirements or OS/language behavior rather than application features.

---

## THE SIX RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)

---

## What Are Derivative Requirements?

**Derivative requirements** are consequences of other requirements or OS/language behavior, not application features.

### Category 1: Natural Consequences of Other Requirements

**Example:**
- **Real requirement:** "Buffer in memory when logging falls behind"
- **Real requirement:** "Never block network I/O on disk writes"
- **Derivative (REMOVE):** "If buffer fills memory, crash with OOM"
- **Why derivative?** OOM is what happens when you buffer indefinitely -- it's not a feature to implement

**Example:**
- **Real requirement:** "Flush buffer to disk periodically"
- **Derivative (REMOVE):** "Data in buffer between flushes may be lost on crash"
- **Why derivative?** This is just restating that unflushed data isn't on disk yet

### Category 2: OS/Language/Runtime Behavior

**Examples to REMOVE:**
- "Crash with out-of-memory error when memory exhausted" (OS does this)
- "Exit with non-zero code on unhandled exception" (runtime does this)
- "Process terminates on SIGKILL" (OS does this)
- "TCP connection closes when process exits" (OS does this)

**Why remove?** You're not implementing these -- the OS/runtime is.

### Category 3: Explanatory Text About Design Trade-offs

README sections often explain **why** design decisions were made and what the trade-offs are. These are not requirements.

**Example:**
- README says: "We chose to buffer in memory and crash on OOM rather than slow down connections, because throughput is more important than logging completeness"
- **Real requirement:** "Never block network I/O on disk writes"
- **Real requirement:** "Buffer in memory when logging falls behind"
- **Derivative (REMOVE):** "Predictable failure mode is OOM crash, not connection slowdown"
- **Why derivative?** This is explanatory text about the design trade-off, not a testable feature

### Category 4: Redundant Restatements

**Example:**
- **Real requirement:** "Never slow down connections due to logging"
- **Derivative (REMOVE):** "Even under stress leading to OOM, connections maintain full throughput until crash"
- **Why derivative?** This just restates the first requirement with added consequence details

---

## What to Keep

**DO keep requirements that specify:**
- Application behavior you implement in code
- Design constraints ("must use non-blocking I/O")
- Observable actions ("log ready message")
- Error handling you write ("show error and exit if port missing")

**DO remove requirements that are:**
- Consequences of other requirements
- OS/language/runtime behavior
- Explanatory text about design trade-offs
- Redundant restatements with consequence details

---

## Common Patterns to Remove

### Pattern 1: OOM/Memory Exhaustion
```
✗ REMOVE: "Crash with OOM when buffer fills"
✗ REMOVE: "Data loss on OOM crash"
✗ REMOVE: "Predictable failure mode is OOM"
✓ KEEP: "Buffer in memory when logging falls behind"
✓ KEEP: "Never block network I/O on disk writes"
```

### Pattern 2: Process Termination Consequences
```
✗ REMOVE: "Unflushed data is lost on crash"
✗ REMOVE: "Connections close when process exits"
✓ KEEP: "Flush buffer on graceful shutdown (SIGTERM)"
```

### Pattern 3: "Why We Chose This" Text
```
✗ REMOVE: "We chose approach X over Y because..."
✗ REMOVE: "Predictable failure mode is Z, not W"
✓ KEEP: "Use approach X" (without the justification)
```

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Identify derivative requirements
4. Remove them from flow files
5. Ensure core requirements that cause the derivatives remain

**Be careful:** Sometimes README explanatory text helps clarify what the actual requirement is. Extract the requirement, discard the explanation.

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process. If derivative requirements are found, list which ones were removed and why.

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `GOODENUF` -- No derivative requirements found
- `NEEDIMPROV` -- Found derivative requirements and removed them (AI edited ./reqs/)
- `READMEBUG` -- README has unclear requirements that need human clarification
