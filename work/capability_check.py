import urllib.request
import subprocess
import os
import json

def verify_capabilities():
    report = {
        "network": {"status": "pending", "details": None},
        "file_system": {"status": "pending", "details": None},
        "pip": {"status": "pending", "details": None}
    }

    # 1. Verify Network (urllib as fallback for requests)
    try:
        response = urllib.request.urlopen("https://api.github.com", timeout=10)
        report["network"]["status"] = "success"
        report["network"]["details"] = f"HTTP {response.getcode()}"
    except Exception as e:
        report["network"]["status"] = "failed"
        report["network"]["details"] = str(e)

    # 2. Verify File System Write
    try:
        os.makedirs('work', exist_ok=True)
        file_path = 'work/test_perm.txt'
        with open(file_path, 'w') as f:
            f.write(f"Network Result: {report['network']['details']}")
        if os.path.exists(file_path):
            report["file_system"]["status"] = "success"
            report["file_system"]["details"] = f"Written to {file_path}"
    except Exception as e:
        report["file_system"]["status"] = "failed"
        report["file_system"]["details"] = str(e)

    # 3. Verify Pip and Subprocess
    try:
        # Try to install tqdm as a lightweight test
        process = subprocess.run(
            ["pip3", "install", "tqdm"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if process.returncode == 0:
            report["pip"]["status"] = "success"
        else:
            report["pip"]["status"] = "failed"
        report["pip"]["details"] = (process.stdout + process.stderr).strip()[:200]
    except Exception as e:
        report["pip"]["status"] = "error"
        report["pip"]["details"] = str(e)

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    verify_capabilities()