# How to Build Software with This System

This system transforms README documents into working, fully tested software through AI-assisted, requirement-driven, and test-driven development, all while keeping context windows small enough to avoid ai brain-fog. This is the intersection of context engineering, spec driven development, and test driven development. This gives you ability to write medium- to large-scale enterprise-ready software, repeatably and predictably, but with most of the ease of vibe-coding.

CONTEXT-ENGINEERING: Necessary, but much more is needed to give the AI direction.

SPEC-DRIVEN DEVELOPMENT: Necessary, but not enough, because the AI can read perfect specs and still write the wrong code.

TEST-DRIVEN DEVELOPMENT: Necessary, but not enough, because if the AI can write or modify the tests, it will over-test things that don't matter, avoid testing critical features, and it will artificially make the tests pass. But if the AI CAN'T write and modify the tests, then test writing becomes a giant project for humans.

This system uses specs to write and rewrite tests, frequently verifies the tests against the specs, then uses spec-driven development AND test-driven development, all while keeping contexts laser focus on small job at a time.
---

## Overview

You write documentation describing the software you want to build.
AI does everything else.

---

## Step 1: Write Your Documentation

Create use-case oriented documentation files:

1. **README.md** -- Project overview, what the software does, and what should be in the ./release/ directory.
2. **./readme/*.md files** -- One file per use case or user perspective or user flow.

Hypothetical Example for a web server that implements a math-oriented SOAP API:

-- README.md
-- ./readme/API.md
-- ./readme/STARTUP-and-SHUTDOWN.md
-- ./readme/ENDPOINT_TRIGONOMETRY.md
-- ./readme/ENDPOINT_3D-CALCULUS.md

Describe the software you want to create. Include technical details ONLY as needed. For example, if it doesn't matter whether React or Vue or Svelte or Flutter is used for the UI, then don't specify. You might want to say C# or Go or Java or Rust, in case you want to read the code or need a certain platform or performance profile, or interoperability.

## Step 2: Run ./the-system/scripts/reqs-gen.py (using `uv run --script`)

This script may exit with **READMEBUG** status, indicating that your README documentation has issues that prevent testable requirements from being written. When this happens:
1. Read the latest report in ./reports/ to understand the specific issues
2. Revise the README documentation to correct the problem
3. Re-run the script

Common issue: README says "X is required" but doesn't say what happens when X is missing (error message? default value? ignore?).

## Step 3: Briefly look at the documents generated under ./reqs/ then consider revising README documents and repeat

## Step 4: When the ./reqs/ documents look correct, run ./the-system/scripts/software-construction.py 

## Step 5: As the ai does its work, watch the ./reports/ directory; consider stopping it, revising ./readme/ documents and working back to this step.

## WHEN BUGS ESCAPE DETECTION:

-- write ./reports/BUG_REPORT.md
-- run ./report-a-bug.py

## PREREQUISITES:

1. The small and fast and zero-config `uv` is installed for running python scripts. This allows the ai to run python scripts without worrying about dependencies.
   -- `winget install --id=astral-sh.uv -e` or `pip install uv` or `brew install uv`, etc.

2. An agentic coder that can be called from the command-line. The system uses `./the-system/scripts/prompt_agentic_coder.py` as a wrapper to call your AI agent. By default, it calls `agentic-coder.bat -p "prompt text"`. To use a different AI agent (Claude Code, Aider, Codex, Gemini-CLI, etc.), edit the `COMMAND` variable at the top of `./the-system/scripts/prompt_agentic_coder.py`.

3. The task watcher must be running before you start:
   -- `uv run --script ./the-system/scripts/task_watcher.py`
   -- This processes work queue tasks asynchronously
   -- Leave it running in a separate terminal throughout your work session
