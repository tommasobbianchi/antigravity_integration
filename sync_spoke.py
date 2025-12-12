import argparse
import json
import os
import requests
import subprocess
import sys
import time

# Default Hub URL (Nativeserver Tailscale IP)
DEFAULT_HUB_URL = "http://100.111.236.92:5000/api/status"
MAX_RETRIES = 10
RETRY_DELAY = 5

def get_hub_status(url):
    for attempt in range(MAX_RETRIES):
        try:
            print(f"[SYNC] Connecting to Hub at {url} (Attempt {attempt + 1}/{MAX_RETRIES})...")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[WARN] Connection failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"[ERROR] Could not connect to Hub after {MAX_RETRIES} attempts.")
                return None

def sync_repo(repo_info, base_dir, dry_run=False):
    name = repo_info.get('name')
    url = repo_info.get('url')
    
    if not name or not url:
        print(f"Invalid repo info: {repo_info}")
        return

    target_dir = os.path.join(base_dir, name)
    
    if os.path.exists(target_dir):
        # Repo exists, pull changes
        print(f"[SYNC] Updating {name}...")
        if not dry_run:
            try:
                # Check if it's a git repo
                if not os.path.exists(os.path.join(target_dir, ".git")):
                     print(f"[WARN] {name} exists but is not a git repo. Skipping.")
                     return

                # Stash local changes to force alignment? Or just pull?
                # "Realign with the data sent by the server" -> implies force or fast-forward
                # For safety, we try pull. If conflict, we might need manual intervention, 
                # but "automatic system" implies we should maybe fail hard or stash.
                # Let's simple pull for now.
                subprocess.run(["git", "pull"], cwd=target_dir, check=True)
                print(f"[SYNC] {name} updated.")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to update {name}: {e}")
    else:
        # Repo missing, clone it
        print(f"[SYNC] Cloning {name} to {target_dir}...")
        if not dry_run:
            try:
                subprocess.run(["git", "clone", url, target_dir], check=True)
                print(f"[SYNC] {name} cloned.")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to clone {name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Synchronize Spoke repositories with Hub.")
    parser.add_argument("--hub", default=DEFAULT_HUB_URL, help="Hub status URL")
    parser.add_argument("--root", default="..", help="Root directory for projects")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    
    args = parser.parse_args()
    
    status = get_hub_status(args.hub)
    
    if not status:
        sys.exit(1)
        
    repos = status.get('repositories', [])
    if not repos:
        print("No repositories listed in Hub status.")
        return

    base_dir = os.path.abspath(args.root)
    print(f"Synchronizing {len(repos)} repositories to {base_dir}...")
    
    for repo in repos:
        sync_repo(repo, base_dir, dry_run=args.dry_run)
        
    print("Synchronization complete.")

if __name__ == "__main__":
    main()
