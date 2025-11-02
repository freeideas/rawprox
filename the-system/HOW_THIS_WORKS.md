# How This Works

Transform use-case README documents into working, tested software through two AI-driven phases.

---

## Overview

This system automates software construction through two distinct phases:

1. **Requirements Generation** -- Human writes/revises README docs → AI generates testable flows → Human reviews → Iterate until flows are correct
2. **Software Construction** -- AI writes tests and code → Runs tests → Fixes failures → Repeats until all tests pass

**Key principle:** Human provides oversight at both phases. Any change to README documentation requires re-running the requirements generation phase.

---

## Prerequisites

**Task watcher must be running:**

```bash
uv run --script ./the-system/scripts/task_watcher.py
```

Leave this running in a separate terminal. All AI invocations are processed through this work queue system.

---

## Phase 1: Requirements Generation

### Human Writes Documentation

Create use-case oriented documentation:

1. **README.md** -- Project overview, what the software does, what goes in `./release/`
2. **./readme/*.md** -- One file per use case, user perspective, or workflow

**Examples:**

**Web server:**
- `README.md` -- Overview
- `./readme/LIFECYCLE.md` -- Start, stop, environment
- `./readme/API.md` -- Endpoints and responses
- `./readme/DEPLOYMENT.md` -- Production deployment

**CLI tool:**
- `README.md` -- Overview
- `./readme/INSTALLATION.md` -- Installation process
- `./readme/BASIC_USAGE.md` -- Common workflows
- `./readme/ADVANCED.md` -- Power user features

**Principle:** Each file tells a story from someone's perspective (user, developer, operator).

### AI Generates Flows

**Run:** `uv run --script ./the-system/scripts/reqs-gen.py`

The script:
1. Reads all README documentation
2. Generates testable requirement flows in `./reqs/`
3. Validates flows for completeness, testability, and consistency
4. Iterates automatically until flows pass validation

**Possible outcomes:**
- **Success** -- Flows are valid, ready for Phase 2
- **Auto-iteration** -- Script detects fixable issues and corrects them automatically
- **README issues** -- Script exits, requesting human to clarify README and re-run

**Common README issue:** Stating constraints without specifying observable behavior. For example, "port number is required" without saying what happens when missing (error message? default value? crash?).

### What Is a Flow?

A flow is a **sequence of steps from application start to shutdown** that can be tested end-to-end.

**Example:** `./readme/LIFECYCLE.md` generates:
- `./reqs/install.md` -- Install to ready state
- `./reqs/startup-to-shutdown.md` -- Start server, use it, stop it
- `./reqs/uninstall.md` -- Remove from system

### Flow Format

Each flow breaks into testable steps identified by unique `$REQ_ID` tags:

```markdown
# Server Startup Flow

**Source:** ./readme/LIFECYCLE.md

Start server, verify ready, shut down cleanly.

## $REQ_STARTUP_001: Launch Process
**Source:** ./readme/LIFECYCLE.md (Section: "Starting the Server")

Start the server executable with default configuration.

## $REQ_STARTUP_002: Bind to Port
**Source:** ./readme/LIFECYCLE.md (Section: "Network Binding")

Server must bind to configured port.

## $REQ_STARTUP_003: Log Ready Message
**Source:** ./readme/LIFECYCLE.md (Section: "Startup Logging")

Server must log when ready to accept connections.

## $REQ_STARTUP_004: Shutdown Cleanly
**Source:** ./readme/LIFECYCLE.md (Section: "Stopping")

Server must exit gracefully when receiving SIGTERM.
```

**Flow requirements:**
- Descriptive title
- Source attribution to README
- Testable steps with unique `$REQ_ID` tags
- Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., `$REQ_STARTUP_001`)
- Each step cites source: `**Source:** ./readme/FILE.md (Section: "Name")`

### Human Reviews and Iterates

1. Read generated flows in `./reqs/`
2. Verify they match your intent
3. **If changes needed:** Revise `./readme/` documentation and re-run `reqs-gen.py`
4. Repeat until flows correctly capture all use cases

**The flows in `./reqs/` are what will be implemented and tested, so they must be right before proceeding to Phase 2.**

---

## Phase 2: Software Construction

### AI Builds the Software

**Run:** `uv run --script ./the-system/scripts/software-construction.py`

The script automates the build/test/fix cycle:

**Setup phase (runs once):**
1. Creates `./tests/build.py` (compiles/packages code)
2. Removes orphan `$REQ_ID` tags from old code
3. Writes tests for all requirements (one flow = one test file)
4. Orders tests from foundational to advanced (numeric prefixes)

**Iteration phase (repeats until done):**
1. Runs all tests in order
2. For each failure, AI fixes code and re-runs
3. When all tests pass individually, re-runs entire suite to check for regressions
4. Done when all tests pass with no changes needed

**Note:** The system uses multiple iterations because fixing one test can break another. Tests are moved back to `./tests/failing/` after any failure to ensure nothing regresses.

### Test Structure

**One flow = One test file:**
```
./reqs/startup.md → ./tests/test_01_startup.py
./reqs/api.md → ./tests/test_02_api.py
```

**Test ordering:** Numeric prefixes ensure tests run from general to specific:
- `00-XX`: Build/installation
- `01-XX`: Startup/lifecycle
- `02-XX`: Core functionality
- `03-XX`: Advanced features

**Test implementation:**
- Standalone Python scripts (not pytest)
- Execute complete flow from start to shutdown
- Tag each assertion with `# $REQ_ID` for traceability
- Clean up in `finally` block (no leaked processes/resources)

### Human Monitors Progress

Watch `./reports/` for AI activity. If you see issues or want to change requirements:
1. Stop construction (Ctrl+C)
2. Revise `./readme/` documentation
3. Re-run `reqs-gen.py` to regenerate flows
4. Re-run `software-construction.py` to rebuild

---

## Running Tests Manually

**Run tests with:**
```bash
uv run --script ./the-system/scripts/test.py              # Failing tests (default)
uv run --script ./the-system/scripts/test.py --passing    # Passing tests
uv run --script ./the-system/scripts/test.py <file>       # Specific test
```

The test script:
1. Runs `./tests/build.py` first (compiles code)
2. Runs specified tests
3. Shows results

---

## Traceability

All `$REQ_ID` tags are indexed in a SQLite database (`./tmp/reqs.sqlite`). This tracks:
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
$REQ_STARTUP_002: Bind to Port
Source: ./readme/LIFECYCLE.md (Section: "Network Binding")
Flow: ./reqs/startup.md
Test: ./tests/passing/test_01_startup.py:42
Code: ./code/server.cs:156, ./code/network.cs:89
```

---

## Directory Structure

```
./readme/                       Use-case documentation (human writes)
./reqs/                         Testable flows (AI generates)
./tests/
  build.py                      Build script (AI creates)
  failing/                      Tests not passing yet
  passing/                      Tests that pass
./code/                         Implementation (AI writes)
./release/                      Build outputs (from build.py)
./reports/                      AI activity reports (timestamped)
./tmp/                          Requirements database
./workQ/                        Task queue for AI invocations
./the-system/
  scripts/
    reqs-gen.py                 Generate flows from READMEs
    software-construction.py    Build software from flows
    task_watcher.py             Process work queue tasks
    prompt_agentic_coder.py     Wrapper for AI agent
    test.py                     Run tests with build step
    reqtrace.py                 Trace requirements to tests/code
    build-req-index.py          Build traceability database
    fix-unique-req-ids.py       Auto-fix duplicate $REQ_IDs
  prompts/
    WRITE_REQS.md               Flow generation instructions
    req-fix_*.md                Validation and fix prompts
    BUILD_SCRIPT.md             Build script creation
    WRITE_TEST.md               Test writing instructions
    FIX_FAILING_TEST.md         Test failure fixing
    ORDER_TESTS.md              Test ordering by dependency
    REMOVE_ORPHAN_REQS.md       Orphan tag cleanup
    PHILOSOPHY.md               Project philosophy
```

---

## Key Principles

- **Two phases, both with human oversight** -- Requirements generation and software construction
- **One flow = One test file** -- Complete use-case scenarios
- **Tests ordered general to specific** -- Foundational before advanced
- **Code is flexible** -- Refactor freely while tests pass
- **All `$REQ_ID` tags must be unique** across all flows
- **Every `$REQ_ID` must have a test** that verifies it
- **Software is done when** all tests pass with no changes needed
- **Any README change requires** re-running `reqs-gen.py`
- **Performance/load testing is out of scope** -- Test functional capabilities (e.g., "handles multiple connections"), not performance characteristics (e.g., "handles 10,000 connections per second"). Specific throughput, latency, and scale requirements may be documented but won't have automated tests.

---

## Benefits

- **Clear separation** -- Human defines what, AI implements how
- **Iterative with oversight** -- Human reviews flows before implementation
- **Fully traceable** -- Every requirement links to source, test, and code
- **Testable by design** -- Flows are executable scenarios, not abstract documents
- **Flexible implementation** -- Code can be refactored freely while tests pass
- **Use-case driven** -- Organized how users think, not how code is structured
- **Small AI context windows** -- Each invocation focuses on one task, avoiding brain-fog
- **Automated iteration** -- Scripts manage AI context and loop until done
