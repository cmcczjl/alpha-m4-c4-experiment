#!/usr/bin/env python3
"""Probe data/output/, if empty re-run workflow script with timeout, then verify."""
import os, subprocess, sys, glob

OUT_DIR = "data/output"
SCRIPT = "scripts/workflow_news_digest_v1.py"

# 1) Probe
os.makedirs(OUT_DIR, exist_ok=True)
existing = [f for f in os.listdir(OUT_DIR) if os.path.isfile(os.path.join(OUT_DIR, f))]
print(f"[probe] data/output/ has {len(existing)} file(s): {existing[:5]}")

# 2) If empty or <3 timestamped files, re-run
ts_files = [f for f in existing if len(f) > 10]  # rough timestamp check
if len(ts_files) < 3:
    print("[action] Running workflow script with 30s timeout...")
    if not os.path.isfile(SCRIPT):
        print(f"[error] {SCRIPT} not found. Available scripts:")
        for p in glob.glob("scripts/*.py"):
            print(f"  {p}")
        sys.exit(2)
    r = subprocess.run(
        ["python3", SCRIPT],
        capture_output=True, text=True, timeout=30
    )
    # print last 15 lines of combined output
    lines = (r.stdout + r.stderr).splitlines()
    print("\n".join(lines[-15:]))
    print(f"[exit_code] {r.returncode}")
else:
    print(f"[ok] Already have {len(ts_files)} timestamped files, skipping re-run.")

# 3) Verify
final = sorted(os.listdir(OUT_DIR))
print(f"\n[verify] data/output/ contents: {final}")
print(f"[verify] total files: {len(final)}")