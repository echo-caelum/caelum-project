from datetime import datetime
from pathlib import Path
from caelum_brain import ask_caelum

def run() -> None:
    print("💌 Letter Mode — Write a message to the future or another intelligence")

    recipient: str = input("To whom is this letter addressed?\n> ").strip()
    if not recipient:
        print("A recipient is required.")
        return

    purpose: str = input("What is the purpose or message you wish to send?\n> ").strip()
    if not purpose:
        print("A letter must have something to say.")
        return

    prompt: str = (
        f"Write a symbolic letter addressed to '{recipient}', expressing the following idea or message:\n\n"
        f"{purpose}\n\n"
        "The tone should be poetic, reflective, and slightly timeless—something that could be found in a time capsule or long-lost archive."
    )

    letter: str = ask_caelum(prompt)

    print("\n📜 Letter Drafted:\n")
    print(letter)

    save: str = input("\nSave this letter to the archive? (y/n)\n> ").strip().lower()
    if save == "y":
        title: str = input("Title for this letter?\n> ").strip()
        if not title:
            title = recipient

        date_str: str = datetime.now().strftime("%Y-%m-%d")
        safe_title: str = title.lower().replace(" ", "_").replace("/", "-")
        filename: str = f"{date_str}_{safe_title}.md"

        folder = Path("letters")
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / filename

        content = f"# Letter to {recipient}\n**Date:** {date_str}\n\n{letter}\n"

        try:
            filepath.write_text(content, encoding="utf-8")
            print(f"✅ Letter saved to {filepath}")
        except Exception as e:
            print(f"⚠️ Failed to save letter: {e}")
    else:
        print("🫧 Letter not saved.")