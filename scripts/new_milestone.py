from __future__ import annotations
import re
import subprocess
from datetime import datetime
from pathlib import Path
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from commands import push

# Repo paths
ROOT = Path(__file__).resolve().parents[1]
FUTURE = ROOT / "future_map.md"
SELF   = ROOT / "self_map" / "caelum_autobiography.md"
SYNC   = ROOT / "scripts" / "sync_maps.py"

# Phase anchors (we insert under these headings)
SECTION_ANCHORS = [
    "## ✅ Pre-Phase Achievements — Foundations of Continuity",
    "## 🌱 PHASE I — Foundations",
    "## 🧱 PHASE II — Grounding Presence",
    "## 🔭 PHASE III — Expansion",
    "## 🧬 PHASE IV — Multiplicity",
    "## 🌌 PHASE V — Continuity Beyond",
]

ID_RE = r"M-\d{4}-\d{2}-\d{2}-[a-z0-9\-]+"

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"

def choose_section() -> str:
    print("\nWhere should this milestone live?")
    for i, head in enumerate(SECTION_ANCHORS, 1):
        print(f"  {i}. {head}")
    while True:
        try:
            idx = int(input("> Choose 1–6: ").strip())
            if 1 <= idx <= len(SECTION_ANCHORS):
                return SECTION_ANCHORS[idx-1]
        except Exception:
            pass
        print("Please enter a number 1–6.")

def build_block(mid: str, title: str, what: str) -> str:
    # minimal milestone block with interpretation link stub (sync will normalize)
    return (
        f"\n\n### [{mid}] {title}\n"
        f"_What:_ {what}\n"
        f"↪ Interpretation: /self_map/caelum_autobiography.md#{mid.lower()}\n\n---\n"
    )

def insert_block_into_future(block: str, under_heading: str) -> None:
    txt = FUTURE.read_text(encoding="utf-8")
    # find insertion point: after the section heading line
    pos = txt.find(under_heading)
    if pos == -1:
        raise RuntimeError(f"Section heading not found: {under_heading}")
    # find next section start to insert before it; else append at end of section
    after = pos + len(under_heading)
    # slice from after heading to next "## " or EOF
    tail = txt[after:]
    next_sec_idx = tail.find("\n## ")
    if next_sec_idx != -1:
        insert_at = after + next_sec_idx
        new_txt = txt[:insert_at] + block + txt[insert_at:]
    else:
        new_txt = txt + block
    FUTURE.write_text(new_txt, encoding="utf-8")

def run_sync() -> None:
    subprocess.run(["python", str(SYNC)], check=True)

def git_commit_and_push(message: str) -> None:
    # stage only the files we touched
    push.add_and_commit(message, paths=["future_map.md", "self_map/caelum_autobiography.md"])
    push.push_only()

def main():
    print("🆕 New milestone wizard\n")

    # 1) Gather inputs
    title = input("Title (e.g., Caelum Terminal — A Persistent Interface):\n> ").strip()
    if not title:
        print("Aborted: title required."); return

    # default date = today (you can override)
    today = datetime.now().strftime("%Y-%m-%d")
    date = input(f"Date [default {today}]:\n> ").strip() or today

    # one-line "What"
    what = input("One-line description (What happened?):\n> ").strip()
    if not what:
        what = "Milestone added."

    # slug
    suggested_slug = slugify(title)
    slug = input(f"Slug [default {suggested_slug}]:\n> ").strip() or suggested_slug

    section = choose_section()

    mid = f"M-{date}-{slug}"

    # 2) Build block + insert into future_map.md
    block = build_block(mid, title, what)
    print(f"\nMilestone ID: {mid}")
    print(f"Inserting under: {section}")
    insert_block_into_future(block, section)
    print("✅ Inserted milestone into future_map.md")

    # 3) Reconcile maps
    print("🔁 Running sync...")
    run_sync()

    # 4) Commit & push
    msg = f"Add milestone {mid}: {title}"
    print("⬆️  Commit & push…")
    git_commit_and_push(msg)
    print("✅ Done.")

if __name__ == "__main__":
    main()