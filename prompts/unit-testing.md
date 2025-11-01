# Unit Testing Convention

Every code file should contain one or more methods with the prefix `_TEST_` in the method name. Each `_TEST_` method should meaningfully test the rest of the code in the same file as much as reasonably possible, without heroic measures.

**Scope**: This applies to application code files only. Scripts under `./scripts/` do not require `_TEST_` methods.

**Background**: Read `README.md` and `SPECIFICATION.md` for project context and technical details.

## Tasks

1. **Review code files**: Examine each code file to ensure it has at least one `_TEST_` method
2. **Validate test methods**: Review each `_TEST_` method to confirm it meaningfully tests the other code in the same file
3. **Test runner script**: Ensure `./scripts/test_0unit.py` exists and properly executes all `_TEST_` methods across the codebase
   - Implementation will be language-specific
   - May require introspection/reflection to discover `_TEST_` methods dynamically
   - Should report success/failure for each method
4. **Main test orchestration**: Ensure `./scripts/test.py` runs all `test_*.py` files in alphanumeric order
   - This ensures `test_0unit.py` runs first (unit tests before integration tests)

## Guidelines

- Tests should be practical and focused on the file's core functionality
- Avoid over-engineering tests for edge cases unless critical
- Keep tests simple and maintainable
- The `_TEST_` prefix makes test methods easily discoverable via code search or reflection
- **Method signature**: `_TEST_` methods must take no arguments and return no value (void)
  - Tests should terminate the process (e.g., `System.exit(1)`, `panic!`, etc.) or throw an exception on failure
  - Success is indicated by the method completing normally without error
