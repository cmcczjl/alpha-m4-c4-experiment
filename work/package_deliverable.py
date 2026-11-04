#!/usr/bin/env python3
"""M4 交付物打包脚本 - 修复版：自动创建输出目录"""
import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# ===== 配置 =====
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "work" / "M4_output"
SOURCE_DIRS = [
    BASE_DIR / "work" / "M4",
    BASE_DIR / "work" / "models",
    BASE_DIR / "work" / "reports",
]
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

def ensure_output_dir():
    """修复点：在检查前用 os.makedirs 创建输出目录"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[OK] 输出目录已就绪: {OUTPUT_DIR}")

def collect_files():
    """收集所有需要打包的源文件"""
    collected = []
    for src in SOURCE_DIRS:
        if not src.exists():
            print(f"[WARN] 源目录不存在，跳过: {src}")
            continue
        for f in src.rglob("*"):
            if f.is_file() and "__pycache__" not in str(f):
                collected.append(f)
    return collected

def compute_md5(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def build_manifest(files):
    manifest = {
        "module": "M4",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "file_count": len(files),
        "files": []
    }
    for f in files:
        rel = str(f.relative_to(BASE_DIR))
        manifest["files"].append({
            "path": rel,
            "size_bytes": f.stat().st_size,
            "md5": compute_md5(f)
        })
    return manifest

def copy_files(files):
    """将源文件复制到输出目录，保留相对结构"""
    copied = 0
    for f in files:
        rel = f.relative_to(BASE_DIR)
        dest = OUTPUT_DIR / rel
        os.makedirs(dest.parent, exist_ok=True)
        shutil.copy2(f, dest)
        copied += 1
    print(f"[OK] 已复制 {copied} 个文件到 {OUTPUT_DIR}")
    return copied

def main():
    # ---- 修复核心：先创建目录 ----
    ensure_output_dir()

    # ---- 收集文件 ----
    files = collect_files()
    if not files:
        print("[WARN] 未找到任何源文件，将生成空 manifest")

    # ---- 复制到输出目录 ----
    copy_files(files)

    # ---- 生成 manifest ----
    manifest = build_manifest(files)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)
    print(f"[OK] Manifest 已写入: {MANIFEST_PATH}")

    # ---- 生成最终 zip ----
    zip_base = OUTPUT_DIR / "M4_deliverable"
    shutil.make_archive(str(zip_base), "zip", root_dir=OUTPUT_DIR)
    print(f"[OK] 交付包已生成: {zip_base}.zip")

    # ---- 汇总 ----
    print("\n===== M4 打包完成 =====")
    print(f"输出目录 : {OUTPUT_DIR}")
    print(f"文件数量 : {manifest['file_count']}")
    print(f"Zip 包   : {zip_base}.zip")
    print(f"Manifest : {MANIFEST_PATH}")

if __name__ == "__main__":
    main()