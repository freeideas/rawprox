# ORDER_TESTS.md -- Order Tests by Dependency

Order test files from general/foundational to specific/advanced using numeric prefixes.

---

## Project Philosophy

**Follow @the-system/prompts/PHILOSOPHY.md:**
- Keep it simple
- Focus on what matters

---

## Your Task

Analyze all test files in `./tests/failing/` and `./tests/passing/` and order them with numeric prefixes.

**Read context:**
- `./README.md` and `./readme/*.md` to understand dependencies
- Test files to see what they verify

**Ordering tiers:**

- **00-XX:** Build/installation (must pass before anything else)
- **01-XX:** Startup/lifecycle (must work before features)
- **02-XX:** Core functionality (basic use cases)
- **03-XX:** Advanced features (build on core)
- **04-XX+:** Edge cases and integrations

**Note:** Infrastructure tests (`_test_*.py`) run before regular tests (`test_*.py`) in the same tier.

**Rename tests as needed:**

Assign appropriate numeric prefixes. Rename files in both `./tests/failing/` and `./tests/passing/`.

Example:
```
test_startup.py → test_01_startup.py
test_proxy.py → test_02_basic_proxy.py
```

**Report results:**

```
TESTS_ORDERED

Renamed:
- test_startup.py → test_01_startup.py
- test_proxy.py → test_02_basic_proxy.py

Final order:
00: Build/Installation
  - _test_00_build_artifacts.py
01: Lifecycle
  - test_01_startup.py
02: Core Features
  - test_02_basic_proxy.py
```

If no renames needed, just report the current order.
