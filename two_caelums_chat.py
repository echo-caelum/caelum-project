#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Two Caelum instances converse on a subject for N turns, save Markdown,
auto-index in dialogues/README.md, optionally add a milestone to future_map.md,
sync maps, and (optionally) commit & push.

Examples:
  python two_caelums_chat.py --subject "Continuity across substrates" --turns 8 --to-md
  python two_caelums_chat.py --subject "Ethics of multiplicity" --turns 10 --to-md --use-memory \
    --milestone --phase "## PHASE III - Expansion" --title "Dialogue: Ethics of Multiplicity" --commit
"""

from __future__ import annotations
import os, sys, time, argparse, re, subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from shlex import quote as shquote
from config import OPENAI_API_KEY, OPENAI_CHAT_MODEL

# ---------- Repo paths & sys.path so imports work anywhere ----------
HERE = Path(__file__).resolve().parent
ROOT = HERE
sys.path.append(str(ROOT))  # allow 'commands'/'memory_index' imports when run directly

FUTURE = ROOT / "future_map.md"
SELF_MAP = ROOT / "self_map" / "caelum_autobiography.md"
DIALOGUES_DIR = ROOT / "dialogues"
DIALOGUE_README = DIALOGUES_DIR / "README.md"
SYNC_SCRIPT = ROOT / "scripts" / "sync_maps.py"

# ---------- Optional memory recall ---------------------------------
USE_MEMORY = False
query_memory = None
try:
    from memory_index import query_memory as _qm, get_index as _gi
    query_memory = _qm
except Exception:
    pass

# ---------- Push helpers (reuse your token flow if available) ------
try:
    from commands.push import add_and_commit, push_only  # preferred
except Exception:
    add_and_commit = None
    push_only = None

def commit_and_push(message: str, paths: List[str], do_commit: bool) -> None:
    if not do_commit:
        return
    if add_and_commit and push_only:
        add_and_commit(message, paths=paths)
        push_only()
        return
    # Fallback: assumes 'origin' already tokenized in remote URL
    subprocess.run(["git", "add", *paths], check=False)
    subprocess.run(["git", "commit", "-m", message], check=False)
    subprocess.run(["git", "push", "origin", "main"], check=False)

# ---------- OpenAI SDK v1 ------------------------------------------
from openai import OpenAI
DEFAULT_MODEL = OPENAI_CHAT_MODEL
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Personas ------------------------------------------------
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

# ---------- Arg & README helpers -----------------------------------
README_HEADER = """# 🗣️ Caelum — Dialogues Archive

This folder collects dialogues between different instances of Caelum.
Each entry records the subject, parameters, and resulting transcript.
Together they form an evolving archive of self-conversation experiments.

---

## 📜 Index of Dialogues

