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

### Work Queue Priority Order

The `software-construction.py` script processes work items in this priority order:

1. **missing_build_script** -- Create `./tests/build.py` (blocks all other work)
2. **orphan_req_id** -- Remove `$REQ_ID` tags in tests/code that aren't in `./reqs/`
3. **untested_req** -- Write test for `$REQ_ID` that has no test coverage
4. **failing_test** -- Fix code until test passes
5. **final_verification** -- Run all passing tests when no other work items remain

**Note:** Duplicate `$REQ_ID` tags are automatically fixed by `reqs-gen.py`, so they don't appear in the work queue.

**AI works down the queue systematically until all tests pass.**

### Work Item Processing

#### 1. missing_build_script

**AI creates:** `./tests/build.py`

This script must:
- Compile/package the code
- Put build artifacts in `./release/`
- Exit with code 0 on success, non-zero on failure
- Be runnable with: `uv run --script ./tests/build.py`

#### 2. orphan_req_id

**AI fixes:** `$REQ_ID` exists in tests or code but not in `./reqs/`

- Removes orphan `$REQ_ID` tags from tests and code
- Updates tests to only verify requirements that exist in `./reqs/`

#### 3. untested_req

**AI creates test:** `$REQ_ID` in `./reqs/` has no test coverage

1. Identifies which flow the `$REQ_ID` belongs to
2. Creates test file in `./tests/failing/` for that flow (if it doesn't exist)
   - Name: `test_FLOWNAME.py` (e.g., `test_startup.py` for `startup.md`)
3. Implements test that verifies all `$REQ_ID` steps in the flow in order
4. **IMPORTANT:** Tests must be careful to not leave app running

**One flow = One test file:**

```
./reqs/startup.md → ./tests/failing/test_startup.py (initially)
                 → ./tests/passing/test_startup.py (when passing)
```

**Test structure:**
- Executes the flow from start to shutdown
- Verifies each `$REQ_ID` step with assertions
- Tags each assertion with comment: `# $REQ_ID`
- Starts in `./tests/failing/`
- Moves to `./tests/passing/` when all assertions pass
- **IMPORTANT:** Tests must be careful to not leave app running

#### 4. failing_test

**AI fixes code:** Test in `./tests/failing/` is not passing

**Note:** Infrastructure tests (`_test_*.py`) are processed before requirement tests (`test_*.py`) because they validate build output that other tests depend on.

1. Runs the test with `uv run --script ./the-system/scripts/test.py`
2. Reads the failure output
3. Implements or fixes code in `./code/` to make test pass
4. Implements or fixes code in `./the-system/scripts/test.py` if the test runner is not valid
5. Runs test again until it passes
6. Moves to passing when all assertions pass:
   ```bash
   mv ./tests/failing/test_NAME.py ./tests/passing/
   ```

**Code structure:**
- Organize files however makes tests pass
- Code can be refactored freely as long as tests pass
- Frameworks and libraries can be changed
- Only requirement: tests must pass

#### 5. final_verification

**Automatic final check:** When no other work items remain, all passing tests run automatically

1. `software-construction.py` runs: `uv run --script ./the-system/scripts/test.py` (runs passing tests when no failing tests exist)
2. If all tests pass, construction is complete
3. If any fail, they indicate a regression that must be investigated

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

## Work Iteration Loop

The `software-construction.py` script iterates automatically:

1. Check for highest priority work item (build script → orphans → untested → failing tests)
2. Process the work item (create test, fix code, etc.)
3. Run tests: `uv run --script ./the-system/scripts/test.py`
4. Move passing tests to `./tests/passing/`
5. Repeat from step 1

**Software is complete when:**
- All `$REQ_ID` tags have tests
- All tests are in `./tests/passing/`
- No failing tests remain
- Final verification passes (all passing tests still pass)

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
- **Tests start in `./tests/failing/`**, move to `./tests/passing/` when done
- **Code is flexible** -- refactor freely while tests pass
- **Work the queue top to bottom** -- don't skip items
- **All `$REQ_ID` tags must be unique** across all flows
- **Every `$REQ_ID` must have a test** that verifies it
- **Software is done when** no failing tests remain and final verification passes
- **Scripts drive AI** -- keeping context focused and iterating automatically
