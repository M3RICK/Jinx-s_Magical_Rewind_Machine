import sys
import os
import subprocess

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_sync():
    """Sync databases with Riot API data."""
    print("db sync")
    # TODO: Implement database synchronization logic
