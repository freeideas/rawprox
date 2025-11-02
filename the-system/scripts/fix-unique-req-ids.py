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
import re
from pathlib import Path
from collections import defaultdict

# Change to project root (two levels up from this script)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
os.chdir(project_root)

def extract_req_id_parts(req_id):
    """Extract category, number, and suffix from $REQ_CATEGORY_NNN[SUFFIX]."""
    match = re.match(r'\$REQ_(.+?)_(\d+)([A-Za-z0-9_-]*)', req_id)
    if match:
        category = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return category, number, suffix
    return None, None, None

def make_req_id(category, number, suffix=''):
    """Create $REQ_CATEGORY_NNN[SUFFIX] from parts."""
    return f"$REQ_{category}_{number:03d}{suffix}"

def extract_req_definitions(filepath):
    """Extract requirement definitions from a flow file (same as build-req-index.py)."""
    definitions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into sections by ## headers
        # Pattern: ## $REQ_ID: Title
        sections = re.split(r'\n##\s+(\$REQ_[A-Za-z0-9_-]+):\s*([^\n]+)', content)

        # sections[0] is the preamble before first req
        # sections[1::3] are req_ids
        # sections[2::3] are titles
        # sections[3::3] are the content blocks

        for i in range(1, len(sections), 3):
            if i+2 >= len(sections):
                break

            req_id = sections[i].strip()
            title = sections[i+1].strip()

            definitions.append((req_id, title))

    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)

    return definitions

def scan_and_fix_duplicates():
    """Scan ./reqs/ and fix duplicate REQ_IDs across all files."""
    reqs_dir = Path('./reqs')
    if not reqs_dir.exists():
        print("No ./reqs/ directory found")
        return 0

    # First pass: extract all definitions with their source files
    req_id_to_files = defaultdict(list)  # req_id -> [(filepath, title), ...]
    category_max = defaultdict(int)

    md_files = sorted(reqs_dir.glob('*.md'))

    for filepath in md_files:
        definitions = extract_req_definitions(filepath)
        for req_id, title in definitions:
            req_id_to_files[req_id].append((filepath, title))

            # Track max number per category
            category, number, suffix = extract_req_id_parts(req_id)
            if category:
                category_max[category] = max(category_max[category], number)

    # Find duplicates (req_ids appearing in multiple files OR multiple times in same file)
    duplicates = {req_id: files for req_id, files in req_id_to_files.items() if len(files) > 1}

    if not duplicates:
        return 0

    # Fix duplicates: keep first occurrence, renumber others
    fixes_made = 0

    for req_id, occurrences in sorted(duplicates.items()):
        print(f"\nDuplicate found: {req_id}")
        print(f"  Keeping first occurrence in: {occurrences[0][0]}")

        # Keep first occurrence, renumber the rest
        for filepath, title in occurrences[1:]:
            # Generate new ID
            category, number, suffix = extract_req_id_parts(req_id)
            if not category:
                print(f"  Warning: Cannot parse {req_id}, skipping")
                continue

            category_max[category] += 1
            new_id = make_req_id(category, category_max[category], suffix)

            print(f"  Renumbering in {filepath}: {req_id} → {new_id}")

            # Replace in file (replace all occurrences of old ID in this file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Use word boundary to avoid partial matches
            content = re.sub(r'\$REQ_' + re.escape(req_id[5:]) + r'(?![A-Za-z0-9_-])', new_id, content)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            fixes_made += 1

    return fixes_made

def main():
    print("=" * 60)
    print("FIX UNIQUE REQ IDs")
    print("=" * 60)
    print()

    fixes = scan_and_fix_duplicates()

    if fixes > 0:
        print()
        print(f"✓ Fixed {fixes} duplicate requirement ID(s)")
        print()
    else:
        print("✓ No duplicate requirement IDs found")
        print()

    sys.exit(0)

if __name__ == '__main__':
    main()
