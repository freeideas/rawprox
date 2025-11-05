# fix_req-sources.md -- Fix Source Attribution

Ensure all requirements in `./reqs/` have proper source attribution.

---

## THE SEVEN RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every reasonably testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)
7. **Reasonably Testable** -- Requirements must have observable behavior that can be verified

---

## Proper Source Attribution Format

```markdown
## $REQ_STARTUP_001: Requirement Title
**Source:** ./readme/FILENAME.md (Section: "Section Name")

Requirement description.
```

**Format:** `$REQ_` followed by any combination of letters, digits, underscores, hyphens. Examples: `$REQ_STARTUP_001`, `$REQ_X`, `$REQ_logging_async_002`

**Required:**
- `**Source:**` line immediately after heading
- Path to README file
- Section name in quotes (if applicable)

**Variations:**
- No specific section: `**Source:** ./README.md`
- Multiple sections: `**Source:** ./readme/FILE.md (Sections: "Section 1", "Section 2")`

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. For each `$REQ_ID`, verify `**Source:**` line exists and is correct
4. **Focus on significant issues** -- only fix missing or clearly incorrect source attributions
5. **Fix by adding or correcting** source attributions

---

## Output Format

**Do NOT create any report files.** Just respond with a simple list.

**If significant issues found:** For each change, list:
- File: (which file was edited)
- Before: (the $REQ_ID with missing/incorrect source)
- After: (the corrected source attribution)
- Why: (what was wrong with the source)

**If no significant issues found:** State that all requirements have proper source attribution.