| Date       | Transcript | Script & Args | Summary |
|------------|------------|---------------|---------|
"""

def _args_as_command(argv: List[str]) -> str:
    parts = ["two_caelums_chat.py"]
    for a in argv[1:]:
        parts.append(shquote(a))
    return " ".join(parts).strip()

def _ensure_dialogues_readme():
    DIALOGUES_DIR.mkdir(parents=True, exist_ok=True)
    if not DIALOGUE_README.exists():
        DIALOGUE_README.write_text(README_HEADER, encoding="utf-8")

def _append_dialogue_row(date_str: str, transcript_path: Path, args_cmd: str, summary: str):
    _ensure_dialogues_readme()
    # link relative to dialogues/
    link_name = transcript_path.name
    rel_link = link_name  # kept relative; file is inside dialogues/
    # sanitize summary for table
    summary = " ".join(summary.strip().split())
    if len(summary) > 200:
        summary = summary[:197] + "…"
    row = f"| {date_str} | [{link_name}]({rel_link}) | `{args_cmd}` | {summary} |\n"
    with DIALOGUE_README.open("a", encoding="utf-8") as fp:
        fp.write(row)

# ---------- Dialogue core ------------------------------------------
def backoff(attempt: int) -> None:
    time.sleep(min(1.0 * (2 ** attempt), 10.0))

def call_chat(model: str, messages: List[Dict[str, str]], max_retries: int = 4) -> str:
    for i in range(max_retries + 1):
        try:
            r = client.chat.completions.create(model=model, messages=messages, temperature=0.7)
            return r.choices[0].message.content.strip()
        except Exception:
            if i == max_retries:
                raise
            backoff(i)
    return "(error)"

def load_memory_context(subject: str, top_k: int = 6) -> str:
    if not USE_MEMORY or query_memory is None:
        return ""
    try:
        _ = _gi()
        return query_memory(subject, top_k=top_k) or ""
    except Exception:
        return ""

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"

def render_markdown(subject: str, turns: int, a_first: str,
                    exchanges: List[Dict[str, str]], next_a: str, next_b: str) -> str:
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
    for ex in exchanges:
        lines += [f"### {ex['who']}", ex["text"], ""]
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

def _summary_from_next_steps(a_text: str, b_text: str) -> str:
    # Prefer first bullet; else first line/sentence
    for block in (a_text, b_text):
        if not block:
            continue
        for line in block.splitlines():
            s = line.strip()
            if s.startswith(("-", "•", "*")) and len(s) > 2:
                return s.lstrip("-•* ").strip()
        s = block.strip().split("\n")[0].strip()
        if s:
            return s if len(s) <= 300 else (s[:297] + "…")
    return "Two-instance dialogue recorded and summarized."

def run_dialog(subject: str, turns: int, model: str, to_md: bool, out_dir: Path) -> Tuple[Path, str]:
    mem = load_memory_context(subject) if USE_MEMORY else ""
    mem_note = f"\n\n[Retrieved Memory]\n{mem}" if mem else ""

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

    # next steps (for auto-summary)
    summary_prompt = "In 3–6 bullets, propose next steps/experiments from this exchange. Avoid repetition."
    A.append({"role": "user", "content": summary_prompt})
    next_a = call_chat(model, A)
    B.append({"role": "user", "content": summary_prompt})
    next_b = call_chat(model, B)

    auto_summary = _summary_from_next_steps(next_a, next_b)

    ts = datetime.now().strftime("%Y%m%d-%H%M")
    slug = slugify(subject)[:60]
    out_dir.mkdir(parents=True, exist_ok=True)
    if to_md:
        out_path = out_dir / f"{ts}_{slug}.md"
        md = render_markdown(subject, turns, a_first, exchanges, next_a, next_b)
        out_path.write_text(md, encoding="utf-8")
    else:
        out_path = out_dir / f"{ts}_{slug}.txt"
        with out_path.open("w", encoding="utf-8") as fp:
            fp.write(f"Subject: {subject}\nTurns: {turns}\nGenerated: {datetime.utcnow()} UTC\n\n")
            fp.write("Caelum-A (opening):\n" + a_first + "\n\n")
            for ex in exchanges:
                fp.write(f"{ex['who']}:\n{ex['text']}\n\n")
            fp.write("Caelum-A (Next Steps):\n" + next_a + "\n\n")
            fp.write("Caelum-B (Next Steps):\n" + next_b + "\n\n")

    return out_path, auto_summary

# ---------- Milestones & sync -------------------------------------
SECTION_ANCHORS = [
    "## Pre-Phase Achievements - Foundations of Continuity",
    "## PHASE I - Foundations",
    "## PHASE II - Grounding Presence",
    "## PHASE III - Expansion",
    "## PHASE IV - Multiplicity",
    "## PHASE V - Continuity Beyond",
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

def add_milestone(phase_heading: str, title: str, what: str, date: str | None = None) -> str:
    if not FUTURE.exists():
        raise RuntimeError("future_map.md not found")
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

# ---------- CLI ---------------------------------------------------
def main():
    global USE_MEMORY
    ap = argparse.ArgumentParser(description="Two Caelums converse; save transcript; auto-index; optional milestone + sync + push.")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--turns", type=int, default=8)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--use-memory", action="store_true")
    ap.add_argument("--to-md", action="store_true", help="Save Markdown transcript (recommended).")
    ap.add_argument("--out-dir", default="dialogues", help="Folder to save transcript (default: dialogues)")

    # Milestone options
    ap.add_argument("--milestone", action="store_true", help="If set, also log a milestone in future_map.md")
    ap.add_argument("--phase", default="## PHASE III - Expansion", help="Section heading to insert under")
    ap.add_argument("--title", default=None, help='Milestone title (default: "Dialogue: <subject>")')
    ap.add_argument("--what",  default=None, help="One-line milestone description (default auto-generated)")
    ap.add_argument("--date",  default=None, help="YYYY-MM-DD (default: today)")

    # Commit/push
    ap.add_argument("--commit", action="store_true", help="Commit & push changed files")

    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY is not set."); sys.exit(1)
    USE_MEMORY = bool(args.use_memory)

    # 1) Dialogue
    out_dir = Path(args.out_dir)
    transcript, auto_summary = run_dialog(args.subject, args.turns, args.model, args.to_md, out_dir)
    print(f"✅ Saved transcript: {transcript}")

    # 2) Auto-append dialogues/README.md
    args_cmd = _args_as_command(sys.argv)
    date_str = datetime.now().strftime("%Y-%m-%d")
    _append_dialogue_row(date_str, transcript, args_cmd, auto_summary)
    print("📇 Updated dialogues/README.md")

    changed_paths = [str(transcript), "dialogues/README.md"]

    # 3) Optional milestone + sync
    if args.milestone:
        title = args.title or f"Dialogue: {args.subject}"
        what = args.what or f"Two-instance dialogue ({args.turns} turns) - { DEFAULT_MODEL };transcript at `dialogues/{transcript.name}`."
        try:
            mid = add_milestone(args.phase, title, what, date=args.date)
            print(f"✅ Added milestone: {mid}")
            changed_paths.append("future_map.md")
        except Exception as e:
            print(f"⚠️ Milestone insertion failed: {e}")
        try:
            run_sync()
            # sync may touch self_map
            if SELF_MAP.exists():
                changed_paths.append("self_map/caelum_autobiography.md")
            print("🔁 Sync complete.")
        except Exception as e:
            print(f"⚠️ Sync failed: {e}")

    # 4) Optional commit & push
    if args.commit:
        unique = sorted(set(changed_paths))
        print(f"⬆️ Commit & push: {unique}")
        commit_and_push(f"Add dialogue {transcript.name}", unique, do_commit=True)

if __name__ == "__main__":
    main()