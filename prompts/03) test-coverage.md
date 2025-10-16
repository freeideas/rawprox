# Test Coverage Analysis

Locate all `*.md` documentation files (excluding `./prompts/` and `./reports/`), then verify that `./scripts/test.py` adequately tests documented behavior.

## Tasks

1. **Update test suite**: Modify `scripts/test.py` and related test scripts to ensure reasonable coverage of every documented feature, rule, and measurable quality
2. **Pragmatic scope**: Skip qualities that are impractical to test
3. **Generate report**: Write `./reports/test-coverage_report.md` documenting:
   - How each feature, rule, or quality is tested
   - Which tests are gratuitous (not derived from documentation)
