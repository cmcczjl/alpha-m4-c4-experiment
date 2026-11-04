#!/usr/bin/env python3
import os

def list_dir(root):
    for dirpath, dirnames, filenames in os.walk(root):
        level = dirpath.replace(root, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(dirpath)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in filenames:
            print(f"{subindent}{f}")

if __name__ == "__main__":
    # List the repository from the current directory
    list_dir('.')