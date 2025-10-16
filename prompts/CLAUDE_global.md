## Environment

- **GitHub**: Already logged in and authenticated
- **Git Branch Naming**: Always use "main" instead of "master" for default branch names, as some people find "master" offensive

### Shell Environment on Windows

**IMPORTANT: The default shell is Git Bash (MINGW64), NOT Windows Command Prompt or PowerShell:**

- **Shell Type**: Git Bash/MINGW64 (running Bash on Windows)
- **Path Format**: Use Unix-style paths (`/c/acex/prjx/` instead of `c:\acex\prjx\`)
- **Path Separators**: Use forward slashes `/` NOT backslashes `\`
- **Backslashes**: Are escape characters in Bash - avoid them in paths
- **Windows Executables**: Can still be run, but use forward slashes: `cmdbin/uv.exe` not `cmdbin\uv.exe`

**Correct Path Examples:**
- ✅ `/c/acex/prjx/project/file.txt` (Unix-style)
- ✅ `python/python.exe scripts/build.py` (relative paths with forward slashes)
- ❌ `c:\acex\prjx\project\file.txt` (Windows-style with backslashes won't work)
- ❌ `dir c:\folder\` (Windows commands with backslashes fail)

**Running Windows Programs:**
- Python: `python/python.exe` or just `python` if on PATH
- Windows tools: Use forward slashes for all paths
- Native commands: `ls` works, `dir` doesn't (use `ls` instead)

## Available Tools

System-wide tools available in any directory:
- `rg` (ripgrep) - Fast text search: `rg "pattern" --type py`
- `jq` - JSON processor: `fd "*.json" | xargs jq .`
- `fd` (fdfind) - Fast file finder
- `bat` (batcat) - Enhanced cat with syntax highlighting
- `tree` - Directory structure: `tree -L 2`
- `xmlstarlet` - XML processing
- `dos2unix` - Fix line endings
- `file` - Determine file types
- `git-extras` - Git utilities (git-flow, git-changelog, git-ignore, etc.)
- `httpie` - Modern HTTP client: `http GET example.com`
- `ncdu` - NCurses disk usage analyzer
- `tldr` - Simplified man pages with practical examples
- `fzf` - Fuzzy finder for terminal
- `ag` (silversearcher) - Fast code searching tool
- `docker` & `docker-compose` - Container tools
- `go` - Go programming language
- `rustc` & `cargo` - Rust programming language and package manager
- `gh` - GitHub CLI
- `uv` - Fast Python package manager and script runner

### Compilers Available in c:\acex\appz
- **Clang/LLVM** (`c:\acex\appz\clang\bin\`) - Modern C/C++ compiler with full toolchain
  - `clang.exe`, `clang++.exe` - C/C++ compilers
  - `clang-format.exe` - Code formatter
  - `lld.exe` - Linker
- **Go** (`c:\acex\appz\golang\bin\`) - Go compiler and tools
  - `go.exe` - Go compiler and build system
- **Rust** (`c:\acex\appz\rust\cargo\bin\`) - Rust toolchain
  - `rustc.exe` - Rust compiler
  - `cargo.exe` - Package manager and build system
  - `rust-analyzer.exe` - Language server
  - `rustfmt.exe`, `clippy-driver.exe` - Formatting and linting

### Windows Development Tools
- **ResourceHacker** - Windows resource editor (on PATH)
  - Edit icons, version info, and other resources in executables

### Python Development

**IMPORTANT: NEVER run Python scripts with `python script.py`. ALWAYS run them directly with their shebang:**
- ✅ CORRECT: `uv run --script ./scripts/my_script.py`
- ❌ WRONG: `python scripts/my_script.py`; `python3 scripts/my_script.py` is also wrong

**All Python scripts MUST have this shebang as the first line:**
```python
#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = [
    # List PyPI packages here
]
# ///
```

**Key points:**
- The shebang `#!/usr/bin/env uvrun` allows scripts to be executed directly
- This works in both Bash and Nushell (unlike `#!/usr/bin/env -S uv run --script` which only works in Bash)
- Scripts can use ANY PyPI package without pre-installation - just list it in dependencies
- The script metadata block (`# /// script`) declares dependencies inline
- Use `uv run` to execute Python scripts with automatic dependency management
- See `/home/ace/bin/l0g` for a working example

