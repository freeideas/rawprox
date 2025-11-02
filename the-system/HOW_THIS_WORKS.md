# How This Works

Transform use-case README documents into working, tested software.

---

## Overview

**Human writes** use-case documentation → **AI generates** testable flows → **Human reviews** flows → **AI implements** code and tests until complete.

**Human runs two Python scripts:**

1. `./the-system/scripts/reqs-gen.py` -- Invokes AI to generate flows from documentation
2. `./the-system/scripts/software-construction.py` -- Invokes AI to build software from flows

These scripts keep the AI context window laser-focused on one task at a time and iterate automatically until completion.

**Prerequisites: The task watcher must be running:**

```bash
uv run --script ./the-system/scripts/task_watcher.py
```

Leave this running in a separate terminal. It processes the work queue that the scripts below create.

---

## Phase 1: Human Writes Documentation

**Human creates:**

1. **README.md** -- Project overview, what the software does
2. **./readme/*.md files** -- Use-case oriented documentation

### Examples of Use-Case Files

**Web server:**
- `README.md` -- Normal overview similar to most README files
- `./readme/LIFECYCLE.md` -- Start, stop, environment needs
- `./readme/DEVELOPER.md` -- Serving HTML and APIs
- `./readme/CLIENT.md` -- Browser and curl usage
- `./readme/DEPLOYMENT.md` -- Production deployment

**CLI tool:**
- `README.md` -- Normal overview similar to most README files
- `./readme/INSTALLATION.md` -- Installation process
- `./readme/BASIC_USAGE.md` -- Common workflows
- `./readme/ADVANCED.md` -- Power user features

**Principle:** Each file tells a story from someone's perspective (user, developer, operator, etc.).

---

## Phase 2: AI Generates Flows

**Human runs:** `uv run --script ./the-system/scripts/reqs-gen.py`

The script prompts AI to write requirements, tests them, and iterates until flows pass validation.

**Three possible outcomes:**
1. **GOODENUF** -- Flows are valid, proceed to Phase 3
2. **NEEDIMPROV** -- Script loops to revise flows automatically
3. **READMEBUG** -- Script exits, requesting human to improve README documentation and re-run

**Note:** The script often identifies issues where README documentation states constraints without specifying testable behavior (e.g., "port number is required" without saying what happens when missing). When this occurs, revise the README files to be more specific about observable behavior, then re-run the script.

**AI processes** each README file into testable flows in `./reqs/`.

### What Is a Flow?

A flow is a **sequence of steps from application start to shutdown** that can be tested end-to-end.

**Example:**

`./readme/LIFECYCLE.md` generates:
- `./reqs/install.md` -- Install to ready state
- `./reqs/startup-to-shutdown.md` -- Start server, use it, stop it
- `./reqs/uninstall.md` -- Remove from system

### Flow Format

```markdown
# Server Startup Flow

**Source:** ./readme/LIFECYCLE.md

This flow runs from app start to shutdown.

## $REQ_STARTUP_001: Launch Process
**Source:** ./readme/LIFECYCLE.md (Section: "Starting the Server")

Start the server executable with default configuration.

## $REQ_STARTUP_002: Listen on Port
**Source:** ./readme/LIFECYCLE.md (Section: "Network Binding")

Server must bind to configured port.

## $REQ_STARTUP_003: Log Ready Message
**Source:** ./readme/LIFECYCLE.md (Section: "Startup Logging")

Server must log when ready to accept connections.

## $REQ_STARTUP_004: Health Check Response
**Source:** ./readme/LIFECYCLE.md (Section: "Health Monitoring")

GET /health must return 200 OK.
```

### Flow Requirements

**Each flow:**
- Has descriptive title
- References source README with `**Source:** ./readme/FILENAME.md (Section)`
- Describes what the flow covers (start to end scenario)
- Breaks into steps, each with unique `$REQ_ID`
- Uses descriptive `$REQ_ID` names (e.g., `$REQ_STARTUP_001` not `$REQ_001`)

**Each step:**
- Has unique `$REQ_ID` starting with `$REQ_` followed by letters, digits, underscores, or hyphens (e.g., `$REQ_STARTUP_001`, `$REQ_X`, `$REQ_foo-bar_123`)
- Includes source attribution: `**Source:** ./readme/FILE.md (Section: "Section Name")`
- Is testable (observable, verifiable)
- Follows sequence from start to shutdown
- Is clear and specific without over-specifying

---

## Phase 3: Human Reviews and Iterates

**Human:**

1. **Reads generated flows** in `./reqs/`
2. **Checks if they match intent** -- Do they capture all use cases correctly?
3. **If needed, adjusts `./readme/` documentation** to clarify or add details
4. **Re-runs `reqs-gen.py`** to regenerate flows
5. **Repeats until flows are correct**

**The flows in `./reqs/` are what will be tested and implemented, so they must be right.**

---

## Phase 4: AI Builds the Software

**Human runs:** `uv run --script ./the-system/scripts/software-construction.py`

The script iterates through writing/revising tests, writing code, and running tests until all tests pass.

**AI operates** the work queue until all tests pass.

### How It Works

The `software-construction.py` script:

1. Creates `./tests/build.py` if missing
2. Removes orphan `$REQ_ID` tags
3. Writes tests for all untested requirements
4. Orders tests from general/foundational to specific/advanced using numeric prefixes
5. Runs tests in order and fixes code until all tests pass with no changes needed

**Note:** Duplicate `$REQ_ID` tags are automatically fixed by `reqs-gen.py`.

**Test ordering:**
Tests are kept ordered from most general to most specific using numeric prefixes (00, 01, 02, etc.). This ensures foundational tests (build, startup) pass before feature tests run.

**One flow = One test file:**
```
./reqs/startup.md → ./tests/test_01_startup.py
```

Tests execute the flow from start to shutdown, verify each `$REQ_ID` step with assertions, and tag each assertion with `# $REQ_ID` for traceability.

---

## Test Execution

**Run tests with:**
```bash
uv run --script ./the-system/scripts/test.py              # Run failing tests by default
uv run --script ./the-system/scripts/test.py --failing    # Explicit failing tests
uv run --script ./the-system/scripts/test.py --passing    # Run passing tests
```

**Test script:**
1. Runs `./tests/build.py` first (compiles/packages code)
2. Runs specified tests
3. Shows results

---

## Traceability

**All `$REQ_ID` tags are indexed** to track:
- **What** -- Requirement text
- **Why** -- Source README reference
- **Test** -- Which test verifies it
- **Code** -- Where it's implemented

**Query any requirement:**
```bash
uv run --script ./the-system/scripts/reqtrace.py $REQ_STARTUP_002
```

**Output:**
```
$REQ_STARTUP_002: Listen on Port
Source: ./readme/LIFECYCLE.md
Flow: ./reqs/startup.md
Test: ./tests/passing/test_startup.py:42
Code: ./code/server.cs:156, ./code/network.cs:89
```

---

## Directory Structure

```
./readme/                       Use-case documentation (human writes)
./reqs/                         Flows (AI generates from readme)
./tests/
  build.py                      Build script (AI creates)
  failing/                      Tests not passing yet (AI works here)
  passing/                      All tests passing (AI moves tests here)
./code/                         Implementation (AI writes)
./release/                      Build outputs (from build.py)
./the-system/
  scripts/                      System automation scripts
    reqs-gen.py                 Generate flows from READMEs
    fix-unique-req-ids.py       Auto-fix duplicate REQ_IDs
    build-req-index.py          Build requirements database index
    prompt_agentic_coder.py     Wrapper for AI agent (edit to swap agents)
    software-construction.py    Build software from flows (includes work queue)
    test.py                     Run tests with build step
    reqtrace.py                 Trace requirements to code/tests
  prompts/                      AI prompts used by scripts
    WRITE_REQS.md               Flow generation instructions
    check_req-contradictions.md Check for contradictory requirements
    check_req-testability.md    Check for untestable constraints
    check_req-coverage.md       Check for complete coverage
    check_req-overspec.md       Check for over-specification
    check_req-sources.md        Check for source attribution
    check_req-flow-structure.md Check for proper flow structure
    WORK_QUEUE.md               Construction instructions
    PHILOSOPHY.md               Project philosophy
```

---

## Benefits

- **Clear division** -- Human writes use cases, AI does implementation
- **Iterative** -- Human reviews flows before implementation starts
- **Traceable** -- Every requirement links to test and code
- **Testable** -- Flows are executable, not abstract
- **Flexible** -- Code can be refactored freely while tests pass
- **Use-case driven** -- Organized how users think
- **Automated workflow** -- Scripts manage AI context and iteration
- **Small context windows** -- Each AI invocation focuses on one task, avoiding brain-fog

---

## Key Principles

- **One flow = One test file**
- **Tests ordered general to specific** -- numeric prefixes ensure proper execution order
- **Code is flexible** -- refactor freely while tests pass
- **All `$REQ_ID` tags must be unique** across all flows
- **Every `$REQ_ID` must have a test** that verifies it
- **Software is done when** all tests pass with no changes needed
- **Scripts drive AI** -- keeping context focused and iterating automatically
