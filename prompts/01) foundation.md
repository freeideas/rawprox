Please read @FOUNDATION.md and then create the skeleton of this project.

1) README.md - a background about this project; written for all audiences.
2) SPECIFICATION.md - the specification of the project; written for experienced developers who have already read README.md.
3) ./scripts/build.py - builds the final output, and copies it to ./release/
4) ./scripts/test.py - runs build.py and then finds and runs every test_*.py file in the ./scripts/ directory. Each of these test_*.py tests the binary in the ./release/ directory.
5) ./release/ directory, which will contain the final binary

Remember that we run .py scripts with uv run --script; not python directly.

Do not create arbitrary specifications that would be easily discovered by the developers with real-life experience.

Do not compare or contrast with previous designs; we are not historians; we are concerned only with the current design; no traces of previous incarnations should exist in documentation nor in code.

This is a minimum viable project. Do not include anything that is nice to have, do not cover edge cases unless we are sure they will actually be needed, and whatever naturally happens in error conditions is probably good enough.