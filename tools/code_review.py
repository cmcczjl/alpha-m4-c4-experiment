#!/usr/bin/env python3
import sys
import argparse
import ast
import textwrap

def analyze_code(source: str) -> str:
    """
    Very simple static analysis:
    - Syntax check (via ast.parse)
    - Detect functions without docstrings
    - Detect overly long lines (> 120 chars)
    Returns a multi‑line review string.
    """
    review_lines = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"❌ Syntax error: {e.msg} (line {e.lineno})"

    # Check for functions without docstrings
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if not doc:
                review_lines.append(f"⚠️ Function `{node.name}` is missing a docstring.")

    # Check line length
    for i, line in enumerate(source.splitlines(), start=1):
        if len(line) > 120:
            review_lines.append(f"⚠️ Line {i} exceeds 120 characters ({len(line)} chars).")

    if not review_lines:
        review_lines.append("✅ No obvious issues found.")
    return "\n".join(review_lines)

def main():
    parser = argparse.ArgumentParser(
        description="Simple AI‑style code reviewer."
    )
    parser.add_argument(
        "code",
        nargs="?",
        help="Path to a file containing code to review. If omitted, reads from STDIN."
    )
    args = parser.parse_args()

    if args.code:
        try:
            with open(args.code, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        source = sys.stdin.read()

    if not source.strip():
        print("No code provided.", file=sys.stderr)
        sys.exit(1)

    review = analyze_code(source)
    print(review)

if __name__ == "__main__":
    main()