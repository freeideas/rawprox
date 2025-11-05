#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import shutil
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def cleanup():
    """Delete reports and tmp directories."""
    dirs_to_delete = ['./reports', './tmp']

    for dir_path in dirs_to_delete:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            print(f"Deleted: {dir_path}")
        else:
            print(f"Skipped (not found): {dir_path}")

if __name__ == '__main__':
    cleanup()
