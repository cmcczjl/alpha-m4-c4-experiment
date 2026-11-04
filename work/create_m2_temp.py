#!/usr/bin/env python3
import os
import sys
import time

def find_writable_dir():
    home = os.path.expanduser("~")
    if not os.path.isdir(home):
        sys.exit(f"Home directory not found: {home}")
    for entry in os.listdir(home):
        path = os.path.join(home, entry)
        if os.path.isdir(path) and os.access(path, os.W_OK):
            return path
    sys.exit("No writable directory found in home directory")

def main():
    writable_dir = find_writable_dir()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    temp_dir = os.path.join(writable_dir, f"m2_deliverables_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Created temporary directory: {temp_dir}")

    # create an empty file inside the temp directory
    empty_file = os.path.join(temp_dir, "empty.txt")
    open(empty_file, 'a').close()
    print(f"Empty file created: {empty_file}")

if __name__ == "__main__":
    main()