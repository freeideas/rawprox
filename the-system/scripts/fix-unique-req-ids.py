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
    """Extract category, number, and suffix from $REQ_CATEGORY_NNN[SUFFIX].

    This is a best-effort parser for pretty-formatted IDs like $REQ_STARTUP_001.
    If the ID doesn't match this pattern, returns (None, None, None).
    """
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

def scan_and_fix_duplicates():
    """Scan ./reqs/ and fix duplicate REQ_IDs by renumbering."""
    reqs_dir = Path('./reqs')
    if not reqs_dir.exists():
        print("No ./reqs/ directory found")
        return 0

    # Track seen REQ_IDs and highest number per category
    seen_ids = set()
    category_max = defaultdict(int)
    fixes_made = 0

    # First pass: collect all unique IDs and find max numbers per category
    md_files = sorted(reqs_dir.glob('*.md'))

    for filepath in md_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        req_ids = re.findall(r'\$REQ_[A-Za-z0-9_-]+', content)

        for req_id in req_ids:
            category, number, suffix = extract_req_id_parts(req_id)
            if category:
                if req_id not in seen_ids:
                    seen_ids.add(req_id)
                    # Track max number per category (ignoring suffix for numbering)
                    category_max[category] = max(category_max[category], number)

    # Second pass: fix duplicates
    for filepath in md_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        file_fixes = 0

        # Track IDs seen in this file
        file_seen = set()

        def replace_duplicate(match):
            nonlocal file_fixes
            req_id = match.group(0)
            category, number, suffix = extract_req_id_parts(req_id)

            if req_id in file_seen:
                # Duplicate within same file - renumber (preserve suffix)
                category_max[category] += 1
                new_id = make_req_id(category, category_max[category], suffix)
                print(f"  Fixed: {req_id} → {new_id} in {filepath}")
                file_fixes += 1
                file_seen.add(new_id)
                return new_id
            else:
                file_seen.add(req_id)
                return req_id

        # Replace duplicates
        content = re.sub(r'\$REQ_[A-Za-z0-9_-]+', replace_duplicate, content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_made += file_fixes

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
