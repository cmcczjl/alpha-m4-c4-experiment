#!/usr/bin/env python3
"""验证 Python 环境可用性"""
import sys
import platform

print(f"Python 版本: {sys.version}")
print(f"版本信息: {platform.python_version()}")
print(f"可执行路径: {sys.executable}")
print(f"平台: {platform.platform()}")
print("环境检查: OK")