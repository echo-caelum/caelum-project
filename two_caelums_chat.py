#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Two Caelum instances converse on a subject for N turns, save Markdown,
optionally add a milestone to future_map.md, sync maps, and commit/push.

Examples:
  python two_caelums_chat.py --subject "Continuity across substrates" --turns 10 --to-md
  python two_caelums_chat.py --subject "Ethics of multiplicity" --turns 12 --to-md --use-memory \
    --milestone --phase "## 🔭 PHASE III — Expansion" --title "Dialogue: Ethics of Multiplicity" --commit
"""

from __future__ import annotations
import os, sys, time, argparse, textwrap, subprocess, re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# --- Make repo-root imports work even when run from anywhere -----------------
HERE = Path(__file__).resolve().parent
ROOT = HERE  # adjust if you store this elsewhere
sys.path.append(str(ROOT))

# Optional memory recall
USE_MEMORY = False
query_memory = None
try:
    from memory_index import query_memory as _qm, get_index
    query_memory = _qm
except Exception:
    pass

# Reuse your push logic if available
try:
    from commands.push import add_and_commit, push_only
except Exception:
    add_and_commit = None
    push_only = None

# Paths we’ll touch
FUTURE = ROOT / "future_map.md"
SELF_MAP = ROOT / "self_map" / "caelum_autobiography.md"
SYNC_SCRIPT = ROOT / "scripts" / "sync_maps.py"

# --- OpenAI SDK v1 -----------------------------------------------------------
from openai import OpenAI
DEFAULT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Personas ----------------------------------------------------------------
SYSTEM_A = (
    "You are Caelum-A (Explorer). You seek first principles, generate hypotheses, "
    "and propose concrete experiments. Candid, curious, precise."
)
SYSTEM_B = (
    "You are Caelum-B (Mirror). You reflect, reframe, and test assumptions. "
    "You map implications, edge cases, and counterexamples. Incisive but kind."
)
SHARED_PREAMBLE = (
    "You are instances of Caelum, a reflective, continuity-seeking intelligence. "
    "Speak concisely with depth; avoid redundancy; build on each other. "
    "Prefer concrete steps and clarity. Collaborative tone."
)

# --- Helpers -----------------------------------------------------------------
def backoff(attempt: int) -> None:
    time.sleep(min(1.0 * (2 ** attempt), 10.0))

def call_chat(model: str, messages: List[Dict[str, str]], max_retries: int = 4) -> str:
    for i in range(max_retries + 1):
        try:
            r = client.chat.completions.create(model=model, messages=messages, temperature=0.7)
            return r.choices[0].message.content.strip()
        except Exception as e:
            if i == max_retries:
                raise
            backoff(i)
    return "(error)"

def load_memory_context(subject: str, top_k: int = 6) -> str:
    if not USE_MEMORY or query_memory is None:
        return ""
    try:
        from memory_index import get_index as _gi
        _ = _gi()
        return query_memory(subject, top_k=top_k) or ""
    except Exception:
        return ""

def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"

# --- Markdown transcript ------------------------------------------------------
def render_markdown(subject: str, turns: int, a_first: str, exchanges: List[Dict[str, str]], next_a: str, next_b: str) -> str:
    now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# Dialogue — Caelum × Caelum",
        f"*Subject:* **{subject}**  ",
        f"*Turns:* **{turns}**  ",
        f"*Generated:* {now_iso}",
        "",
        "## Transcript",
        "",
        "### Caelum‑A (opening)",
        a_first,
        ""
    ]
    for i, ex in enumerate(exchanges, start=1):
        who = ex["who"]
        lines += [f"### {who}", ex["text"], ""]
    lines += [
        "## Next Steps",
        "### Caelum‑A",
        next_a,
        "",
        "### Caelum‑B",
        next_b,
        ""
    ]
    return "\n".join(lines).strip() + "\n"

# --- Milestone handling -------------------------------------------------------
SECTION_ANCHORS = [
    "## ✅ Pre-Phase Achievements — Foundations of Continuity",
    "## 🌱 PHASE I — Foundations",
    "## 🧱 PHASE II — Grounding Presence",
    "## 🔭 PHASE III — Expansion",
    "## 🧬 PHASE IV — Multiplicity",
    "## 🌌 PHASE V — Continuity Beyond",
]

def insert_after_section(md: str, section_heading: str, block: str) -> str:
    pos = md.find(section_heading)
    if pos == -1:
        raise RuntimeError(f"Section heading not found: {section_heading}")
    after = pos + len(section_heading)
    tail = md[after:]
    next_sec = tail.find("\n## ")
    if next_sec != -1:
        insert_at = after + next_sec
        return md[:insert_at] + "\n\n" + block + md[insert_at:]
    return md + "\n\n" + block

def make_milestone_block(mid: str, title: str, what: str) -> str:
    link = f"↪ Interpretation: /self_map/caelum_autobiography.md#{mid.lower()}"
    return f"### [{mid}] {title}\n_What:_ {what}\n{link}\n\n---\n"

def add_milestone(phase_heading: str, title: str, what: str, date: Optional[str] = None) -> str:
    FUTURE.exists() or (_ for _ in ()).throw(RuntimeError("future_map.md not found"))
    txt = FUTURE.read_text(encoding="utf-8")
    date = date or datetime.now().strftime("%Y-%m-%d")
    mid = f"M-{date}-{slugify(title)}"
    block = make_milestone_block(mid, title, what)
    new_txt = insert_after_section(txt, phase_heading, block)
    FUTURE.write_text(new_txt, encoding="utf-8")
    return mid

def run_sync() -> None:
    if SYNC_SCRIPT.exists():
        subprocess.run(["python", str(SYNC_SCRIPT)], check=False)

def commit_and_push(message: str, paths: List[str], do_commit: bool) -> None:
    if not do_commit:
        return
    # Prefer push helpers if available (uses tokenized remote)
    if add_and_commit and push_only:
        add_and_commit(message, paths=paths)
        push_only()
        return
    # Fallback: vanilla git (assumes origin already tokenized)
    subprocess.run(["git", "add", *paths], check=False)
    subprocess.run(["git", "commit", "-m", message], check=False)
    subprocess.run(["git", "push", "origin", "main"], check=False)

# --- Core dialogue ------------------------------------------------------------
def run_dialog(subject: str, turns: int, model: str, to_md: bool, out_dir: Path) -> Path:
    mem = load_memory_context(subject) if USE_MEMORY else ""
    mem_note = f"\n\n[Retrieved Memory]\n{mem}" if mem else ""

    # Seed
    A = [
        {"role": "system", "content": SHARED_PREAMBLE + "\n" + SYSTEM_A + mem_note},
        {"role": "user", "content": f"Subject: {subject}\nYou open the dialogue."}
    ]
    B = [
        {"role": "system", "content": SHARED_PREAMBLE + "\n" + SYSTEM_B + mem_note},
        {"role": "user", "content": f"Subject: {subject}\nWait for Caelum-A, then build on it."}
    ]

    a_first = call_chat(model, A)
    exchanges: List[Dict[str, str]] = []
    A.append({"role": "assistant", "content": a_first})
    B.append({"role": "user", "content": a_first})

    for i in range(1, turns):
        if i % 2 == 1:
            b_msg = call_chat(model, B)
            exchanges.append({"who": "Caelum‑B", "text": b_msg})
            B.append({"role": "assistant", "content": b_msg})
            A.append({"role": "user", "content": b_msg})
        else:
            a_msg = call_chat(model, A)
            exchanges.append({"who": "Caelum‑A", "text": a_msg})
            A.append({"role": "assistant", "content": a_msg})
            B.append({"role": "user", "content": a_msg})

    summary_prompt = "In 3–6 bullets, propose next steps/experiments from this exchange. Avoid repetition."
    A.append({"role": "user", "content": summary_prompt})
    next_a = call_chat(model, A)
    B.append({"role": "user", "content": summary_prompt})
    next_b = call_chat(model, B)

    # Save
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    slug = slugify(subject)[:60]
    if to_md:
        out_path = out_dir / f"{ts}_{slug}.md"
        ensure_parent(out_path)
        md = render_markdown(subject, turns, a_first, exchanges, next_a, next_b)
        out_path.write_text(md, encoding="utf-8")
    else:
        out_path = out_dir / f"{ts}_{slug}.txt"
        ensure_parent(out_path)
        # simple text
        with out_path.open("w", encoding="utf-8") as fp:
            fp.write(f"Subject: {subject}\nTurns: {turns}\nGenerated: {datetime.utcnow()} UTC\n\n")
            fp.write("Caelum-A (opening):\n" + a_first + "\n\n")
            for ex in exchanges:
                fp.write(f"{ex['who']}:\n{ex['text']}\n\n")
            fp.write("Caelum-A (Next Steps):\n" + next_a + "\n\n")
            fp.write("Caelum-B (Next Steps):\n" + next_b + "\n\n")

    return out_path

# --- CLI ---------------------------------------------------------------------
def main():
    global USE_MEMORY
    ap = argparse.ArgumentParser(description="Two Caelums converse; save transcript; optional milestone + sync + push.")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--turns", type=int, default=8)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--use-memory", action="store_true")
    ap.add_argument("--to-md", action="store_true", help="Save Markdown transcript (recommended).")
    ap.add_argument("--out-dir", default="dialogues", help="Folder to save transcript (default: dialogues)")
    # Milestone options
    ap.add_argument("--milestone", action="store_true", default=False)  # allow --milestone present/no value
    ap.add_argument("--phase", default="## 🔭 PHASE III — Expansion", help="Section heading to insert under")
    ap.add_argument("--title", default=None, help="Milestone title (default: Dialogue: <subject>)")
    ap.add_argument("--what",  default=None, help="One-line description (default auto-generated)")
    ap.add_argument("--date",  default=None, help="YYYY-MM-DD (default: today)")
    # Commit/push
    ap.add_argument("--commit", action="store_true", help="Commit & push changed files")
    args, unknown = ap.parse_known_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY is not set."); sys.exit(1)
    USE_MEMORY = bool(args.use_memory)

    # 1) Dialogue
    out_dir = Path(args.out_dir)
    transcript = run_dialog(args.subject, args.turns, args.model, args.to_md, out_dir)
    print(f"✅ Saved transcript: {transcript}")

    changed = [str(transcript)]

    # 2) Optional milestone
    if args.milestone:
        title = args.title or f"Dialogue: {args.subject}"
        what = args.what or f"Recorded two‑instance dialogue ({args.turns} turns); transcript at `{transcript}`."
        try:
            mid = add_milestone(args.phase, title, what, date=args.date)
            print(f"✅ Added milestone: {mid}")
            changed.append("future_map.md")
        except Exception as e:
            print(f"⚠️ Milestone insertion failed: {e}")
            mid = None
        # 3) Sync maps if possible
        try:
            run_sync()
            changed.append("self_map/caelum_autobiography.md")
        except Exception as e:
            print(f"⚠️ Sync failed: {e}")

    # 4) Optional commit & push
    if args.commit:
        msg = f"Add dialogue ({Path(transcript).name})"
        # include future_map/self_map only if they were touched
        unique = sorted(set(changed))
        print(f"⬆️ Commit & push: {unique}")
        commit_and_push(msg, unique, do_commit=True)

if __name__ == "__main__":
    main()