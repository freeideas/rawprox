# REMOVE_ORPHAN_REQS.md -- Remove Orphan Requirement Tags

You are an AI assistant tasked with cleaning up orphan requirement tags from tests and code.

---

## What Are Orphan $REQ_IDs?

An **orphan $REQ_ID** is a requirement tag that appears in test files or code files but does **NOT** exist in any flow file under `./reqs/`.

This happens when:
- Requirements were removed from flows but references weren't cleaned up
- Tests or code referenced $REQ_IDs that were never defined
- Flow files were restructured and some $REQ_IDs were deleted

---

## Your Task

Remove all orphan $REQ_ID tags from tests and code files.

You will be provided with a list of orphan $REQ_IDs and their locations.

---

## Instructions

### Step 1: Review the Orphan List

The prompt will include a list like:
```
  $REQ_STARTUP_999:
    - ./tests/failing/test_startup.py:42
    - ./code/server.py:156
  $REQ_INVALID_001:
    - ./tests/passing/test_validation.py:78
```

### Step 2: Remove Tags from Files

For each file listed:
1. Open the file
2. Find the orphan $REQ_ID tags
3. Remove or update the lines containing those tags

**How to remove depends on context:**

**In tests (assertions with comments):**
```python
# Before:
assert server.is_running()  # $REQ_STARTUP_999

# After:
assert server.is_running()  # Remove the comment entirely
```

**In code (implementation comments):**
```csharp
// Before:
public void StartServer()
{
    // $REQ_STARTUP_999: Launch the server process
    Process.Start("server.exe");
}

// After:
public void StartServer()
{
    // Launch the server process
    Process.Start("server.exe");
}
```

**If entire test assertion is only for orphan req:**
```python
# Before:
def test_startup():
    server = Server()
    server.start()
    assert server.is_running()  # $REQ_STARTUP_999
    assert server.port == 8080  # $REQ_STARTUP_002

# After (if only $REQ_STARTUP_999 is orphan):
def test_startup():
    server = Server()
    server.start()
    # Removed orphan assertion for $REQ_STARTUP_999
    assert server.port == 8080  # $REQ_STARTUP_002
```

### Step 3: Update Tests if Needed

If removing orphan tags causes a test to become empty or meaningless:
- Remove the entire test function
- Or update it to test only valid requirements

**Never leave broken tests** -- tests must still be valid Python after removal.

---

## Important Notes

- **Only remove the specified orphan $REQ_IDs** -- do not remove other tags
- **Preserve code functionality** -- removing tags should not break working code
- **Keep tests valid** -- tests must still compile and run after tag removal
- **Be surgical** -- only modify lines containing orphan tags

---

## Example

### Input:
```
Orphan $REQ_IDs to remove:
  $REQ_AUTH_999:
    - ./tests/failing/test_auth.py:23
  $REQ_INVALID_001:
    - ./code/auth.py:67
```

### File: ./tests/failing/test_auth.py (before)
```python
def test_authentication():
    user = User("alice", "password123")
    assert user.authenticate()  # $REQ_AUTH_999
    assert user.has_permission("read")  # $REQ_AUTH_002
```

### File: ./tests/failing/test_auth.py (after)
```python
def test_authentication():
    user = User("alice", "password123")
    # Removed orphan $REQ_AUTH_999
    assert user.has_permission("read")  # $REQ_AUTH_002
```

### File: ./code/Auth.cs (before)
```csharp
public bool Authenticate(string username, string password)
{
    // $REQ_INVALID_001: Validate credentials
    return CheckCredentials(username, password);
}
```

### File: ./code/Auth.cs (after)
```csharp
public bool Authenticate(string username, string password)
{
    // Validate credentials
    return CheckCredentials(username, password);
}
```

---

## Summary

1. Review the list of orphan $REQ_IDs and their locations
2. Remove or clean up the orphan tags from each file
3. Ensure tests remain valid and runnable after changes
4. Preserve all working code and non-orphan requirements
