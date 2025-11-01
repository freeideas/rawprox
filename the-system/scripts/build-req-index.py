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
import sqlite3
from pathlib import Path

# Change to project root (two levels up from this script)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
os.chdir(project_root)

def extract_req_locations(filepath, category):
    """Extract all $REQ_ID tags from a file with line numbers."""
    locations = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                # Match $REQ_ID pattern (letters, digits, underscores, hyphens)
                matches = re.findall(r'\$REQ_[A-Za-z0-9_-]+', line)
                for req_id in matches:
                    locations.append((req_id, str(filepath), line_num, category))
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
    return locations

def extract_req_definitions(filepath):
    """Extract requirement definitions from a flow file in ./reqs/."""
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
            content_block = sections[i+2].strip()

            # Extract source attribution from content
            source_match = re.search(r'\*\*Source:\*\*\s*([^\n]+)', content_block)
            source_attribution = source_match.group(1).strip() if source_match else ''

            # Extract requirement text (everything after source line)
            if source_match:
                req_text = content_block[source_match.end():].strip()
            else:
                req_text = content_block

            definitions.append((req_id, req_text, source_attribution, str(filepath)))

    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)

    return definitions

def scan_directory(directory, extensions, category):
    """Scan directory for files and extract $REQ_ID locations."""
    locations = []
    if not os.path.exists(directory):
        return locations

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not any(filename.endswith(ext) for ext in extensions):
                continue
            filepath = Path(root) / filename
            locations.extend(extract_req_locations(filepath, category))

    return locations

def build_index():
    """Build the requirements index database."""
    # Create tmp directory
    os.makedirs('./tmp', exist_ok=True)

    # Remove existing database
    db_path = './tmp/reqs.sqlite'
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE req_definitions (
            req_id TEXT PRIMARY KEY,
            req_text TEXT NOT NULL,
            source_attribution TEXT,
            flow_file TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE req_locations (
            req_id TEXT NOT NULL,
            filespec TEXT NOT NULL,
            line_num INTEGER NOT NULL,
            category TEXT NOT NULL
        )
    ''')

    cursor.execute('CREATE INDEX idx_loc_req_id ON req_locations(req_id)')
    cursor.execute('CREATE INDEX idx_loc_category ON req_locations(category)')

    # Scan ./reqs/ for definitions
    definitions = []
    if os.path.exists('./reqs'):
        for req_file in Path('./reqs').glob('*.md'):
            definitions.extend(extract_req_definitions(req_file))

    # Insert definitions
    cursor.executemany('''
        INSERT INTO req_definitions (req_id, req_text, source_attribution, flow_file)
        VALUES (?, ?, ?, ?)
    ''', definitions)

    # Scan all directories for locations
    all_locations = []
    all_locations.extend(scan_directory('./reqs', ['.md'], 'reqs'))
    all_locations.extend(scan_directory('./tests', ['.py'], 'tests'))
    all_locations.extend(scan_directory('./code', ['.py', '.cs', '.go', '.rs', '.java', '.js', '.ts', '.c', '.cpp', '.h'], 'code'))

    # Insert locations
    cursor.executemany('''
        INSERT INTO req_locations (req_id, filespec, line_num, category)
        VALUES (?, ?, ?, ?)
    ''', all_locations)

    conn.commit()

    # Print summary
    cursor.execute('SELECT COUNT(DISTINCT req_id) FROM req_definitions')
    def_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM req_locations WHERE category = "reqs"')
    reqs_loc_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM req_locations WHERE category = "tests"')
    tests_loc_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM req_locations WHERE category = "code"')
    code_loc_count = cursor.fetchone()[0]

    conn.close()

    print(f"Requirements index built: {db_path}")
    print(f"  Definitions: {def_count} unique $REQ_IDs")
    print(f"  Locations:   {reqs_loc_count} in ./reqs/, {tests_loc_count} in ./tests/, {code_loc_count} in ./code/")

def main():
    build_index()

if __name__ == '__main__':
    main()
