## Environment

- **GitHub**: Already logged in and authenticated
- **Project Repositories**: All project repos are located under `/home/ace/prjx`
- **Git Branch Naming**: Always use "main" instead of "master" for default branch names, as some people find "master" offensive

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

### Python Development

**IMPORTANT: NEVER run Python scripts with `python script.py`. ALWAYS run them directly with their shebang:**
- ✅ CORRECT: `uv run --script ./scripts/my_script.py`
- ❌ WRONG: `python scripts/my_script.py` or `python3 scripts/my_script.py`

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

**When creating new Python scripts:**
1. ALWAYS start with the `#!/usr/bin/env uvrun` shebang
2. Add the script metadata block with dependencies
3. Make the script executable: `chmod +x script.py`
4. Run it directly: `./script.py` NOT `python script.py`

### Node.js Tools (global npm packages)
- `prettier` - Code formatter for JS/TS/CSS/etc
- `eslint` - JavaScript linter
- `typescript` - TypeScript compiler
- `tsx` - TypeScript execute
- `nodemon` - Auto-restart node apps
- `pm2` - Process manager
- `yarn`, `pnpm` - Alternative package managers

**Note**: If you need any standard development tools that aren't listed above or that you discover are missing during your work, feel free to install them using the appropriate package manager (apt, pip, npm, etc.). This ensures you have all necessary tools to complete tasks efficiently.

**ALWAYS use ./tmp directory for temporary scripts:**

```bash
# Create tmp directory if it doesn't exist
mkdir -p ./tmp
# Run tests with absolute or relative paths (NO cd!)
uv run --script ./tmp/test_script.py
# Or specify output paths:
uv run --script script.py --output ./tmp/results.json

# Bad - Never create temporary files in:
# - Git repository roots (except in tmp/, which should be added to .gitignore)
# - Project source directories
# - Any version-controlled directory (except tmp/, which should be added to .gitignore)
```

Python: Always use `./tmp` directory (create it with `os.makedirs('./tmp', exist_ok=True)` if needed).

## Important Instructions

### ⚠️ CRITICAL: NEVER LAUNCH MOCK ALFRESCO SERVERS IN TESTS
- **NEVER** start mock servers in test code
- **NEVER** launch `tests/mock_alfresco.py` from any test
- **DO NOT** try to fix or improve `tests/mock_alfresco.py`
- Tests MUST use an external proxy running on `localhost:8081` that forwards to a **real Alfresco instance**
- Mock servers produce broken clients that fail in production - we test against REAL Alfresco ONLY
- If a test needs Alfresco, ensure your proxy is running: `http://localhost:8081/alfresco/` should return 200
- Tests verify against recorded SOAP traces from real Alfresco in `net-traces/traces.sqlite`

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

## Cross Platform
- We try to write everything in the most Windows and Linux -compatible way
- We often name shell scripts with .bat and binary executables with .exe even on Linux devices, because Linux doesn't care, but Windows does.
