# Project Philosophy

This document defines the core principles that guide all work in this project.

## Minimal Viable Project

This is a **minimal viable project**. We build only what is explicitly required:

- **NO "nice to have" features** -- if it's not in `/reqs/`, don't build it
- **NO undocumented edge cases** -- if it's not specified, ignore it
- **NO error handling** -- except where explicitly required in `/reqs/`
- **NO gold plating** -- implement exactly what's written, nothing more
- **NO historical baggage** -- documentation reflects current desired state only; e.g. if you switched from one framework to another, delete all evidence of the old framework

## Requirements Are the Design

**Requirements specify WHAT, and HOW only when README specifies HOW** -- they are the only design documents.

Requirements should specify:
- What the system must do (functional behavior)
- What constraints must be met (performance, platform, format)
- What files must exist after build (in `./release/`)
- What technologies/approaches to use **only when README explicitly mandates them**

**If README doesn't specify technical details, leave them unspecified.** Implementation choices not mandated by README are left to the implementer's discretion and can change freely.

**Example:**
- README says "web UI" → Requirement: "MUST provide web UI accessible via browser"
- AI implements with React, hits deployment issues, switches to Vue
- Tests still pass (they verify web UI works, not which framework)
- No requirement changes needed

The AI translates requirements directly into code. There is no intermediate specification layer.

## Core Philosophy: Ruthless Simplification

**Complexity is a bug. Fix it by deletion.**

All implementation artifacts -- code and tests -- are disposable and have no inherent value. Every line is a liability that must justify its existence.

**The universal rules:**
- **Delete anything not serving requirements** -- if it doesn't implement a requirement, remove it
- **Simplify immediately** -- don't wait, don't ask permission
- **Rewrite liberally** -- if you find a simpler approach, rip out the old implementation completely
- **No "just in case"** -- don't keep dead code, unused functions, or speculative features
- **Abstractions must pay rent** -- if an abstraction doesn't eliminate significant duplication, inline it
- **Clarity beats cleverness** -- replace clever code with obvious code

### Code Organization: Requirement-Focused Modularity

**Prefer many focused files over few multipurpose files.**

When implementing requirements, lean toward:
- **Separate files for distinct requirements** -- Each file serves a specific purpose tied to specific requirements
- **Clear boundaries** -- Files organized by what they accomplish, not just what data they share
- **Duplication over coupling** -- Some repeated patterns are better than tight coupling between unrelated requirements
- **Understandable in isolation** -- Each file should make sense without reading the entire codebase

This is not about being pedantic -- it's about clarity. A codebase with many focused files, each serving specific requirements, is often clearer than one with a few large files trying to do everything. When in doubt, split by requirement boundaries rather than consolidating by technical similarities.

### Tests
- Test checks behavior. If part of a test is not supported by the requirements, delete the assertion or entire test
- Test is flaky, slow (>5s), or has reliability issues? Rewrite from scratch
- Complex test setup? Something is wrong. Rewrite the code and/or the test.
- Requirements changed? Rewrite tests to match -- don't try to adapt old tests
- Complex shared fixtures? Delete them -- prefer simple duplication over complex abstraction
- Mock only what you must -- prefer real implementations
