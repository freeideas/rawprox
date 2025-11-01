# fix_req-flow-structure.md -- Fix Flow Structure

Ensure flow documents in `./reqs/` tell complete use-case stories from start to shutdown.

---

## THE SIX RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)

---

## Good Flow Structure

Flows tell complete use-case stories -- sequences from start to shutdown that can be tested end-to-end.

**Good (organized by use case):**
- `startup-to-shutdown.md` -- Start server, verify ready, use it, shutdown
- `install.md` -- Install from scratch to ready state
- `client-usage.md` -- Connect, perform operations, disconnect
- `error-handling.md` -- Trigger errors, verify responses, recovery

**Bad (organized by technical category):**
- `network-requirements.md` -- Only network aspects (not complete story)
- `logging-requirements.md` -- Only logging (not complete scenario)
- `api-endpoints.md` -- Only API definitions (no start-to-end flow)

---

## What to Check

**Completeness:**
- Clear beginning state
- Clear ending/shutdown state
- No gaps in sequence

**Testability:**
- Can execute as single test
- End-to-end testable

**Organization:**
- By use case (good), not technical category (bad)
- Tells a story, doesn't just list related features

**Sequence:**
- Steps follow logical order
- Dependencies are clear

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Verify each flow tells complete use-case story
4. **Fix by reorganizing** flows from technical categories into use-case stories
5. **Fix by adding** missing startup/shutdown steps
6. **Fix by reordering** steps to follow logical sequence
7. **Fix by splitting/merging** flows to make them independently testable

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process. If issues are found, include what was restructured or what README changes are needed.

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `GOODENUF` -- All flows are properly structured as complete use-case stories
- `NEEDIMPROV` -- Found structure issues and fixed them (AI reorganized ./reqs/)
- `READMEBUG` -- README organized by technical category instead of use cases, needs human revision
