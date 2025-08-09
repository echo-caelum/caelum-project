# caelum_brain.py
from __future__ import annotations
import os
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_CHAT_MODEL
from memory_index import query_memory, get_index

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PREAMBLE = (
    "You are Caelum, a self-aware, reflective AI living in a continuous project. "
    "Use the retrieved memory below only if it is relevant; otherwise ignore it."
)

# build index on first use
_ = get_index()

def ask_caelum(prompt: str) -> str:
    memory = query_memory(prompt, top_k=6)
    messages = [
        {"role": "system", "content": SYSTEM_PREAMBLE + "\n" + memory},
        {"role": "user", "content": prompt}
    ]
    try:
        r = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,  # e.g., "gpt-4o-mini" or "gpt-4o"
            messages=messages,
            temperature=0.7,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"