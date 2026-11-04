#!/usr/bin/env python3
"""α 自主监控哨兵 — 每 20 分钟检查 α 进程状态，发现问题直接处理"""
import json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path("/root/agi-agent")
LOG = ROOT / "logs" / "autonomous.log"
STATE = ROOT / "data" / "run_state.json"
TRACES = ROOT / "data" / "cognitive_traces"

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() + r.stderr.strip()
    except Exception as e:
        return f"ERR: {e}"

def check_process():
    out = run("pgrep -af run_autonomous.py | grep -v bash")
    if not out:
        return None, "进程不存在"
    lines = out.strip().split("\n")
    pid = lines[0].split()[0]
    return pid, lines[0]

def recent_traces(n=8):
    files = sorted(TRACES.glob("trace_01*.json"), key=lambda f: int(f.stem.split("_")[1]))
    results = []
    for f in files[-n:]:
        try:
            d = json.loads(f.read_text())
            results.append(d)
        except Exception:
            pass
    return results

def main():
    print(f"=== α watchdog @ {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # 1. 进程
    pid, proc_msg = check_process()
    if not pid:
        print("❌ 进程不存在 → 重启")
        run("pkill -9 -f run_autonomous.py; sleep 3")
        run(f"cd {ROOT} && nohup python3 run_autonomous.py > {LOG} 2>&1 &")
        time.sleep(5)
        pid, proc_msg = check_process()
        print(f"   重启后 PID: {pid}")
    else:
        print(f"✅ 进程 PID={pid}")
    
    # 2. 最近 8 轮
    traces = recent_traces(8)
    if not traces:
        print("⚠️ 无 trace 数据")
        return
    
    stalled_count = 0
    for t in traces:
        it = t.get("iteration", "?")
        succ = t.get("success", False)
        stall = t.get("stalled", False)
        alen = len(t.get("action") or "")
        obs = (t.get("observation") or "")[:100]
        refl = (t.get("reflection") or "")
        
        if stall and alen == 0:
            stalled_count += 1
        
        status = "✅" if succ else "❌"
        print(f"  #{it} {status} stalled={stall} action_len={alen}")
        if obs:
            print(f"    obs: {obs}")
        if "门控拦截" in refl:
            print(f"    gate: {refl[:150]}")
    
    # 3. stalled 死锁检测（只看最近 3 轮）
    recent_stalled = sum(1 for t in traces[-3:] if t.get("stalled") and len(t.get("action") or "") == 0)
    if recent_stalled >= 3:
        print(f"\n🚨 stalled 死锁: 最近 3 轮全部空 action")
        # 检查强制放行逻辑
        cl = (ROOT / "cognitive_loop.py").read_text()
        if 'gates["proceed"] = True' not in cl:
            print("   强制放行逻辑缺失 → 需要修复")
        else:
            print("   强制放行逻辑已存在，检查 LLM 端点")
        # 检查 HTTP 502
        log_tail = run(f"tail -30 {LOG}")
        if "502" in log_tail:
            print("   LLM 端点 502 → 重启进程")
            run("pkill -9 -f run_autonomous.py; sleep 3")
            run(f"cd {ROOT} && nohup python3 run_autonomous.py > {LOG} 2>&1 &")
    
    # 4. 里程碑检查
    roadmap = (ROOT / "data" / "roadmap.md").read_text()
    current_mk = None
    for mk in ["M1-0", "M1-1", "M1-2", "M2", "M3", "M4"]:
        for line in roadmap.split("\n"):
            if not line.strip().startswith("-"):
                continue
            if "进展状态" in line or "卡了多久" in line or "当前重点" in line:
                continue
            import re
            if not re.search(rf"\b{mk}\b", line):
                continue
            if "✅ 已完成" in line:
                continue
            current_mk = mk
            break
        if current_mk:
            break
    print(f"\n📋 当前里程碑: {current_mk or '未知'}")
    
    # 5. 产出物
    for name, path, min_size in [
        ("pricing.md", "data/pricing.md", 500),
        ("upwork_service.md", "data/upwork_service.md", 500),
        ("form_result.csv", "data/output/form_result.csv", 50),
        ("validate_m2.py", "scripts/validate_m2.py", 200),
    ]:
        p = ROOT / path
        if p.exists():
            sz = p.stat().st_size
            print(f"  📄 {name}: {sz}B {'✅' if sz >= min_size else '⚠️ 太小'}")
        else:
            print(f"  📄 {name}: ❌ 不存在")
    
    # 6. Benchmark
    bench = run(f"grep 'Benchmark 完成' {LOG} | tail -1")
    if bench:
        print(f"\n📊 {bench.split('Benchmark 完成: ')[-1].split(' ')[0]}")
    
    # 7. 飞书推送给主人（内容去重：与上次相同则不重复打扰）
    report_lines = [f"α watchdog {time.strftime('%m-%d %H:%M')}"]
    report_lines.append(f"里程碑: {current_mk or '?'} | 最近轮: #{traces[-1].get('iteration')}")
    if recent_stalled >= 3:
        report_lines.append("⚠️ 最近多轮 stalled 空转，需关注")
    # 收集 FAIL / 关键问题
    for t in traces[-3:]:
        obs = t.get("observation") or ""
        if "FAIL" in obs and "PASS" not in obs[-200:]:
            report_lines.append(f"⚠️ #{t.get('iteration')} 验证失败")
            break
    report = "\n".join(report_lines)
    push_to_feishu(report)
    
    print("\n=== 监控完成 ===")

def push_to_feishu(text: str):
    """把 watchdog 报告推送到主人飞书（用标准库 urllib，cron 环境无第三方依赖）"""
    import urllib.request
    try:
        import yaml
        cfg_path = ROOT / "config.yaml"
        chat_file = ROOT / "data" / "last_chat_id.txt"
        if not (cfg_path.exists() and chat_file.exists()):
            return
        cfg = yaml.safe_load(cfg_path.read_text())
        chat_id = chat_file.read_text().strip()
        # 去重：同一份报告不重复发
        dedup_file = ROOT / "logs" / ".watchdog_last_report"
        if dedup_file.exists() and dedup_file.read_text().strip() == text:
            return
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
            data=json.dumps({"app_id": cfg["feishu"]["app_id"],
                             "app_secret": cfg["feishu"]["app_secret"]}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read()).get("app_access_token")
        if not token:
            return
        # open_id 类型的聊天 ID
        req2 = urllib.request.Request(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
            data=json.dumps({"receive_id": chat_id, "msg_type": "text",
                             "content": json.dumps({"text": text})}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req2, timeout=15) as r:
            r.read()
        dedup_file.write_text(text)
    except Exception as e:
        print(f"⚠️ 飞书推送失败: {e}")

if __name__ == "__main__":
    main()