# Workflow Guide for Humans

**Important**: Don't move to the next step until the previous step is settled. For example, don't try to get good test coverage if the documentation is not consistent yet.
**Note on Reports**: Generated reports are often extremely long. Scan them quickly and skip directly to the recommendations at the end rather than reading everything in detail.

## Initial Project Setup

1. Write `@FOUNDATION.md`
2. Run `@"01) foundation.md"` prompt
3. Read generated `@README.md` and `@SPECIFICATION.md`; consider updating `@FOUNDATION.md`; at least one redo will be needed
4. Run `@"02) doc-consistency.md"` prompt; consider recommendations in its report
5. Run `@"03) test-coverage.md"` prompt; consider recommendations in its report
6. Run `@"04) startup.md"` prompt; consider recommendations in its report

## After Changing Documentation

1. Run `@"02) doc-consistency.md"` prompt; consider recommendations in its report
2. Run `@"03) test-coverage.md"` prompt; read the report it generates
3. **Exercise judgment**: Evaluate recommendations rather than blindly following them. You will know you don't need to make changes when the recommendations become trivial.

## After Changing Tests or Code

1. Run `@"05) test-fix-loop.md"` prompt
2. Review the generated report

## When a Bug Escapes Testing

1. Document the bug in `./tmp/BUG_REPORT.md`
2. Run `@"06) bug-report.md"` prompt
3. Review the analysis report

---

**Note**: Additional prompts exist in this directory, but you may not need them for typical workflows.
