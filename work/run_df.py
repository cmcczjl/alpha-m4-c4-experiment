#!/usr/bin/env python3
import subprocess, sys
result = subprocess.run(['df', '-h'], capture_output=True, text=True)
print(result.stdout)