# BUILD_SCRIPT.md -- Create Build Script

Create `./tests/build.py` that compiles/packages the code and puts build artifacts in `./release/`.

---

## Project Philosophy

**Follow @the-system/prompts/PHILOSOPHY.md:**
- Build only what is explicitly required
- No "nice to have" features
- Keep it simple

---

## Instructions

Read `./README.md` to understand:
- Programming language(s)
- Build process
- Expected build artifacts in `./release/`

**If README.md does not specify the programming language:**
```
INSUFFICIENT_BUILD_INFO

README.md is missing:
- Programming language not specified
```

**If `./code/` is empty:**

1. Read `./README.md` and all `./readme/*.md` files
2. Implement a complete first attempt at the application in `./code/`
3. Use proper project structure for the language
4. This is best-effort -- TDD loop will catch gaps

**Create `./tests/build.py`:**

- Use uvrun shebang and script metadata
- Compile/package code according to README.md
- Put all build artifacts in `./release/`
- Exit 0 on success, non-zero on failure
- Executable with: `uv run --script ./tests/build.py`

**Test it:**

Run `uv run --script ./tests/build.py` and verify it works. Fix if needed.

**Report your work:**

Write a brief analysis report covering:
- What you created (files in ./code/ and ./tests/build.py)
- Build approach and any key decisions
- Test run results
- Final artifacts in ./release/

End with:
```
BUILD_SCRIPT_SUCCESS

Artifacts created: [list]
```
