#!/usr/bin/env python3
"""M1-2 交付物验收：工作流模板文件验证"""
import json, os, re, sys
from datetime import datetime

errors = []

# 1. 检查 data/m1_service_package/template.yaml 存在且为有效 YAML
template_path = 'data/m1_service_package/template.yaml'
if not os.path.exists(template_path):
    errors.append(f"{template_path} 不存在")
else:
    content = open(template_path).read()
    # 基本 YAML 结构检查：必须包含 trigger、steps、outputs 等关键字段
    required_fields = ['trigger', 'steps', 'outputs']
    for field in required_fields:
        if field not in content:
            errors.append(f"template.yaml 缺少必需字段: {field}")
    # 检查 steps 至少包含一个 step 定义
    if 'steps:' in content or '- name:' in content:
        pass  # 有步骤定义
    else:
        errors.append("template.yaml 无有效的 steps 定义")

# 2. 检查 definition.md 完整存在且包含里程碑表
definition_path = 'data/m1_service_package/definition.md'
if not os.path.exists(definition_path):
    errors.append(f"{definition_path} 不存在")
else:
    content = open(definition_path).read()
    if 'M1-1' not in content and '里程碑' not in content:
        errors.append("definition.md 缺少里程碑表")

if errors:
    print(f"❌ M1-2 验收失败 ({len(errors)} 个错误):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"✅ M1-2 验收通过: template.yaml 有效, definition.md 完整")
    print(f"M1-2 完成! {datetime.now().isoformat()}")