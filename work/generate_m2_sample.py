#!/usr/bin/env python3
import pathlib, re, sys

def main():
    script_path = pathlib.Path("scripts/validate_m2.py")
    if not script_path.is_file():
        print("validate_m2.py not found at scripts/validate_m2.py", file=sys.stderr)
        sys.exit(1)

    content = script_path.read_text(encoding="utf-8")

    # Find all literal paths that look like they point to files under a data/ directory
    # e.g., open('data/input.csv', ...) or Path('data/input.json')
    pattern = re.compile(r"""['"](?P<path>data/[^'"]+)['"]""")
    matches = pattern.findall(content)

    if not matches:
        print("No data file references found in validate_m2.py")
        sys.exit(1)

    data_dir = pathlib.Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    generated = set()
    for rel_path in matches:
        file_path = data_dir / pathlib.Path(rel_path).name  # use only the filename
        if file_path in generated:
            continue
        generated.add(file_path)

        if file_path.suffix.lower() == ".csv":
            file_path.write_text("id,value\n1,example\n", encoding="utf-8")
        elif file_path.suffix.lower() == ".json":
            file_path.write_text("[{\"id\": 1, \"value\": \"example\"}]\n", encoding="utf-8")
        elif file_path.suffix.lower() == ".txt":
            file_path.write_text("example line\n", encoding="utf-8")
        else:
            # generic placeholder
            file_path.write_text("placeholder content\n", encoding="utf-8")
        print(f"Generated sample data file: {file_path}")

    print("All required sample files have been created.")

if __name__ == "__main__":
    main()