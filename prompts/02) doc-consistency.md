# Documentation Consistency Review

Read `FOUNDATION.md`, `README.md`, and `SPECIFICATION.md` to ensure they meet these criteria:

## Consistency Requirements

1. **Internal agreement**: All documents must align on facts and requirements
2. **Minimal overlap**: Eliminate redundancy between documents
3. **Audience targeting**:
   - `README.md` → General audience (non-developers)
   - `SPECIFICATION.md` → Experienced developers who have read README
4. **Code examples**: SPECIFICATION should not include code that experienced developers already know how to write
5. **Brevity**: All documents should be concise and avoid verbosity

## Document Hierarchy

`FOUNDATION.md` establishes the core concept ("I want to create X"). Then:
- `README.md` provides a user-oriented overview of X
- `SPECIFICATION.md` defines X with implementation-level precision

The foundation underlies both documents, but README and SPECIFICATION should have minimal overlap with each other.

## Additional Context

Compare these three documents against all other `*.md` files in the tree (excluding `./prompts/` and `./reports/`).

**Important**: Ignore historical designs and implementations. Focus only on the current project design.

## Output

Write proposed changes to `./reports/doc-consistency_report.md`. Do not make changes yet.
