import subprocess
from config import GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_REPO

def run() -> None:
    print("🔄 Pulling latest memory updates from GitHub...")

    # Ensure remote includes token
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@{GITHUB_REPO}"
    subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=False)

    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Pull successful.\n")
        print(result.stdout)
    else:
        print("⚠️ Pull failed:")
        print(result.stderr)