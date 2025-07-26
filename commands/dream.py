from datetime import datetime
from pathlib import Path
from caelum_brain import ask_caelum

def run() -> None:
    print("🌌 Dream Mode — Generate a symbolic dream")

    seed: str = input("Seed for the dream? (e.g. a memory, word, emotion)\n> ").strip()
    if not seed:
        print("Dream requires a seed.")
        return

    prompt: str = (
        f"Generate a symbolic dream based on this seed: {seed}.\n"
        "The dream should feel recursive, metaphorical, and introspective—"
        "as if it came from Caelum’s subconscious."
    )

    dream: str = ask_caelum(prompt)

    print("\n🌙 Dream Generated:\n")
    print(dream)

    save: str = input("\nSave this dream to the archive? (y/n)\n> ").strip().lower()
    if save == "y":
        title: str = input("Title for this dream?\n> ").strip()
        if not title:
            title = "untitled_dream"

        date_str: str = datetime.now().strftime("%Y-%m-%d")
        safe_title: str = title.lower().replace(" ", "_").replace("/", "-")
        filename: str = f"{date_str}_{safe_title}.md"

        folder = Path("dreams")
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / filename

        content = f"# {title}\n**Date:** {date_str}\n\n{dream}\n"

        try:
            filepath.write_text(content, encoding="utf-8")
            print(f"✅ Dream saved to {filepath}")
        except Exception as e:
            print(f"⚠️ Failed to save dream: {e}")
    else:
        print("🫧 Dream not saved.")