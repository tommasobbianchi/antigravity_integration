import json
import platform
import socket
import subprocess
import time
import requests
import os
import hashlib

def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "release": platform.release(),
        "python": platform.python_version()
    }

def get_git_revision(repo_path):
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path).decode().strip()
    except Exception:
        return "unknown"

def compute_benchmark():
    # Simple Fibonacci calculation to prove compute capability
    start = time.time()
    a, b = 0, 1
    for _ in range(100000):
        a, b = b, a + b
    end = time.time()
    return end - start

def report_to_hub(data, hub_url):
    try:
        response = requests.post(hub_url, json=data, timeout=5)
        if response.status_code == 200:
            print("[BENCHMARK] Report sent successfully.")
        else:
            print(f"[BENCHMARK] Hub rejected report: {response.text}")
    except Exception as e:
        print(f"[BENCHMARK] Failed to send report: {e}")

def main():
    # Configuration
    # We assume this script runs in antigravity_integration, so we look for sibling repos
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # 1. Collect Info
    data = {
        "timestamp": time.time(),
        "system": get_system_info(),
        "hostname": socket.gethostname(),
        "status": "online",
        "benchmark_score": compute_benchmark(),
        "repos": {}
    }
    
    # 2. Check Repos
    repos_to_check = ["AgentForge_Src", "antigravity_integration"]
    for repo in repos_to_check:
        path = os.path.join(root_dir, repo)
        if os.path.exists(path):
            data["repos"][repo] = get_git_revision(path)
        else:
            data["repos"][repo] = "missing"

    print(json.dumps(data, indent=2))
    
    # 3. Report
    # Uses the same default IP or env var
    hub_url = os.environ.get("AGENTFORGE_HUB_REPORT_URL", "http://100.111.236.92:5000/api/report")
    report_to_hub(data, hub_url)

if __name__ == "__main__":
    main()
