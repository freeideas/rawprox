# How to Build Software with This System

Transform README documentation into working, tested software through two AI-driven phases.

---

## Prerequisites

1. **Install `uv`** (Python script runner)
   - `winget install --id=astral-sh.uv -e` or `pip install uv` or `brew install uv`

2. **Configure your AI agent**
   - Edit `./the-system/scripts/prompt_agentic_coder.py`
   - Set the command for your AI agent (Claude Code, Aider, etc.)

---

## Phase 1: Requirements Generation

**Goal:** Transform your README documentation into testable requirement flows.

### Step 1: Write Documentation

Create use-case oriented documentation:
- `README.md` -- Project overview, what the software does
- `./readme/*.md` -- One file per use case, user perspective, or workflow

**Example for a web server:**
- `README.md` -- Overview and what goes in `./release/`
- `./readme/STARTUP.md` -- Starting and stopping the server
- `./readme/API.md` -- API endpoints and responses
- `./readme/DEPLOYMENT.md` -- Production deployment

### Step 2: Generate Flows

```bash
uv run --script ./the-system/scripts/reqs-gen.py
```

The AI reads your documentation and generates testable requirement flows in `./reqs/`.

**Common issues:** If the script reports problems (READMEBUG status), it means your README documentation needs clarification. For example, if you say "port number is required" but don't specify what happens when it's missing (error? default? ignore?), the AI can't write testable requirements.

**Performance and load testing:** This system tests functional behavior, not performance characteristics. Write "must handle multiple connections" (testable), not "must handle 10,000 connections" (not reliably testable). Specific throughput numbers, latency requirements, and load testing are out of scope.

### Step 3: Review and Iterate

1. Read the generated flows in `./reqs/`
2. Check if they match your intent
3. **If changes needed:** Revise `./readme/` documentation and re-run `reqs-gen.py`
4. Repeat until the flows correctly capture all use cases

**Important:** The flows in `./reqs/` are what gets implemented and tested, so they must be right before proceeding to Phase 2.

---

## Phase 2: Software Construction

**Goal:** Build and test software from the requirement flows.

### Step 4: Build Software

```bash
uv run --script ./the-system/scripts/software-construction.py
```

The AI automatically:
1. Creates a build script (`./tests/build.py`)
2. Writes tests for all requirements
3. Implements code to pass the tests
4. Fixes failures until all tests pass

The script runs iteratively -- it will keep working until all tests pass with no changes needed.

### Step 5: Monitor Progress

Watch `./reports/` directory for AI activity reports. If you see problems or want to change requirements:
1. Stop the construction script (Ctrl+C)
2. Revise `./readme/` documentation
3. Re-run `reqs-gen.py` to regenerate flows
4. Re-run `software-construction.py` to continue building

---

## Summary

Two phases, both with human oversight:

1. **Requirements Generation** -- Write/revise READMEs → AI generates flows → Review flows → Iterate until correct
2. **Software Construction** -- AI writes tests and code → Runs tests → Fixes failures → Done when all tests pass

Any change to README documentation requires re-running `reqs-gen.py`.

---

## When Bugs Escape Detection

If you find bugs after construction completes:
1. Write `./reports/BUG_REPORT.md` describing the issue
2. Update `./readme/` to clarify expected behavior
3. Re-run `reqs-gen.py` to regenerate flows
4. Re-run `software-construction.py` to fix the bug

---

## Need More Detail?

See `@the-system/HOW_THIS_WORKS.md` for detailed explanation of flows, tests, and traceability.
