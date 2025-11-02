"""
Script to create the new database tables.
Run this once to set up MatchHistory, Conversations, and Sessions tables.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from init_tables import init_all_tables

if __name__ == "__main__":
    print("Setting up new database tables...")
    print("This will create: MatchHistory, Conversations, Sessions")
    print("(Players table already exists and will be skipped)\n")

    init_all_tables()

    print("\n✓ Setup complete!")
