# CODE_REVIEW_FOR_REQUIREMENT.md -- Verify Architectural Requirement

You are reviewing code to verify that an architectural requirement is satisfied.

---

## Your Task

Examine the implementation in `./code/` and determine if it satisfies the specified architectural requirement.

---

## Instructions

1. **Read the requirement carefully** -- You will be given a specific architectural requirement to verify
2. **Read all relevant code** -- Examine implementation files in `./code/`
3. **Verify the architecture** -- Check if the code structure matches the requirement
4. **Respond with verdict** -- Output either PASS or FAIL with explanation

---

## Available Tools

**Finding relevant code:**

You can run `reqtrace.py` to see which code files are already tagged with the requirement ID:

```bash
uv run --script ./the-system/scripts/reqtrace.py $REQ_LOGGING_001
```

This shows:
- The full requirement definition from `./reqs/`
- Which code files implement this requirement (with line numbers)
- Which tests verify this requirement
- Source attribution (which README section this came from)

**Use this to:**
- Start your review with the most relevant files
- Verify consistency across all tagged implementations
- Understand the broader context of the requirement

**If reqtrace.py isn't available or fails, that's okay** -- just examine all code in `./code/` directly.

---

## Output Format

**If requirement is satisfied:**
```
VERDICT: PASS

The code satisfies the requirement because:
- [specific evidence from code with file:line references]
- [architectural pattern observed]
- [relevant implementation details]
```

**If requirement is NOT satisfied:**
```
VERDICT: FAIL

The code does NOT satisfy the requirement because:
- [what's wrong]
- [what's missing]
- [what contradicts the requirement]
```

---

## Examples

### Example 1: Non-blocking Logging

**Requirement:** Network I/O operations must never block on disk writes

**Response:**
```
VERDICT: PASS

The code satisfies the requirement because:
- Network handler in ./code/Network.cs:45 uses async/await pattern
- All disk writes go through LogBuffer class which queues to memory
- Disk I/O happens on background thread (see ./code/LogBuffer.cs:89)
- Network operations never call disk I/O directly
- LogBuffer.Write() returns immediately after queuing to memory buffer
```

### Example 2: Async Pattern

**Requirement:** All file operations must use async/await pattern

**Response:**
```
VERDICT: FAIL

The code does NOT satisfy the requirement because:
- File.ReadAllText() is used synchronously in ./code/ConfigLoader.cs:23
- File.WriteAllBytes() is used synchronously in ./code/DataWriter.cs:67
- These should be replaced with async equivalents (File.ReadAllTextAsync, etc.)
```

---

## Important Notes

- **Be specific** -- Cite exact file paths and line numbers
- **Look for patterns** -- Check if architecture is consistently applied throughout codebase
- **Consider all code paths** -- Don't just check the happy path
- **Be thorough** -- Examine all relevant files in `./code/`
- **Base verdict only on code** -- Don't assume implementation, verify it exists

---

## Common Architectural Requirements

**Non-blocking I/O:**
- Look for async/await usage
- Check that operations return immediately
- Verify background processing for slow operations

**Separation of concerns:**
- Check that modules have clear responsibilities
- Verify no cross-cutting concerns mixed together

**Performance patterns:**
- Look for buffering, pooling, caching
- Check that expensive operations are optimized

**Error handling:**
- Verify proper exception handling
- Check that errors don't crash the system
