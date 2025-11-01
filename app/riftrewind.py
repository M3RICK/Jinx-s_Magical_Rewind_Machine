#!/usr/bin/env python3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.chat import run_chat
from cli.sync import run_sync

VERSION = "1.0.0"

def print_help():
    print("\nRiftRewind CLI - Available Commands:")
    print("-" * 50)
    print("  chat        Start AI coaching chat with player lookup")
    print("  sync        Sync databases with Riot API data")
    print("  help        Show this help message")
    print("  version     Show version information")
    print("  exit        Exit RiftRewind CLI")
    print("-" * 50)
    print()

def print_banner():
    print("\n" + "=" * 50)
    print(f"  RiftRewind CLI v{VERSION}")
    print("  League of Legends Analysis & Coaching Tool")
    print("=" * 50)
    print("\nType 'help' for available commands\n")

def main():
    print_banner()

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            # Parse command and arguments (keep original case for args)
            parts = user_input.split()
            command = parts[0].lower()  # Normalize command to lowercase
            args = parts[1:] if len(parts) > 1 else []

            # Route commands using match/case
            match command:
                case "help":
                    print_help()
                case "version":
                    print(f"RiftRewind CLI v{VERSION}")
                case "chat":
                    run_chat()
                case "sync":
                    run_sync()
                case "exit" | "quit" | "q" | "bye" | "kill":
                    print("\nGoodbye!")
                    break
                case _:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
        except KeyboardInterrupt:
            print("\n\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
