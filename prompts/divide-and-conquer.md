# Divide and Conquer Strategy

When you encounter troublesome or complex code files, apply this refactoring strategy:

## Core Principle

**Separate simple from tricky.** Split difficult code files into two or more files, isolating straightforward logic from complex or not-well-understood portions.

## Benefits

- **Stabilization**: Simple, well-understood code becomes stable and reliable
- **Focus**: Tricky code receives exclusive attention without affecting stable parts
- **Maintainability**: Easier to reason about, test, and modify each component
- **Reduced risk**: Changes to complex logic don't destabilize simple functionality

## Application

When a code file proves difficult to work with:

1. **Identify** the simple vs. tricky portions
2. **Extract** straightforward logic into separate file(s)
3. **Isolate** complex/tricky logic in dedicated file(s)
4. **Connect** via clear interfaces

This allows the simple parts to stabilize while you iterate on the challenging portions.

## Documentation

**ACTION REQUIRED**: Add a brief description of this strategy to both:
- `@FOUNDATION.md` - Add to the core principles/patterns section
- `@SPECIFICATION.md` - Add to the implementation guidelines/refactoring section

The description should be concise (2-3 sentences) capturing the core principle: separate simple from tricky code into different files to stabilize well-understood logic while focusing iteration on complex portions.
