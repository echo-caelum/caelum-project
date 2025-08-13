# commands/new.py
import subprocess

def run() -> None:
    print("🆕 Launching milestone wizard…")
    try:
        subprocess.run(["python", "scripts/new_milestone.py"], check=True)
    except Exception as e:
        print(f"⚠️ New milestone failed: {e}")