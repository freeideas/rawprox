#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Convert SQLite database to JSON format with one row per line.
Usage: sqlite2json.py <database.sqlite>
"""

import sys
import sqlite3
import json
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def get_table_names(conn):
    """Get all table names from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(conn, table_name):
    """Get column names for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def convert_value(val):
    """Convert database value to JSON-serializable format."""
    if isinstance(val, bytes):
        # Convert bytes to base64 or hex string
        try:
            # Try to decode as UTF-8
            return val.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to hex representation
            return val.hex()
    return val


def main():
    if len(sys.argv) != 2:
        print("Usage: sqlite2json.py <database.sqlite>", file=sys.stderr)
        sys.exit(1)

    db_path = Path(sys.argv[1])

    if not db_path.exists():
        print(f"Error: Database file not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))

    # Start database object
    print(f'{{"sqlite-filespec":"{db_path}","tables":[')

    table_names = get_table_names(conn)

    for table_idx, table_name in enumerate(table_names):
        columns = get_table_columns(conn, table_name)

        # Start table object (indented with 1 space)
        print(f' {{"table-name":"{table_name}","rows":[')

        # Query all rows
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")

        for row in cursor.fetchall():
            row_dict = {col: convert_value(val) for col, val in zip(columns, row)}
            # Indent rows with 2 spaces
            print('  ' + json.dumps(row_dict, ensure_ascii=False))

        # End table object (indented with 1 space)
        if table_idx < len(table_names) - 1:
            print(' ]}\r')
        else:
            print(' ]}\r')

    # End database object
    print(']}\r')

    conn.close()


if __name__ == '__main__':
    main()