**When creating new Python scripts:**
1. ALWAYS start with the `#!/usr/bin/env uvrun` shebang
2. Add the script metadata block with dependencies
3. Add UTF-8 encoding fix for Windows console (after imports):
   ```python
   import sys
   # Fix Windows console encoding for Unicode characters
   if sys.stdout.encoding != 'utf-8':
       sys.stdout.reconfigure(encoding='utf-8')
       sys.stderr.reconfigure(encoding='utf-8')
   ```
4. Make the script executable: `chmod +x script.py`
5. Run it directly: `./script.py` NOT `python script.py`

### Node.js Tools (global npm packages)
- `prettier` - Code formatter for JS/TS/CSS/etc
- `eslint` - JavaScript linter
- `typescript` - TypeScript compiler
- `tsx` - TypeScript execute
- `nodemon` - Auto-restart node apps
- `pm2` - Process manager
- `yarn`, `pnpm` - Alternative package managers

**Note**: If you need any standard development tools that aren't listed above or that you discover are missing during your work, feel free to install them using the appropriate package manager (apt, pip, npm, etc.). This ensures you have all necessary tools to complete tasks efficiently.

## Email Access

### Quick Email Commands

```bash
# Send email
email-send <to> <subject> <body> [html]
email-send user@example.com "Subject" "Message body"
email-send user@example.com "Subject" "<h1>HTML</h1>" html

# Read emails
email-read        # Read latest email
email-read 5      # Read last 5 emails
```

## WebShot Screenshot Tool

Captures screenshots of webpages at any URL.

```bash
webshot [URL] [output-file] [WIDTHxHEIGHT]
```

## Temporary Files and Scripts

### 📁 ALWAYS use ./tmp directory for ALL temporary files and scripts

**MANDATORY: All temporary scripts, test files, and intermediate outputs MUST go in the project's ./tmp/ directory:**

```bash
# ALWAYS create tmp directory first if it doesn't exist
mkdir -p ./tmp

# Examples of correct usage:
./tmp/test_script.py           # Test scripts
./tmp/debug_output.txt         # Debug output
./tmp/temp_data.json          # Temporary data files
uv run --script ./tmp/test.py  # Running Python test scripts

# Python example:
import os
os.makedirs('./tmp', exist_ok=True)  # Always ensure tmp exists
with open('./tmp/output.txt', 'w') as f:
    f.write('temporary output')
```

**NEVER create temporary files in:**
- ❌ Git repository root (except ./tmp/)
- ❌ Project source directories (src/, lib/, etc.)
- ❌ Any version-controlled directory (except ./tmp/)
- ❌ System temp directories (/tmp, %TEMP%) for project-specific files

**Remember:** The ./tmp/ directory should be added to .gitignore to keep temporary files out of version control.

## Important Instructions

### ⚠️ CRITICAL: NEVER USE THE cd COMMAND
- **ALWAYS use absolute paths instead of cd**
- ❌ WRONG: `cd /path/to/dir && ./script.py`  
- ✅ RIGHT: `/path/to/dir/script.py`
- ❌ WRONG: `cd /home/ace/prjx/project && npm test`
- ✅ RIGHT: `npm test --prefix /home/ace/prjx/project` or run from root with full paths
- The ONLY exception is the Bash tool documentation mentions maintaining working directory with absolute paths

- Always be brief and do only what is needed now; never write code that "might be needed someday"
- Never create files unless absolutely necessary
- Always use ./tmp directory for temporary scripts
