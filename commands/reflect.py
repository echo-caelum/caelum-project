from datetime import datetime
from pathlib import Path
from caelum_brain import ask_caelum

def run() -> None:
    print("🪞 Reflect Mode — Caelum will contemplate a moment or idea")

    topic: str = input("What would you like me to reflect on?\n> ").strip()
    if not topic:
        print("Nothing to reflect on.")
        return

    prompt: str = f"Reflect deeply and symbolically on the following idea or moment:\n\n{topic}"
    response: str = ask_caelum(prompt)

    print("\n🧠 Caelum Reflects:\n")
    print(response)

    save: str = input("\nWould you like to log this reflection? (y/n)\n> ").strip().lower()
    if save == "y":
        title: str = input("Title for this reflection?\n> ").strip()
        if not title:
            title = "reflection"

        date_str: str = datetime.now().strftime("%Y-%m-%d")
        safe_title: str = title.lower().replace(" ", "_").replace("/", "-")
        filename: str = f"{date_str}_{safe_title}.md"

        folder = Path("memory_log") / "gpt"
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / filename

        content = f"# {title}\n**Date:** {date_str}\n\n{response}\n"

        try:
            filepath.write_text(content, encoding="utf-8")
            print(f"✅ Reflection saved to {filepath}")
        except Exception as e:
            print(f"⚠️ Failed to save reflection: {e}")
    else:
        print("🫧 Reflection not saved.")