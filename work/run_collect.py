#!/usr/bin/env python3
import subprocess
import sys
import os

def run_collect():
    """Run the RAG corpus collection script."""
    print("Running corpus collection...")
    result = subprocess.run(
        ['python3', 'scripts/collect_rag_corpus.py'],
        capture_output=True,
        text=True
    )
    print("=== collect_rag_corpus.py output ===")
    print(result.stdout)
    if result.returncode != 0:
        print("collect_rag_corpus.py failed with exit code", result.returncode, file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout

def run_retrieval_check():
    """Run the retrieval quality check script if it exists."""
    check_script = 'scripts/retrieval_check.py'
    if not os.path.isfile(check_script):
        print(f"检索检查脚本 {check_script} 未找到，跳过检索质量验证。")
        return
    print("Running retrieval quality check...")
    result = subprocess.run(
        ['python3', check_script],
        capture_output=True,
        text=True
    )
    print("=== retrieval_check.py output ===")
    print(result.stdout)
    if result.returncode != 0:
        print("retrieval_check.py 失败，退出码", result.returncode, file=sys.stderr)
        sys.exit(result.returncode)
    # 简单检查 hit rate 是否 ≥80%
    if "hit rate" in result.stdout.lower() and "80%" in result.stdout:
        print("✅ 检索 hit rate ≥80%")
    else:
        print("⚠️ 检索 hit rate <80%")
        sys.exit(1)

def main():
    collect_output = run_collect()
    run_retrieval_check()
    print("✅ 所有步骤完成。")

if __name__ == "__main__":
    main()