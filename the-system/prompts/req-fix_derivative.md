# fix_req-derivative.md -- Remove Derivative Requirements

Remove requirements that are natural consequences of other requirements or OS/language behavior rather than application features.

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

### Category 5: Performance/Load Characteristics

**Examples to REMOVE:**
- "Handles 10,000 requests per second" (performance claims are hard to test reliably)
- "Low latency response" (subjective and environment-dependent)
- "Scales to high traffic" (load characteristics are difficult to verify consistently)
- "Fast startup time" (speed is relative and hard to test)

**Why remove?** Performance and load characteristics are difficult to test reliably and consistently.

**Exception:** Keep architectural requirements that enable performance (e.g., "use non-blocking I/O", "buffer in memory").

---

## What to Keep

**DO keep requirements that specify:**
- Application behavior you implement in code
- Design constraints ("must use non-blocking I/O")
- Observable actions ("log ready message")
- Error handling you write ("show error and exit if port missing")
- **Startup/shutdown steps needed for flow completeness** (see exception below)

**DO remove requirements that are:**
- Consequences of other requirements
- OS/language/runtime behavior
- Explanatory text about design trade-offs
- Redundant restatements with consequence details

---

## CRITICAL EXCEPTION: Flow Completeness

**DO NOT remove startup/shutdown steps if removal would make a flow incomplete.**

Each flow must be independently testable from start to shutdown (Rule #4: Tell Stories). Even if startup/shutdown steps seem like "natural consequences" of lifecycle requirements defined elsewhere, **keep them if they're necessary for the flow to be executable end-to-end.**

**Example - DO NOT REMOVE:**
```
# Configuration Flow (./reqs/configuration.md)

$REQ_CONFIG_STARTUP_001: Start Service
The service must start with ./release/AiAlfrescoSvc.exe and bind to a port.

$REQ_CONFIG_002: Load Configuration File
At startup, the service must load appsettings.json...

$REQ_CONFIG_SHUTDOWN_001: Graceful Shutdown
The service must shut down gracefully when Ctrl+C is pressed.
```

**Why keep?** Removing these would leave configuration.md with no start/shutdown steps, making it untestable as a standalone flow.

**What IS derivative and should be removed:**
```
$REQ_CONFIG_003: OOM Crash on Memory Exhaustion
If memory fills, the service crashes with out-of-memory error.
```

**Why remove?** This is a consequence of memory usage, not a configuration feature.

---

## Guideline: Complete Flows vs Truly Derivative

**Test:** If removing a requirement would make the flow untestable end-to-end, keep it (even if similar requirements exist elsewhere).

**Keep:**
- Startup steps in each flow (needed for test execution)
- Shutdown steps in each flow (needed for test cleanup)
- Core sequence steps specific to that flow's use case

**Remove:**
- Consequences of other requirements (OOM, data loss on crash)
- OS/runtime behavior (SIGKILL handling, connection auto-close)
- Design trade-off explanations
- Redundant restatements with extra consequence details

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
4. **Focus on significant issues** -- ignore minor redundancies; only remove clear derivative requirements
5. Remove them from flow files
6. Ensure core requirements that cause the derivatives remain
7. **CRITICAL:** DO NOT remove startup/shutdown steps that make flows incomplete and untestable

**Be careful:**
- Sometimes README explanatory text helps clarify what the actual requirement is. Extract the requirement, discard the explanation.
- Each flow must remain independently testable from start to shutdown after your edits

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the derivative requirement text, including $REQ_ID)
- After: (deleted)
- Why: (why this was derivative, which category)

**If no significant issues found:** State that no significant derivative requirements were found.
