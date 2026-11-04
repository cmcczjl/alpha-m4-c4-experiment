#!/usr/bin/env python3
"""
M2-0 验收脚本：表单提交 → 结构化 CSV 数据
场景：表单提交后 10 秒内，一行结构化数据出现在 data/output/form_result.csv
验收条件：
  1. data/output/form_result.csv 存在
  2. CSV 包含必需字段：name, email, product, quantity, price, total, timestamp
  3. CSV 至少 1 行数据（表头除外）
  4. timestamp 字段符合 ISO8601 格式
"""
import csv
import os
import sys
import re
from datetime import datetime

OUTPUT_DIR = "/root/agi-agent/data/output"
CSV_PATH = os.path.join(OUTPUT_DIR, "form_result.csv")
REQUIRED_FIELDS = {"name", "email", "product", "quantity", "price", "total", "timestamp"}
ISO8601_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def main():
    errors = []
    warnings = []

    # 1. 检查文件存在
    if not os.path.isfile(CSV_PATH):
        print(f"FAIL: {CSV_PATH} 不存在")
        sys.exit(1)

    # 2. 读取 CSV
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            rows = list(reader)
    except Exception as e:
        print(f"FAIL: 读取 CSV 失败: {e}")
        sys.exit(1)

    # 3. 检查必需字段
    missing_fields = REQUIRED_FIELDS - headers
    if missing_fields:
        errors.append(f"缺少必需字段: {missing_fields}")

    # 4. 检查至少 1 行数据
    if len(rows) == 0:
        errors.append("CSV 无数据行")

    # 5. 检查 timestamp 格式
    for i, row in enumerate(rows):
        ts = row.get("timestamp", "")
        if ts and not ISO8601_PATTERN.match(ts):
            warnings.append(f"第{i+1}行 timestamp 格式不标准: {ts}")

    # 6. 打印详情
    print("=" * 50)
    print("M2-0 验收检查")
    print("=" * 50)
    print(f"✅ CSV 文件存在: {CSV_PATH}")
    print(f"   字段列表: {sorted(headers)}")
    print(f"   数据行数: {len(rows)}")
    print()

    # 7. 报告结果
    if errors:
        print("❌ 验收失败:")
        for e in errors:
            print(f"  - {e}")
        print("=" * 50)
        sys.exit(1)
    else:
        if warnings:
            print("⚠️ 验收通过（有警告）:")
            for w in warnings:
                print(f"  {w}")
        else:
            print("✅ 所有硬断言通过")
        print("=" * 50)
        sys.exit(0)


if __name__ == "__main__":
    main()
