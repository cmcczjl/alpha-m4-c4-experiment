import os, subprocess, json

# 1. 当前目录
cwd = os.getcwd()

# 2. 当前目录内容
ls = subprocess.run(["ls", "-la"], capture_output=True, text=True)

# 3. 全盘搜索 act_check.py（限制在常见路径，避免 /proc 等噪声）
search_roots = ["/home", "/root", "/opt", "/tmp", "/usr/local", "/workspace", "/data"]
found = []
for root in search_roots:
    if not os.path.isdir(root):
        continue
    r = subprocess.run(
        ["find", root, "-name", "act_check.py", "-type", "f"],
        capture_output=True, text=True, timeout=30
    )
    if r.stdout.strip():
        found.extend(r.stdout.strip().splitlines())

# 4. 兜底：再搜 / 但排除 /proc /sys /dev
if not found:
    r = subprocess.run(
        ["find", "/", "-path", "/proc", "-prune", "-o", "-path", "/sys", "-prune",
         "-o", "-path", "/dev", "-prune", "-o", "-name", "act_check.py", "-type", "f", "-print"],
        capture_output=True, text=True, timeout=60
    )
    if r.stdout.strip():
        found.extend(r.stdout.strip().splitlines())

result = {
    "cwd": cwd,
    "ls": ls.stdout,
    "act_check_py_paths": found,
    "exists": len(found) > 0
}
print(json.dumps(result, indent=2, ensure_ascii=False))