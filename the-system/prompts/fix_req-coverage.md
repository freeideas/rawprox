# fix_req-coverage.md -- Fix Coverage Gaps

Ensure all testable behaviors from READMEs are represented in `./reqs/`.

---

## THE SIX RULES FOR REQUIREMENTS

1. **Complete Coverage** -- Every testable behavior in READMEs must have a $REQ_ID
2. **No Invention** -- Only requirements from READMEs are allowed
3. **No Overspecification** -- Requirements must not be more specific than READMEs
4. **Tell Stories** -- Flows go from start to shutdown (complete use-case scenarios)
5. **Source Attribution** -- Every $REQ_ID cites: `**Source:** ./readme/FILE.md (Section: "Name")`
6. **Unique IDs** -- Each $REQ_ID appears exactly once. Format: `$REQ_` followed by letters/digits/underscores/hyphens (e.g., $REQ_STARTUP_001)

---

## Your Task

1. Read `./README.md` and all files in `./readme/`
2. Read all flow files in `./reqs/`
3. Identify testable behaviors in READMEs missing from flows
4. **Fix by adding missing requirements** to appropriate flow files
5. **Fix by splitting** requirements that combine multiple distinct behaviors

**Testable behaviors:**
- Actions users take
- System responses
- Observable outputs
- Error conditions
- Success criteria
- State changes
- Network behavior
- File operations
- Process lifecycle

**Skip:**
- Background information
- Installation instructions (unless they specify behavior)
- General descriptions without testable outcomes
- Explanatory text about design trade-offs ("we chose X over Y because...")
- Natural consequences of other requirements (e.g., OOM from unbounded buffering)
- OS/runtime behavior (e.g., process termination, signal handling by OS)
- Redundant restatements with added consequence details

---

## How to Fix

**Add missing requirements:**
- For each missing testable behavior, add a $REQ_ID to the appropriate flow file
- Use proper format and source attribution
- Maintain flow sequence (start to shutdown)

**Split combined requirements:**
- If one requirement describes multiple distinct testable behaviors, split into separate $REQ_IDs
- Each behavior gets its own requirement

---

## Output Format

Write a markdown analysis report with your full reasoning, findings, and thought process. Include what was missing and what was added/needs clarification if issues were found.

**IMPORTANT:** The LAST LINE of your response must be the status word alone:
- `GOODENUF` -- All testable behaviors are covered by requirements
- `NEEDIMPROV` -- Found missing coverage and fixed it (AI added requirements to ./reqs/)
- `READMEBUG` -- README documentation is unclear or incomplete, preventing proper coverage
