# Project Reorganization

Reorganize this project into a clean, minimum-viable structure. Include only essential elements.

## Documents to Create

### `README.md`
- **Audience**: All users
- **Content**: Purpose, usage instructions, practical examples
- **Style**: Clear, concise, actionable

### `SPECIFICATION.md`
- **Audience**: Experienced developers
- **Content**: Architecture, behavior specs, platform requirements
- **Style**: Precise, technical, unambiguous
- **Exclude**: Code examples (developers understand patterns), hypothetical constraints
- **Error handling**: Cover only realistic failure scenarios
- **Edge cases**: Document only those likely to occur in production

### `./scripts/build.py`
- Builds project and outputs to `./release/*.exe`
- Uses PEP 723 dependencies with `#!/usr/bin/env uvrun` shebang

### `./scripts/test.py`
- Executes complete test suite
- Uses PEP 723 dependencies with `#!/usr/bin/env uvrun` shebang

### `./doc/` Directory
- **Purpose**: Implementation guidance and technical background
- **Include**: Deep dives, platform-specific notes, algorithm explanations
- **Examples**: Performance optimization, API patterns, design rationale
- **Preserve**: These documents provide essential developer context

## Reorganization Steps

1. Read all `.md` and `.py` files to understand current state
2. Archive outdated or redundant content in `./old/`
3. Preserve technical documentation in `./doc/`
4. Write README.md and SPECIFICATION.md with zero overlap
5. Create or update build.py and test.py scripts
6. Maintain brevity—this is minimum-viable scope

## Core Principles

- **Error handling**: Basic validation only
- **Edge cases**: Realistic scenarios exclusively
- **Constraints**: Necessary requirements only
- **Code examples**: Minimal to none in specifications
- **Document overlap**: Eliminate redundancy
