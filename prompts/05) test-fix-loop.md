# Test-Fix Iteration Loop

Read `@README.md` and `@SPECIFICATION.md` to understand expected behavior.

## Process

1. **Run tests**: Execute `./scripts/test.py`
2. **Fix failures**: Edit source code or test scripts as needed
3. **Iterate**: Repeat until all tests pass

## Debugging Strategy

When failure causes are unclear, add intermediate tests to narrow down the problem area. If something fails between point A and point Z, add a test at point N to identify which half contains the issue.

## Documentation Issues

Append to `./reports/test-fix-loop_report.txt` whenever you discover:
- Documentation inaccuracies or contradictions
- Requirements that are impractical or impossible to implement
