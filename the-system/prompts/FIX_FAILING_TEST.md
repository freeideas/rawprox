# FIX_FAILING_TEST.md -- Fix Code to Make Test Pass

Fix failing tests by implementing or correcting code in `./code/`.

---

## Project Philosophy

**Follow @the-system/prompts/PHILOSOPHY.md:**
- Build only what is explicitly required in `/reqs/`
- No "nice to have" features
- No undocumented edge cases
- No error handling except where required
- Complexity is a bug -- fix it by deletion
- Implementation choices not mandated by README can change freely

---

## Instructions

### Step 1: Understand the Failure

Read test output to identify the issue:
- **Import errors** -- missing modules/files
- **Assertion errors** -- expected behavior not implemented
- **Runtime errors** -- bugs in code
- **Process errors** -- executable missing or crashes

### Step 2: Read the Test

Read the failing test file:
- What $REQ_IDs it tests (check `# $REQ_ID` comments)
- What behavior is expected
- What the test verifies

### Step 3: Read the Requirements

For each $REQ_ID, use `uv run --script ./the-system/scripts/reqtrace.py $REQ_ID` to see the requirement definition, flow file, and implementation status.

### Step 4: Implement or Fix Code

Create/modify files in `./code/` to make test pass.

**Code structure is flexible:**
- Organize however makes sense
- Refactor freely as long as tests pass
- Follow programming language in README.md

**Tag code with $REQ_ID comments:**
```csharp
public void Start()
{
    // $REQ_STARTUP_001: Launch server process
    _process.Start();

    // $REQ_STARTUP_002: Bind to port
    _listener = new TcpListener(IPAddress.Any, _port);
    _listener.Start();
}
```

**Tagging guidelines:**
- Add above/on line implementing the requirement
- Format: `// $REQ_ID` or `// $REQ_ID: brief description`
- Not every line needs a tag -- just key implementation points

### Step 5: Fix Test Only If Truly Incorrect

**In most cases, fix the code, not the test.**

**Valid reasons to fix a test:**
- Test misinterprets the requirement
- Test has a bug (wrong assertion logic)
- Test impossible to satisfy as written

**If you fix a test:**
- Document why in a comment
- Ensure it still verifies same $REQ_IDs
- Keep all $REQ_ID tags

---

## Common Failure Patterns

### Import Error
```
ImportError: No module named 'server'
```
**Fix:** Create the missing module/class in `./code/`

### Missing Executable
```
FileNotFoundError: './release/server.exe'
```
**Fix:** Implement code in `./code/`, update `./tests/build.py` to compile and copy to `./release/`

### Assertion Failure
```
AssertionError: Process not running  # $REQ_STARTUP_001
```
**Fix:** Read the requirement, implement missing functionality

---

## Code Organization

Organize `./code/` however makes sense:
- Single-file projects
- Multi-file projects
- Namespace-based structure

All application code goes in `./code/` (never in `./tests/`, `./reqs/`, or `./the-system/`).

---

## Build Integration

If test expects executable in `./release/`, update `./tests/build.py` to:
1. Compile your code
2. Place executable in `./release/`

Test runner automatically runs `./tests/build.py` before tests.

---

## Architectural Tests (Rare)

Some tests verify **implementation patterns** by invoking AI code review:

```python
def test_logging_nonblocking():
    prompt = """Follow @the-system/prompts/CODE_REVIEW_FOR_REQUIREMENT.md

Requirement: $REQ_LOGGING_001 - Logging never blocks on disk I/O"""

    result = subprocess.run(
        ['uv', 'run', '--script', './the-system/scripts/prompt_agentic_coder.py'],
        input=prompt, capture_output=True, text=True, encoding='utf-8'
    )
    assert 'VERDICT: PASS' in result.stdout  # $REQ_LOGGING_001
```

**If architectural test fails:**
1. Read AI's verdict (explains what's wrong)
2. Understand the architectural requirement (HOW to implement, not just WHAT)
3. Refactor code to match required pattern
4. Keep behavioral tests passing while refactoring

**Key difference:**
- Behavioral test fails → Implement missing functionality
- Architectural test fails → Refactor to use required pattern

---

## Example

**Test failing:**
```python
def test_startup():
    process = subprocess.Popen(['./release/server.exe'])
    time.sleep(1)
    assert process.poll() is None  # $REQ_STARTUP_001

    sock = socket.socket()
    assert sock.connect_ex(('localhost', 8080)) == 0  # $REQ_STARTUP_002
    sock.close()
```

**Fix with code:**
```csharp
// ./code/Server.cs
using System.Net.Sockets;

class Server
{
    static void Main(string[] args)
    {
        // $REQ_STARTUP_002: Bind to port 8080
        TcpListener listener = new TcpListener(IPAddress.Any, 8080);
        listener.Start();

        // $REQ_STARTUP_001: Keep running
        while (true) System.Threading.Thread.Sleep(1000);
    }
}
```

**And update build:**
```python
# ./tests/build.py
def main():
    os.makedirs('./release', exist_ok=True)
    subprocess.run(['dotnet', 'build', '-c', 'Release', './code/Server.csproj'])
    shutil.copy('./code/bin/Release/net8.0/Server.exe', './release/server.exe')
```

---

## Important Notes

### Keep It Simple

Only implement what tests require. No unnecessary features, abstractions, or "future-proofing".

### Tests Are the Specification

The test defines correct behavior. If test says "port 8080", use port 8080 -- even if you prefer different.

**Requirements → Tests → Code** (in that order)

### Failing Tests Stay in ./tests/failing/

Don't move tests yourself. Construction script moves them when they pass.

### Iteration Is Normal

You may need multiple attempts:
1. Implement code
2. Run test
3. Fix issue
4. Repeat

This is expected.

---

## Summary

1. Read test output to understand failure
2. Read test file and requirements
3. Implement/fix code in `./code/`
4. Update `./tests/build.py` if needed
5. Fix test only if truly incorrect (rare)
6. Keep code simple
7. Tests define correct behavior
