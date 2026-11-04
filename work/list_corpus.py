#!/usr/bin/env python3
import os

def main():
    path = "/root/agi-agent/scripts/rag_corpus/"
    try:
        files = os.listdir(path)
        for f in files:
            print(f)
    except Exception as e:
        print(f"Error listing {path}: {e}")

if __name__ == "__main__":
    main()