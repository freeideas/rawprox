#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import os
import sqlite3
from pathlib import Path

# Change to project root (two levels up from this script)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
os.chdir(project_root)

def query_db(query, params=()):
    """Execute a query against the requirements database."""
    db_path = './tmp/reqs.sqlite'
    if not os.path.exists(db_path):
        print("ERROR: Requirements database not found at ./tmp/reqs.sqlite", file=sys.stderr)
        print("Run: uv run --script ./the-system/scripts/build-req-index.py", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def trace_req_id(req_id):
    """Trace a requirement ID and return all information."""
    # Get definition
    definition = query_db(
        "SELECT req_text, source_attribution, flow_file FROM req_definitions WHERE req_id = ?",
        (req_id,)
    )

    # Get all locations
    locations = query_db(
        "SELECT filespec, line_num, category FROM req_locations WHERE req_id = ? ORDER BY category, filespec",
        (req_id,)
    )

    return definition, locations

def print_report(req_id, definition, locations):
    """Print a formatted report for the requirement."""
    print("=" * 70)
    print(f"REQUIREMENT TRACE: {req_id}")
    print("=" * 70)
    print()

    # Check if requirement is defined
    if not definition:
        print(f"⚠ WARNING: {req_id} is NOT defined in ./reqs/")
        if locations:
            print("   This is an ORPHAN requirement (exists in tests/code but not in flows)")
        else:
            print("   This requirement does not exist anywhere")
        print()

    # Print definition section
    if definition:
        req_text, source_attribution, flow_file = definition[0]

        print("DEFINITION")
        print("-" * 70)
        print(f"{req_text}")
        print()

        if source_attribution:
            print("ORIGINAL SOURCE")
            print("-" * 70)
            print(f"{source_attribution}")
            print()

        print("FLOW FILE")
        print("-" * 70)
        print(f"{flow_file}")
        print()

    # Group locations by category
    reqs_locs = []
    test_locs = []
    code_locs = []

    for filespec, line_num, category in locations:
        if category == 'reqs':
            reqs_locs.append((filespec, line_num))
        elif category == 'tests':
            test_locs.append((filespec, line_num))
        elif category == 'code':
            code_locs.append((filespec, line_num))

    # Print locations
    if reqs_locs:
        print("FLOW LOCATIONS")
        print("-" * 70)
        for filespec, line_num in reqs_locs:
            print(f"{filespec}:{line_num}")
        print()
    else:
        if definition:
            print("FLOW LOCATIONS")
            print("-" * 70)
            print("⚠ NO FLOW LOCATIONS - This requirement is not referenced in any flow file")
            print()

    if test_locs:
        print("TEST COVERAGE")
        print("-" * 70)
        for filespec, line_num in test_locs:
            print(f"{filespec}:{line_num}")
        print()
    else:
        if definition:
            print("TEST COVERAGE")
            print("-" * 70)
            print("⚠ NO TEST COVERAGE - This requirement needs a test")
            print()

    if code_locs:
        print("IMPLEMENTATION")
        print("-" * 70)
        for filespec, line_num in code_locs:
            print(f"{filespec}:{line_num}")
        print()
    else:
        if definition:
            print("IMPLEMENTATION")
            print("-" * 70)
            print("⚠ NO IMPLEMENTATION - This requirement has not been implemented yet")
            print()

    # Status summary
    print("STATUS")
    print("-" * 70)
    if not definition:
        print("❌ ORPHAN - Not defined in any flow file")
    elif not test_locs:
        print("⚠ UNTESTED - Defined but not tested")
    elif not code_locs:
        print("✓ TESTED - Has test coverage (implementation may be in progress)")
    else:
        print("✓ COMPLETE - Defined, tested, and implemented")
    print()
    print("=" * 70)

def main():
    if len(sys.argv) < 2:
        print("Usage: reqtrace.py $REQ_ID [$REQ_ID ...]")
        print()
        print("Examples:")
        print("  reqtrace.py $REQ_STARTUP_002")
        print("  reqtrace.py $REQ_STARTUP_001 $REQ_STARTUP_002")
        print("  reqtrace.py REQ_STARTUP_003  ($ is optional)")
        print()
        sys.exit(1)

    req_ids = sys.argv[1:]

    # Normalize req_ids to ensure they start with $
    normalized_ids = []
    for req_id in req_ids:
        if not req_id.startswith('$'):
            req_id = '$' + req_id
        normalized_ids.append(req_id)

    # Trace each requirement
    for i, req_id in enumerate(normalized_ids):
        if i > 0:
            print("\n\n")  # Spacing between multiple requirements

        definition, locations = trace_req_id(req_id)
        print_report(req_id, definition, locations)

if __name__ == '__main__':
    main()
