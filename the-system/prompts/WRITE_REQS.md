# WRITE_REQS.md -- Write Requirements from READMEs

Create testable requirement flows in `./reqs/` based on use-case documentation in `./readme/` and `./README.md`.

**This prompt is only used when no requirements exist yet.**

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

## What Is a Flow?

A flow is a **sequence of steps from application start to shutdown** that can be tested end-to-end.

**Example:** `./readme/LIFECYCLE.md` generates:
- `./reqs/install.md` -- Install to ready state
- `./reqs/startup-to-shutdown.md` -- Start server, use it, stop it
- `./reqs/uninstall.md` -- Remove from system

---

## Flow Document Format

```markdown
# Server Startup Flow

**Source:** ./readme/LIFECYCLE.md

Start server, verify ready, and shut down cleanly.

## $REQ_STARTUP_001: Launch Process
**Source:** ./readme/LIFECYCLE.md (Section: "Starting the Server")

Start the server executable with default configuration.

## $REQ_STARTUP_002: Bind to Port
**Source:** ./readme/LIFECYCLE.md (Section: "Network Binding")

Server must bind to configured port.

## $REQ_STARTUP_003: Log Ready Message
**Source:** ./readme/LIFECYCLE.md (Section: "Startup Logging")

Server must log when ready to accept connections.

## $REQ_STARTUP_004: Health Check Response
**Source:** ./readme/LIFECYCLE.md (Section: "Health Monitoring")

GET /health must return 200 OK.

## $REQ_STARTUP_005: Shutdown Cleanly
**Source:** ./readme/LIFECYCLE.md (Section: "Stopping")

Server must exit gracefully when receiving SIGTERM.
```

---

## What to Include

**DO write requirements for delivered software:**
- Runtime behavior of executable with correct inputs (happy paths)
- Command-line arguments and options (what they do, not what happens with wrong values)
- Network behavior, logging, file I/O
- Error handling **explicitly documented in README**
- Observable outputs and responses
- Architectural constraints (e.g., "use non-blocking I/O")

**DO NOT write requirements for:**
- Build scripts or build processes
- Development prerequisites (.NET SDK, compilers)
- How to compile or package
- Development tooling or infrastructure
- **Wrong inputs/edge cases** (unless README explicitly documents error behavior)
- **Negative capabilities** (e.g., "does not support UDP" - absence of feature)
- **Performance/load characteristics** (e.g., "handles 10k requests/sec" - hard to test reliably)
- **Natural consequences** (e.g., OOM crashes, data loss on process kill)
- **OS/runtime behavior** (e.g., process termination on SIGKILL)

**Why?** Customers receive built executable from `./release/`. Requirements focus on what the delivered product does with correct usage, not exhaustive error testing.

---

## How to Write Requirements

### Step 1: Read All Documentation

Read thoroughly:
- `./README.md`
- All files in `./readme/`

Identify reasonably testable behaviors **of delivered software:**
- Actions users take with executable (with correct inputs)
- System responses (to valid requests)
- Observable outputs
- Error conditions **explicitly documented in README**
- Success criteria

**Skip sections about:**
- "Building from source"
- "Development prerequisites"
- Build/compilation instructions
- Limitations stated as absences ("doesn't support X")
- Performance/load claims ("handles 10k req/sec")
- What happens with wrong inputs (unless README documents it)

### Step 2: Identify User Flows

Group related behaviors into flows:
- Installation flow
- Startup flow
- Normal operation flow
- Error handling flow
- Shutdown flow
- Uninstallation flow

Each flow should be independently testable.

### Step 3: Write Flow Documents

For each flow:
1. **Create file:** `./reqs/flow-name.md`
2. **Add title:** Descriptive name
3. **Add source:** Reference README file
4. **Add description:** What this flow covers
5. **Add requirements:** One `$REQ_ID` per testable step

### Step 4: Write Each Requirement

For each requirement:
1. **ID:** Format is `$REQ_` followed by any combination of letters, digits, underscores, hyphens. Must be unique across all files. Pretty examples: `$REQ_STARTUP_001`, `$REQ_LOGGING_002`
2. **Title:** Short description
3. **Source:** Cite README file and section
4. **Description:** Clear, testable statement

**Make each requirement:**
- Observable (can be verified by test)
- Specific enough to test
- Not over-specified
- Traceable to source
- **Focused on happy paths** (correct usage, not wrong inputs)

---

## Critical Distinctions

**Happy paths vs. error exhaustion:**
- ✓ "Accepts one directory argument" → this IS a requirement (describes correct usage)
- ✗ "Exit with error if two directories provided" → skip unless README explicitly documents this
- ✓ "Port number is required" → this IS a requirement (describes correct usage)
- ✗ "Show error if port missing" → skip unless README explicitly documents this error

**Capabilities vs. absences:**
- ✓ "Proxies TCP connections" → this IS a requirement (what it does)
- ✗ "Does not support UDP" → skip (absence of feature, nothing to test)
- ✓ "Returns error 'UDP not supported' if UDP attempted" → this IS a requirement IF README documents it

**Architectural constraints vs. natural consequences:**
- ✓ "Never block network I/O on disk writes" → this IS a requirement (architectural constraint)
- ✗ "Will crash with OOM instead of blocking" → skip (natural consequence, not a feature)
- ✓ "Buffer in memory when logging falls behind" → this IS a requirement (what system does)

**Explicit error handling vs. implied validation:**
- ✓ README says "If config file missing, exit with error 'CONFIG_NOT_FOUND'" → this IS a requirement
- ✗ README says "Requires config file" without mentioning error → skip the error behavior

---

## Over-Specification Examples

**Over-specified (WRONG):**
- README: "On startup, if config file is missing, show error and exit"
- REQ: "Print `ERROR: CONFIG_NOT_FOUND` to STDERR with exit code -3 and log to Windows Event Viewer"
- **Problem:** Exact message, stream, exit code, and Event Viewer logging not in README

**Correctly specified (RIGHT):**
- README: "On startup, if config file is missing, show error and exit"
- REQ: "Show error message if config file is missing at startup and exit"

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
- Specific exit codes (unless specified or necessary)
- Wrong input handling (unless specified)
- Edge case behavior (unless specified)

---

## File Naming

Use descriptive, lowercase names with hyphens:
- `install.md`
- `startup-to-shutdown.md`
- `client-usage.md`
- `error-handling.md`
- `uninstall.md`

---

## Output

Report when done:
- Number of README files processed
- Number of flow files created
- List of flow files
- Brief description of each flow
