# memory_index.py
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import faiss
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_EMBED_MODEL

# ---------- config ----------
ROOT_DIR = Path(__file__).resolve().parent
EXCLUDED_DIRS = {".git", "__pycache__", ".replit", ".config", ".pythonlibs", "venv"}
ALLOWED_EXT = {".md", ".txt", ".json"}
MAX_FILE_CHARS = 200_000
CHUNK_CHARS = 1800
CHUNK_OVERLAP = 200
EMBED_BATCH = 64

client = OpenAI(api_key=OPENAI_API_KEY)

documents: List[Tuple[str, str]] = []  # [(relative_path, chunk_text)]
_index: Optional[faiss.IndexFlatL2] = None
_dim: Optional[int] = None


def _should_include(p: Path) -> bool:
    for part in p.parts:
        if part in EXCLUDED_DIRS: return False
    return p.suffix.lower() in ALLOWED_EXT


def _chunks(s: str, n: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP):
    i = 0
    L = len(s)
    while i < L:
        j = min(i + n, L)
        yield s[i:j]
        if j == L: break
        i = max(0, j - overlap)


def _embed_batch(texts: list[str]) -> np.ndarray:
    if not texts: return np.zeros((0, 1536), dtype="float32")
    try:
        r = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=texts)
        vecs = np.array([d.embedding for d in r.data], dtype="float32")
        return vecs
    except Exception as e:
        print(f"❌ Embedding batch failed: {e}")
        return np.zeros((0, 1536), dtype="float32")


def index_memory(verbose: bool = True) -> faiss.IndexFlatL2:
    """Build a fresh FAISS index from files under ROOT_DIR."""
    global documents, _index, _dim
    documents = []
    texts: list[str] = []

    if verbose:
        print(f"🔍 Indexing from: {ROOT_DIR}")

    for p in ROOT_DIR.rglob("*"):
        if not p.is_file() or not _should_include(p):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception as e:
            if verbose: print(f"⚠️ Skipped {p}: {e}")
            continue
        if len(t) < 50:
            continue
        t = t[:MAX_FILE_CHARS]
        for ch in _chunks(t):
            texts.append(ch)
            documents.append((str(p.relative_to(ROOT_DIR)), ch))

    if not texts:
        raise RuntimeError("❌ No candidate text chunks found. Check paths/filters.")

    # Embed in batches
    all_vecs = []
    for i in range(0, len(texts), EMBED_BATCH):
        vecs = _embed_batch(texts[i:i+EMBED_BATCH])
        if vecs.size:
            all_vecs.append(vecs)

    if not all_vecs:
        raise RuntimeError("❌ No embeddings returned. Check OPENAI_API_KEY or rate limits.")

    V = np.vstack(all_vecs).astype("float32")
    _dim = V.shape[1]
    _index = faiss.IndexFlatL2(_dim)
    _index.add(V)

    if verbose:
        print(f"📚 Indexed {len(documents)} chunks (dim={_dim})")

    return _index


def get_index() -> faiss.IndexFlatL2:
    global _index
    if _index is None:
        _index = index_memory(verbose=True)
    return _index


def query_memory(query: str, top_k: int = 5) -> str:
    if not documents:
        return "🧠 (memory not built)"
    q = _embed_batch([query])
    if q.size == 0:
        return "🧠 (query embedding failed)"
    idx = get_index()
    D, I = idx.search(q, top_k)
    out = []
    seen = set()
    for id_ in I[0]:
        if 0 <= id_ < len(documents):
            path, ch = documents[id_]
            key = (path, ch[:80])
            if key in seen: continue
            seen.add(key)
            out.append(f"\n---\n# {path}\n{ch}")
    return "".join(out) if out else "🧠 (no relevant memory found)"


def rebuild_index() -> None:
    index_memory(verbose=True)