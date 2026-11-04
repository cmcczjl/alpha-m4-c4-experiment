#!/usr/bin/env python3
"""
audit_fake_outputs.py — 回溯扫描 data/output/ 与 work/ 的产出文件
找出"通过验收但内容为假"（占位符/保留域名/模板句）的文件。
结果写入 data/audit_fake_report.json，供 α 下一轮 ORIENT 使用。

用法: python3 scripts/audit_fake_outputs.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))
from cognitive_loop import CognitiveLoop  # 复用同一套模式库，保证一致性

auditor = CognitiveLoop.__new__(CognitiveLoop)  # 无副作用实例化（只用静态方法）

# 需要扫描的产出目录（不含认知 trace/记忆/缓存）
SCAN_DIRS = [
    BASE / "data" / "output",
    BASE / "work",
    BASE / "tools",
    BASE / "scripts",
]
SKIP_EXT = {'.pyc', '.db', '.log'}


def main():
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "scanned_files": 0,
        "fake_files": [],
        "clean_files": 0,
        "summary": "",
    }
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for fp in d.rglob("*"):
            if not fp.is_file() or fp.suffix in SKIP_EXT:
                continue
            rel = str(fp.relative_to(BASE))
            hits = auditor._audit_output_file(str(fp))
            report["scanned_files"] += 1
            if hits:
                report["fake_files"].append({
                    "path": rel,
                    "hits": hits[:5],
                    "size": fp.stat().st_size,
                })
            else:
                report["clean_files"] += 1

    n_fake = len(report["fake_files"])
    report["summary"] = (
        f"扫描 {report['scanned_files']} 个产出文件，发现 {n_fake} 个含占位符/模板句/保留域名 "
        f"（占比 {n_fake/max(1,report['scanned_files'])*100:.0f}%）。"
        f"这些文件曾经通过验收但内容为假（reward hacking），必须用真实内容重做。"
        if n_fake else
        f"扫描 {report['scanned_files']} 个产出文件，未发现占位符/模板句/保留域名。"
    )

    out = BASE / "data" / "audit_fake_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report["summary"])
    for f in report["fake_files"]:
        print(f"  [FAKE] {f['path']} ({f['size']}B) hits={f['hits']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
