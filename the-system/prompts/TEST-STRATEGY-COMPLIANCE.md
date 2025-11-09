# Test Strategy Compliance

## Objective

Ensure all tests in `./tests/failing/` directory comply with the testing strategies and specifications documented in `./README.md` and `./readme/` directory.

## Instructions

### 1. Read Documentation

Read and understand the testing strategies from:
- `./README.md` - Look for testing-related sections
- `./readme/TESTING.md` - Primary testing specification document
- Any other `./readme/*.md` files that mention testing

Pay special attention to:
- Required test patterns and flows
- Tools that must be used (e.g., mock servers, special tools, etc.)
- Expected test data generation methods
- Verification requirements
- Artifact locations

### 2. Analyze Existing Tests

Read all test files in `./tests/failing/` directory:
- Understand what each test is trying to verify
- Identify which requirements each test covers
- Note any deviations from documented testing strategies

### 3. Identify Non-Compliance

Compare the actual test implementations against the documented testing strategies.

**IMPORTANT**: If there is no specific testing strategy documented in the README files, OR if the tests are already compliant with the documented strategy, then **DO NOT make any changes**. Simply report that no action is needed.

Otherwise, look for:
- Missing steps in the test flow
- Tools that should be used but aren't
- Incorrect test data generation methods
- Steps performed in wrong order
- Missing mock implementations
- Shortcuts that violate the documented approach

### 4. Take Corrective Action

**If tests are compliant or no testing strategy exists**: Report that no changes are needed and stop here.

**If non-compliance is found**: Do whatever is necessary to achieve full compliance:

**Modify existing tests** if they:
- Follow the right approach but have implementation issues
- Are mostly correct but skip required steps
- Can be fixed to match the documented strategy

**Delete tests** if they:
- Cannot be salvaged to match the documented strategy
- Test the wrong thing entirely
- Are duplicates of other tests

**Write new tests** if:
- The documented strategy requires test steps that don't exist
- Existing tests must be deleted and replaced
- Coverage gaps exist that need new test files

### 5. Ensure Complete Compliance

After making changes, verify that:
- All steps in the documented test strategy are implemented
- Tests use the correct tools and methods
- Test flow matches the documented pattern
- All verification requirements are met
- Test artifacts are placed in correct locations

## Success Criteria

- Every test in `./tests/failing/` follows the documented testing strategy exactly
- No shortcuts or deviations from the documented approach
- All required test steps are implemented
- Tests use the correct tools (mock servers, rawprox, etc.)
- Test data is generated using documented methods

## Output

**If no changes needed**:
- State that tests are already compliant, OR
- State that no testing strategy is documented

**If changes made**:

For each change you make:
1. Explain what was non-compliant
2. Describe your corrective action (modify/delete/create)
3. Confirm how the change achieves compliance

At the end, summarize:
- Total tests modified
- Total tests deleted
- Total tests created
- Confirmation that all tests now comply with documented strategies
