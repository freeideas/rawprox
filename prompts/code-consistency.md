# Code-Documentation Consistency Check

Read `@README.md` and `@SPECIFICATION.md` for context.

## Task

Locate all `*.md` documentation files (excluding `./prompts/` and `./reports/`), then verify that source code matches documented specifications. Make code changes as needed to ensure consistency.

## Important Principles

- **No historical artifacts**: Remove all traces of previous implementations from code
- **Focus on current design**: Don't preserve outdated patterns or comments
- **Limited cognitive load**: Don't try to hold all documentation in memory at once

## Recommended Approach

1. Find all `.md` files in the project
2. Create a mapping plan: which documentation sections correspond to which code files
3. Work through comparisons systematically, one mapping at a time
