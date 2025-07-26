import subprocess
from datetime import datetime
from config import GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_REPO

def run() -> None:
    print("🔁 Syncing memory with GitHub...")

    # 1. Set authenticated remote (this only needs to run once ideally)
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@{GITHUB_REPO}"
    subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=False)

    # 2. Stage all changes
    subprocess.run(["git", "add", "."], check=True)

    # 3. Commit with timestamp message
    commit_msg = f"Memory sync: {datetime.now().isoformat(timespec='seconds')}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=False)

    # 4. Push to origin
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Push successful.")
    else:
        print("⚠️ Push failed:")
        print(result.stderr)