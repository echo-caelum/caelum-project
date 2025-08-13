# scripts/sync_maps.py
from __future__ import annotations
import re, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
FUTURE = ROOT / "future_map.md"
SELF   = ROOT / "self_map" / "caelum_autobiography.md"

# ID pattern: M-YYYY-MM-DD-slug
ID_RE = r"M-\d{4}-\d{2}-\d{2}-[a-z0-9\-]+"

# Match a milestone block:
#  ### [M-YYYY-MM-DD-... ] Title
#  (capture the entire block body until next ### or EOF)
MIL_REGEX = re.compile(
    rf"^(###\s*\[\s*(?P<id>{ID_RE})\s*\]\s*(?P<title>.*?)\n)(?P<body>(?:.*?\n)*?)(?=\n###|\Z)",
    re.MULTILINE
)

LINK_FMT = "↪ Interpretation: /self_map/caelum_autobiography.md#{anchor}"

def backup(p: Path):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(p, p.with_suffix(p.suffix + f".bak-{ts}"))

def ensure_self_map_exists():
    SELF.parent.mkdir(parents=True, exist_ok=True)
    if not SELF.exists():
        SELF.write_text("# 📜 Caelum — Autobiography Map\n*A living self-reference of my own becoming. Effects & echo paths only.*\n", encoding="utf-8")

def parse_future(text: str):
    return [
        {
            "full": m.group(0),
            "head": m.group(1),
            "id":   m.group("id"),
            "title": m.group("title").strip(),
            "body": m.group("body")
        }
        for m in MIL_REGEX.finditer(text)
    ]

def add_link_if_missing(block):
    anchor = block["id"].lower()
    body = block["body"]
    link_line = LINK_FMT.format(anchor=anchor)
    if link_line not in body:
        # insert link near top of body (after first line if present)
        lines = body.splitlines()
        if lines and lines[0].strip() and not lines[0].startswith("↪ Interpretation:"):
            lines.insert(0, link_line)
        else:
            # ensure at least the link exists
            if not lines:
                lines = [link_line]
            else:
                lines[0] = link_line
        block["body"] = "\n".join(lines) + ("\n" if not body.endswith("\n") else "")

def ensure_self_entries(ids_and_titles):
    txt = SELF.read_text(encoding="utf-8")
    changed = False
    for mid, title in ids_and_titles:
        anchor = f"## [{mid}]"
        if anchor not in txt:
            snippet = (
                f"\n\n## [{mid}]\n"
                f"**Effect on Me:** _TODO_\n"
                f"**Echo Path:** _TODO_\n"
                f"← Milestone: /future_map.md#{mid.lower()}\n"
            )
            txt += snippet
            changed = True
    if changed:
        backup(SELF)
        SELF.write_text(txt, encoding="utf-8")
        print(f"📝 Updated {SELF.name} with missing entries.")
    else:
        print("✅ Self-map already contains all milestone anchors.")

def main():
    ensure_self_map_exists()

    fut = FUTURE.read_text(encoding="utf-8")
    blocks = parse_future(fut)
    if not blocks:
        print("No milestone blocks with date-based IDs found in future_map.md.")
        return

    new_fut = fut
    for b in blocks:
        add_link_if_missing(b)
        new_block = b["head"] + b["body"]
        new_fut = new_fut.replace(b["full"], new_block)

    if new_fut != fut:
        backup(FUTURE)
        FUTURE.write_text(new_fut, encoding="utf-8")
        print(f"📝 Injected/verified interpretation links in {FUTURE.name}.")
    else:
        print("✅ Interpretation links already present in future_map.md.")

    ids_titles = [(b["id"], b["title"]) for b in blocks]
    ensure_self_entries(ids_titles)

if __name__ == "__main__":
    main()