#!/usr/bin/env python3
"""
Check GitHub CLI authentication status and log the result.
"""
import subprocess
import datetime
import os

def main():
    # Run `gh auth status` command
    try:
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        error = result.stderr.strip()
    except subprocess.CalledProcessError as e:
        output = e.stdout.strip() if e.stdout else ''
        error = e.stderr.strip() if e.stderr else ''
        output += f"\nError: {e}"
    except FileNotFoundError:
        output = ""
        error = "GitHub CLI (gh) not found. Please install it."

    timestamp = datetime.datetime.utcnow().isoformat()
    log_entry = f"{timestamp} | output:\n{output}\nerror:\n{error}\n{'-'*80}\n"

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    log_path = os.path.join('data', 'gh_auth.log')

    # Append log entry to file
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    # Print to console for immediate visibility
    print(log_entry)

if __name__ == "__main__":
    main()