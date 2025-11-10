# Write Build Artifacts Validation Test

Create a test that validates ./release/ contains exactly what the documentation specifies.

---

## Your Task

### Step 1: Read Documentation

Read all documentation to understand what should be in `./release/`:
- Read `./README.md`
- Read all files in `./readme/`
- Look for statements about:
  - What files should be in ./release/
  - Build output expectations
  - Deployment artifacts
  - Dependencies or lack thereof
  - Single executable vs multiple files

### Step 2: Write a Simple Python Test

Create `./tests/failing/test_00_build_artifacts.py` that:
- Lists all files in ./release/ directory
- Asserts expected files are present
- Asserts no unexpected files exist
- Uses clear assertion messages that explain what's wrong

**IMPORTANT: This must be a simple, fast Python test -- NOT a test that calls AI agents!**

The test should:
- Run in under a second
- Use plain Python file operations (Path, os.listdir, etc.)
- Have clear, readable assertions
- Print helpful error messages when it fails

**Test structure:**
```python
#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Build Artifacts Validation Test

IMPORTANT: Before modifying this test, read:
- ./README.md
- All files in ./readme/

This test validates that ./tests/build.py produces exactly
the artifacts specified in the documentation.

If this test fails, the problem is likely in ./tests/build.py
-- it's not building what the documentation specifies.
The documentation is the source of truth.

To regenerate this test (if documentation changes):
  Run: ./the-system/scripts/software-construction.py
  (This will regenerate the test based on current documentation)
"""

import sys
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path

def main():
    release_dir = Path('./release')

    # List what's actually in ./release/
    actual_files = set()
    if release_dir.exists():
        for item in release_dir.iterdir():
            if item.is_file():
                actual_files.add(item.name)

    # Define expected files based on documentation
    expected_files = {
        # Fill this in based on what you read in README.md and ./readme/
        'file1.exe',
        'file2.py',
        # etc.
    }

    # Check for missing files
    missing = expected_files - actual_files
    if missing:
        print(f"ERROR: Missing files in ./release/:")
        for f in sorted(missing):
            print(f"  - {f}")
        return 1

    # Check for unexpected files
    unexpected = actual_files - expected_files
    if unexpected:
        print(f"ERROR: Unexpected files in ./release/:")
        for f in sorted(unexpected):
            print(f"  - {f}")
        return 1

    print("Build artifacts validation: PASS")
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

### Step 3: Customize the Test

Replace the `expected_files` set with the actual files you found in the documentation.

Make sure the error messages clearly explain:
- What was expected (based on documentation)
- What was found (actual files)
- Where to look (./README.md and ./readme/)

---

## Important Notes

- **The test should NOT call AI agents** -- it should be a simple Python script
- **Documentation is the source of truth** -- the test validates that build.py produces what documentation says
- **Be specific** -- list exact filenames, not patterns (unless documentation specifies wildcards)
- **Consider subdirectories** -- if documentation says files should be in subdirectories under ./release/, check for those

---

## Output

Write the test file to `./tests/failing/test_00_build_artifacts.py` and report what you created.
