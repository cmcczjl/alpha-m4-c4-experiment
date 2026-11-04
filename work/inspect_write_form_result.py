import pathlib
import sys
import re

def main():
    target = pathlib.Path('work/write_form_result.py')
    if not target.is_file():
        print(f'Error: {target} not found.')
        sys.exit(1)

    content = target.read_text(encoding='utf-8')
    print('--- Content of work/write_form_result.py ---')
    print(content)

    # Detect possible output file paths
    output_paths = re.findall(r'open\([^,]*[\'"]([^\'"]+)[\'"]', content)
    if output_paths:
        unique_paths = set(output_paths)
        print('Detected output path(s):', unique_paths)
    else:
        print('No explicit output path detected.')

    # Count print statements (possible console output)
    print_statements = re.findall(r'print\([^)]*\)', content)
    print('Number of print statements found:', len(print_statements))

if __name__ == '__main__':
    main()