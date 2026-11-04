#!/usr/bin/env python3
import zipfile
import hashlib
import sys
import os

def compute_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def main(zip_path: str):
    if not os.path.isfile(zip_path):
        print(f"Error: '{zip_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                # Skip directories
                if info.is_dir():
                    continue
                file_data = zf.read(info.filename)
                md5_hash = compute_md5(file_data)
                print(f"{info.filename}: {md5_hash}")
    except zipfile.BadZipFile:
        print(f"Error: '{zip_path}' is not a valid zip file.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 默认压缩包名称为 deliverable.zip，可通过命令行参数覆盖
    zip_file = sys.argv[1] if len(sys.argv) > 1 else "deliverable.zip"
    main(zip_file)