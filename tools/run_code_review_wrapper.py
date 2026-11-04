#!/usr/bin/env python3
"""
Wrapper script to run tools/code_review.py on code supplied via stdin or as a command‑line argument.

If the script is called without arguments, it reads the entire stdin as the code to review.
If one argument is supplied, it is treated as the code string to review.
The code is written to a temporary file and the original code_review.py is invoked with that file path.
"""

import sys
import tempfile
import subprocess
import os
from pathlib import Path

def main():
    # Determine the code to review
    if len(sys.argv) > 1:
        # If an argument is supplied, treat it as the code string
        code_str = sys.argv[1]
    else:
        # Otherwise, read from stdin
        code_str = sys.stdin.read()

    if not code_str.strip():
        print("No code provided for review.", file=sys.stderr)
        sys.exit(1)

    # Create a temporary file to hold the code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code_str)
        tmp_path = Path(tmp.name)

    try:
        # Locate the code_review.py script relative to this wrapper
        script_path = Path(__file__).parent / "code_review.py"
        if not script_path.is_file():
            print(f"Error: code_review.py not found at {script_path}", file=sys.stderr)
            sys.exit(1)

        # Execute the code review script with the temporary file as argument
        result = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path)],
            capture_output=True,
            text=True,
            check=False
        )

        # Print stdout and stderr from the code review script
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")

        # Exit with the same return code as the code review script
        sys.exit(result.returncode)

    finally:
        # Clean up the temporary file
        try:
            tmp_path.unlink()
        except Exception:
            pass

if __name__ == "__main__":
    main()