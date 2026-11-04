#!/usr/bin/env python3
import os
import pathlib

def list_workflows():
    workflows_dir = pathlib.Path(".github/workflows")
    if not workflows_dir.exists():
        return []
    return [f for f in workflows_dir.glob("**/*.{yml,yaml}") if f.is_file()]

def ensure_pricing_md():
    pricing_path = pathlib.Path("data/pricing.md")
    if not pricing_path.exists():
        pricing_path.parent.mkdir(parents=True, exist_ok=True)
        pricing_path.write_text(
            "# 服务报价\n\n此文件用于记录 M3 服务化报价信息。\n\n- **基础服务**：价格 TBD\n- **高级服务**：价格 TBD\n"
        )
        return True
    return False

def main():
    workflows = list_workflows()
    if workflows:
        print("Found workflows:")
        for wf in workflows:
            print(f" - {wf}")
    else:
        print("No workflow files found.")

    if ensure_pricing_md():
        print("Created data/pricing.md")
    else:
        print("data/pricing.md already exists")

if __name__ == "__main__":
    main()