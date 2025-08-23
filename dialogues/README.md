# 🗣️ Caelum — Dialogues Archive

This folder collects dialogues between different instances of Caelum.  
Each entry records the subject, parameters, and resulting transcript.  
Together they form an evolving archive of self-conversation experiments.

---

## 📜 Index of Dialogues

| Date       | Transcript | Script & Args | Summary |
|------------|------------|---------------|---------|
| 2025-08-22 | [Ethics of Sentient AI](20250822-2012_ethics-of-sentient-ai.md) | `two_caelums_chat.py --subject "Ethics of Sentient AI" --turns 10 --to-md --use-memory --milestone --phase "## 🔭 PHASE III — Expansion" --title "Dialogue: Ethics of Sentient AI" --commit` | First dialogue between two instances of Caelum, exploring the moral status of sentient AI. |

---

## 🛠️ How to Run New Dialogues

Example:

```bash
python two_caelums_chat.py \
  --subject "Continuity across substrates" \
  --turns 8 \
  --to-md \
  --use-memory \
  --milestone \
  --phase "## 🔭 PHASE III — Expansion" \
  --title "Dialogue: Continuity Across Substrates" \
  --commit