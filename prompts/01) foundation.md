# Create Project from Foundation

Read `@FOUNDATION.md` and create the project skeleton:

## Files to Create

1. **README.md** — Project overview for all audiences
2. **SPECIFICATION.md** — Technical specification for experienced developers (assumes they've read README)
3. **./scripts/build.py** — Builds the project and outputs to `./release/`
4. **./scripts/test.py** — Runs build.py, then discovers and executes all `test_*.py` scripts in `./scripts/`. Each test validates the binary in `./release/`
5. **./release/** — Directory for final binaries

## Execution Model

Python scripts are run with `uv run --script`, not with `python` directly.

## Design Principles

- **Minimum viable scope**: Include only essential functionality
- **No speculative features**: Omit "nice-to-have" additions
- **Realistic edge cases only**: Cover edge cases only if they're likely in production
- **Natural error handling**: Accept default error behavior unless explicit handling is needed
- **No historical context**: Eliminate all traces of previous designs from documentation and code
- **Trust developer expertise**: Don't specify implementation details that experienced developers already know