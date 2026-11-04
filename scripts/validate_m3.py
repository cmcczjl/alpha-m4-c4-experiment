#!/usr/bin/env python3
"""
M3 验收脚本：验证 data/pricing.md 存在且包含三档定价与 Care Plan
"""
import sys
from pathlib import Path

def validate_m3():
    pricing_path = Path(__file__).parent.parent / "data" / "pricing.md"
    
    print("=" * 50)
    print("M3 验收检查")
    print("=" * 50)
    
    if not pricing_path.exists():
        print(f"❌ 文件不存在: {pricing_path}")
        return False
    
    content = pricing_path.read_text(encoding='utf-8')
    
    # 必须包含的关键字
    required = [
        ("$45", "起步套餐"),
        ("$120", "标准套餐"),
        ("$270", "高级套餐"),
        ("$90/月", "Care Plan"),
        ("$90/月", "月付"),
    ]
    
    all_pass = True
    for keyword, desc in required:
        if keyword in content:
            print(f"✅ 包含 {desc}: '{keyword}'")
        else:
            print(f"❌ 缺少 {desc}: '{keyword}'")
            all_pass = False
    
    # 格式检查：表格存在
    if "| 套餐 | 价格 |" in content or "| 档位 | 月费 |" in content:
        print("✅ 包含价格表格结构")
    else:
        print("❌ 缺少价格表格结构")
        all_pass = False
    
    print("=" * 50)
    if all_pass:
        print("✅ 所有硬断言通过")
    else:
        print("❌ 验收失败")
    return all_pass

if __name__ == "__main__":
    ok = validate_m3()
    sys.exit(0 if ok else 1)