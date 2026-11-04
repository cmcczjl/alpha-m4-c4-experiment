#!/usr/bin/env python3
"""
服务器诊断信息采集脚本
用法: python3 collect_diagnostics.py [输出文件路径]
默认输出到 stdout，也可指定文件保存。
"""
import subprocess, sys, os, json, time

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception as e:
        return f"[ERROR] {e}"

def collect():
    data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": run("hostname"),
        "os": run("uname -a"),
        "uptime": run("uptime"),
        "cpu_top": run("top -bn1 | head -20"),
        "memory": run("free -h"),
        "disk": run("df -h"),
        "load_avg": run("cat /proc/loadavg"),
        "cpu_info": run("grep -c ^processor /proc/cpuinfo"),
        "network": run("ss -tunlp 2>/dev/null | head -30 || netstat -tunlp 2>/dev/null | head -30"),
        "top_processes": run("ps aux --sort=-%mem | head -15"),
        "io_wait": run("iostat 1 2 2>/dev/null | tail -20 || vmstat 1 3 | tail -10"),
    }
    return data

if __name__ == "__main__":
    out = collect()
    text = json.dumps(out, indent=2, ensure_ascii=False)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            f.write(text)
        print(f"诊断数据已写入: {sys.argv[1]}")
    else:
        print(text)
    print("\n请将输出发送回进行分析。")