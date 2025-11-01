# fix_req-sources.md -- Fix Source Attribution

Ensure all requirements in `./reqs/` have proper source attribution.

---

## THE SIX RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)

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
4. **Fix by adding or correcting** source attributions

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process. If issues are found, include which requirements were missing sources and how they were fixed.

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `GOODENUF` -- All requirements have proper source attribution
- `NEEDIMPROV` -- Found missing/incorrect source attributions and fixed them (AI updated ./reqs/)
- `READMEBUG` -- Should not occur for this check (source issues are always fixable)
