#!/usr/bin/env python3
import subprocess
import sys

def main():
    # Search for the file under /root
    try:
        result = subprocess.run(
            ["find", "/root", "-type", "f", "-name", "run_check_env.py"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"find command failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Print each found path (there should be at most one)
    for line in result.stdout.strip().splitlines():
        print(line)

if __name__ == "__main__":
    main()