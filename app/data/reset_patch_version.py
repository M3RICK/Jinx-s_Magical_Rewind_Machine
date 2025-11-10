#!/usr/bin/env python3
"""
Reset the patch version in the database to force a sync.

This will set the patch version to None, causing the next sync
to detect a "new patch" and re-populate all League data.
"""

import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'league_data.db')

def reset_patch_version():
    """Reset the patch version to None to force a sync."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check current version
        cursor.execute("SELECT version FROM patch_version WHERE id = 1")
        result = cursor.fetchone()
        current_version = result[0] if result else None

        print(f"Current patch version: {current_version}")

        # Reset to None
        cursor.execute("DELETE FROM patch_version WHERE id = 1")
        conn.commit()

        print("Patch version reset! Next sync will re-populate all data.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_patch_version()
