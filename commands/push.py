# commands/push.py
import subprocess
from datetime import datetime
from typing import Iterable, Optional
from config import GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_REPO

def ensure_remote() -> None:
    """Set the tokenized remote URL (idempotent)."""
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@{GITHUB_REPO}"
    subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=False)

def add_and_commit(message: Optional[str] = None, paths: Optional[Iterable[str]] = None) -> None:
    """Stage and commit. If paths is None, stage all. Commit is skipped if no changes."""
    ensure_remote()
    if paths:
        subprocess.run(["git", "add", *paths], check=True)
    else:
        subprocess.run(["git", "add", "."], check=True)

    if message is None:
        message = f"Memory sync: {datetime.now().isoformat(timespec='seconds')}"

    # commit returns nonzero if nothing to commit; don’t error
    subprocess.run(["git", "commit", "-m", message], check=False)

def push_only() -> bool:
    """Push current HEAD to origin/main. Returns True on success."""
    ensure_remote()
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Push successful.")
        return True
    print("⚠️ Push failed:")
    print(result.stderr)
    return False

def run() -> None:
    """Original behavior: add all, commit with timestamp, push."""
    print("🔁 Syncing memory with GitHub...")
    add_and_commit()      # stage all + commit (if any changes)
    push_only()