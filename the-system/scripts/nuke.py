#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Nuke script: Moves all unprotected items to a timestamped temp directory.

SAFE APPROACH: First runs cleanup.py, then moves everything except protected items
into a timestamped directory in the OS temp folder.

Protected items (NEVER moved):
  - ./README.md
  - ./readme/
  - ./the-system/
  - ./subprojects/

Everything else gets moved to: {TEMP}/nuke_backup_{timestamp}/
"""

import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Items to PROTECT (never move these)
PROTECTED_ITEMS = {
    'README.md',
    'readme',
    'the-system',
    'subprojects',
    'doc',
    'docs',
}

def get_project_root():
    """Get the project root directory (parent of the-system)."""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent.parent

def run_cleanup():
    """Run cleanup.py script first."""
    cleanup_script = Path(__file__).parent / 'cleanup.py'
    if cleanup_script.exists():
        print("🧹 Running cleanup.py first...")
        try:
            subprocess.run(['uv', 'run', '--script', str(cleanup_script)], check=True)
            print()
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: cleanup.py failed: {e}")
            print()

def nuke_project():
    """Move all unprotected items to a timestamped temp directory."""
    project_root = get_project_root()

    # Run cleanup first
    run_cleanup()

    print(f"🔥 Nuking project at: {project_root}")
    print()
    print("🛡️  Protected items (will NOT be moved):")
    for item in sorted(PROTECTED_ITEMS):
        print(f"   - ./{item}")
    print()

    # Find items to move
    items_to_move = []
    for item in project_root.iterdir():
        if item.name not in PROTECTED_ITEMS and not item.name.startswith('.'):
            items_to_move.append(item)

    if not items_to_move:
        print("✅ Nothing to move (all items are protected)")
        return

    print("📦 Items to move:")
    for item in sorted(items_to_move):
        item_type = "📁" if item.is_dir() else "📄"
        print(f"   {item_type} ./{item.name}")
    print()

    # Confirm operation
    response = input("⚠️  Proceed with moving items to temp directory? [y/N]: ")
    if response.lower() != 'y':
        print("❌ Aborted")
        return

    # Create timestamped backup directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    temp_dir = Path(tempfile.gettempdir())
    backup_dir = temp_dir / f"nuke_backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    print()
    print(f"📂 Moving items to: {backup_dir}")
    print()

    # Move items
    moved_items = []
    for item in items_to_move:
        try:
            dest = backup_dir / item.name
            shutil.move(str(item), str(dest))
            item_type = "📁" if dest.is_dir() else "📄"
            print(f"✓ Moved {item_type} {item.name}")
            moved_items.append(item.name)
        except Exception as e:
            print(f"✗ Failed to move {item.name}: {e}")

    print()
    print("✅ Nuke complete")
    print()
    print(f"📦 Moved {len(moved_items)} item(s) to:")
    print(f"   {backup_dir}")
    print()
    print("NOTE: Protected items remain in the project directory.")

if __name__ == '__main__':
    try:
        nuke_project()
    except KeyboardInterrupt:
        print()
        print("❌ Aborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
