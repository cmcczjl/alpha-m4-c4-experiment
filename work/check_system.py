#!/usr/bin/env python3
import subprocess
import sys

cmd = "df -h; free -h; which python3; which ls; id; find /etc/security -type f -name whitelist.conf"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("ERR:", result.stderr, file=sys.stderr)