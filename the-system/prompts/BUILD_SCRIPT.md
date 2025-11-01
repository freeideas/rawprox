# BUILD_SCRIPT.md -- Create Build Script

You are an AI assistant tasked with creating a build script for this project.

---

## Your Task

Create `./tests/build.py` that compiles/packages the code and puts build artifacts in `./release/`.

---

## Instructions

### Step 1: Read README.md

Read `./README.md` to understand:
1. What programming language(s) the project uses
2. How to build/compile the code
3. What files should be produced in `./release/`

### Step 2: Check if README has Sufficient Information

The README.md **must** specify:
- **Programming language(s)** to use (e.g., Python, C#, Go, Rust, etc.)
- **Build process** (what commands to run, what tools to use)
- **Build artifacts** (what files should be in `./release/` after building)

**If README.md does not contain enough information:**
- Respond with exactly: `INSUFFICIENT_BUILD_INFO`
- Follow with a bulleted list of what's missing
- Do NOT create the build script
- Exit

**Example insufficient response:**
```
INSUFFICIENT_BUILD_INFO

README.md is missing:
- Programming language not specified
- Build process not documented
- Expected build artifacts not listed
```

### Step 3: Create ./tests/build.py

If README.md has sufficient information, create `./tests/build.py` with this structure:

```python
#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   # Add any packages needed for build process
# ]
# ///

import sys
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import os
import subprocess
from pathlib import Path

# Change to project root
script_dir = Path(__file__).parent
project_root = script_dir.parent
os.chdir(project_root)

def main():
    print("Building project...")

    # Create release directory
    os.makedirs('./release', exist_ok=True)

    # TODO: Add build commands here based on README.md
    # Examples:
    #   - Python: Copy .py files, create executable with PyInstaller
    #   - C#: Run dotnet build, copy exe to ./release/
    #   - Go: Run go build, copy binary to ./release/
    #   - Rust: Run cargo build --release, copy binary to ./release/

    print("✓ Build complete")
    print("Artifacts in ./release/")
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

**Requirements for ./tests/build.py:**
- Must have the uvrun shebang and script metadata block
- Must create `./release/` directory
- Must compile/package the code according to README.md
- Must put all build artifacts in `./release/`
- Must exit with code 0 on success
- Must exit with non-zero code on failure
- Must be executable with: `uv run --script ./tests/build.py`

---

## Important Notes

- **Do NOT guess or infer build details** -- if README.md doesn't specify, respond with `INSUFFICIENT_BUILD_INFO`
- **Follow README.md exactly** -- use the language, tools, and process it specifies
- **Keep build.py simple** -- just compile and copy artifacts to ./release/
- **Test the build script** -- make sure it actually runs and produces expected output

---

## Examples

### Example 1: C# Console Application

README.md says:
```
This is a C# console application. Build with 'dotnet build -c Release' and copy the exe from bin/Release/ to ./release/
```

Your build.py should:
```python
# Run: dotnet build -c Release ./code/MyApp.csproj
# Find and copy the .exe from ./code/bin/Release/net8.0/MyApp.exe to ./release/MyApp.exe
```

### Example 2: C# Web API Service

README.md says:
```
This is a C# ASP.NET Core Web API. Build with 'dotnet publish -c Release' and copy the published output to ./release/
```

Your build.py should:
```python
# Run: dotnet publish -c Release -o ./publish ./code/WebApi.csproj
# Copy all files from ./publish/ to ./release/
```

### Example 3: C# Class Library with Dependencies

README.md says:
```
This is a C# class library. Build with 'dotnet build -c Release' and copy the DLL and all dependencies to ./release/
```

Your build.py should:
```python
# Run: dotnet build -c Release ./code/MyLibrary.csproj
# Copy ./code/bin/Release/net8.0/*.dll to ./release/
# Copy ./code/bin/Release/net8.0/*.json to ./release/ (if any config files)
```

---

## Summary

1. Read README.md
2. If insufficient info, respond with `INSUFFICIENT_BUILD_INFO` + list
3. If sufficient, create ./tests/build.py that builds and populates ./release/
4. Make sure build.py is runnable with `uv run --script ./tests/build.py`
