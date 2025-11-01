# Check Build Artifacts Against Documentation

Verify that the `./release/` directory contains exactly the files specified in the documentation, and nothing more.

---

## Your Task

1. **Read documentation** to understand what should be in `./release/`:
   - Read `./README.md`
   - Read all files in `./readme/`
   - Look for any statements about:
     - What files should be in ./release/
     - Build output expectations
     - Deployment artifacts
     - Dependencies or lack thereof
     - Single executable vs multiple files

2. **Check actual build output**:
   - List all files in `./release/`
   - Compare against documentation expectations

3. **Report findings**:
   - What documentation says should be in ./release/
   - What is actually in ./release/
   - Whether they match
   - If mismatch: what's missing or what shouldn't be there

---

## Success Criteria

The build artifacts match documentation if:
- All expected files are present
- No unexpected files are present
- File types match documentation (e.g., single .exe vs .dll + .exe)
- Dependencies match documentation (e.g., "no dependencies" means no .dll/.deps.json/.runtimeconfig.json)

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process.

Include:
1. What documentation specifies for ./release/
2. What is actually in ./release/
3. Whether they match

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `PASS` -- Build artifacts match documentation perfectly
- `FAIL` -- Mismatch detected (missing files or extra files)

**IMPORTANT:** If there's a mismatch, the problem is almost always in `./tests/build.py` -- it's not building what the documentation specifies. The documentation is the source of truth.
