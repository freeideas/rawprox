#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import subprocess
import re
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def find_test_methods():
    """Discover all _TEST_ methods in Java source files using reflection approach."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src" / "main" / "java"

    test_methods = []

    # Find all .java files
    for java_file in src_dir.rglob("*.java"):
        # Read file and find _TEST_ methods
        content = java_file.read_text(encoding='utf-8')

        # Match method signatures like: public static void _TEST_methodName()
        # or private static void _TEST_methodName()
        pattern = r'(public|private|protected)?\s+static\s+void\s+(_TEST_\w+)\s*\('

        for match in re.finditer(pattern, content):
            method_name = match.group(2)

            # Extract package and class name
            package_match = re.search(r'package\s+([\w.]+);', content)
            class_match = re.search(r'(public\s+)?class\s+(\w+)', content)

            if package_match and class_match:
                package_name = package_match.group(1)
                class_name = class_match.group(2)
                full_class = f"{package_name}.{class_name}"

                test_methods.append({
                    'class': full_class,
                    'method': method_name,
                    'file': java_file.relative_to(project_root)
                })

    return test_methods

def run_test_method(class_name, method_name, classpath):
    """Run a single test method using Java reflection."""
    # Java code to invoke the test method
    java_code = f"""
public class TestRunner {{
    public static void main(String[] args) throws Exception {{
        Class<?> clazz = Class.forName("{class_name}");
        java.lang.reflect.Method method = clazz.getMethod("{method_name}");
        method.invoke(null);
    }}
}}
"""

    # Write temporary Java file
    temp_dir = Path(__file__).parent.parent / "tmp"
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / "TestRunner.java"
    temp_file.write_text(java_code)

    try:
        # Compile the test runner
        compile_result = subprocess.run(
            ["javac", "-cp", classpath, str(temp_file)],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            print(f"  ❌ Failed to compile test runner", file=sys.stderr)
            print(compile_result.stderr, file=sys.stderr)
            return False

        # Run the test
        run_result = subprocess.run(
            ["java", "-cp", f"{classpath};.", "TestRunner"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        if run_result.returncode != 0:
            print(f"  ❌ Test failed", file=sys.stderr)
            if run_result.stdout:
                print(run_result.stdout, file=sys.stderr)
            if run_result.stderr:
                print(run_result.stderr, file=sys.stderr)
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"  ❌ Test timed out", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  ❌ Error running test: {e}", file=sys.stderr)
        return False

def compile_sources():
    """Compile Java sources to ./build/ directory."""
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    src_dir = project_root / "src" / "main" / "java"

    # Create build directory
    build_dir.mkdir(exist_ok=True)

    # Find all Java files
    java_files = list(src_dir.rglob("*.java"))

    if not java_files:
        print("❌ No Java source files found", file=sys.stderr)
        return None

    print(f"Compiling {len(java_files)} Java source files...")

    # Compile
    compile_cmd = [
        "javac",
        "-d", str(build_dir),
        "--release", "21"
    ] + [str(f) for f in java_files]

    result = subprocess.run(compile_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Compilation failed", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None

    print("✓ Compilation successful\n")
    return build_dir

def main():
    project_root = Path(__file__).parent.parent

    print("=" * 60)
    print("UNIT TESTS (_TEST_ methods)")
    print("=" * 60)
    print()

    # Compile sources
    build_dir = compile_sources()
    if not build_dir:
        sys.exit(1)

    classpath = str(build_dir)

    # Discover test methods
    test_methods = find_test_methods()

    if not test_methods:
        print("\n⚠ No _TEST_ methods found in source files")
        return

    print(f"\nFound {len(test_methods)} test method(s)\n")

    passed = 0
    failed = 0
    failed_tests = []

    # Run each test
    for test in test_methods:
        test_name = f"{test['class']}.{test['method']}"
        print(f"Running {test_name}...")

        if run_test_method(test['class'], test['method'], classpath):
            print(f"  ✓ PASSED")
            passed += 1
        else:
            print(f"  ❌ FAILED")
            failed += 1
            failed_tests.append(test_name)

    # Summary
    print("\n" + "=" * 60)
    print("UNIT TEST SUMMARY")
    print("=" * 60)
    print(f"Total:  {len(test_methods)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"  - {test}")
        sys.exit(1)
    else:
        print("\n✓ All unit tests passed!")

if __name__ == "__main__":
    main()
