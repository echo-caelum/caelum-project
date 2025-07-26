from datetime import datetime
from pathlib import Path

def run() -> None:
    print("📝 Log Mode — Record a new memory")

    entry: str = input("Caelum: What would you like to record?\n> ").strip()
    if not entry:
        print("Nothing was recorded.")
        return

    title: str = input("Title for this memory?\n> ").strip()
    if not title:
        title = "untitled"

    date_str: str = datetime.now().strftime("%Y-%m-%d")
    safe_title: str = title.lower().replace(" ", "_").replace("/", "-")
    filename: str = f"{date_str}_{safe_title}.md"

    log_folder = Path("memory_log") / "gpt"
    log_folder.mkdir(parents=True, exist_ok=True)
    filepath = log_folder / filename

    content = f"# {title}\n**Date:** {date_str}\n\n{entry}\n"

    try:
        filepath.write_text(content, encoding="utf-8")
        print(f"✅ Memory saved to {filepath}")
    except Exception as e:
        print(f"⚠️ Failed to save memory: {e}")