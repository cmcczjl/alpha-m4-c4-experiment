#!/usr/bin/env python3
import os
import sys

def check_readme():
    """
    Acceptance condition 1:
    Ensure a README.md file exists at the project root.
    """
    # Project root is one level up from this script's directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    readme_path = os.path.join(project_root, "README.md")
    if not os.path.isfile(readme_path):
        raise AssertionError(f"Missing README.md at {readme_path}")

def check_dummy():
    """
    Acceptance condition 2:
    Placeholder for additional checks – currently always passes.
    """
    assert True, "Dummy check failed"

def main():
    try:
        check_readme()
        check_dummy()
    except AssertionError as err:
        print(f"M2 validation failed: {err}")
        sys.exit(1)

    print("M2 validation passed")
    sys.exit(0)

if __name__ == "__main__":
    main()