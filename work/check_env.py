#!/usr/bin/env python3
import os

def check_module(name: str) -> str:
    try:
        __import__(name)
        return f"Module '{name}' imported successfully."
    except Exception as e:
        return f"Module '{name}' import failed: {e}"

def check_file(path: str) -> str:
    if not os.path.exists(path):
        return f"File '{path}' does not exist."
    if not os.path.isfile(path):
        return f"'{path}' is not a regular file."
    if not os.access(path, os.R_OK):
        return f"File '{path}' is not readable."
    return f"File '{path}' exists and is readable."

def main() -> None:
    modules = ["n8n", "make"]
    files = ["data/market_leads.json", "work/search_bounty.py"]

    for mod in modules:
        print(check_module(mod))
    for f in files:
        print(check_file(f))

if __name__ == "__main__":
    main()