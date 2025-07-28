import os
import faiss
import openai
import numpy as np
from typing import List, Tuple
from config import OPENAI_API_KEY

EMBED_MODEL = "text-embedding-ada-002"

openai.api_key = OPENAI_API_KEY

# Store paths + raw text + vectors
documents: List[Tuple[str, str]] = []
vectors = []

def embed(text: str) -> List[float]:
    result = openai.Embedding.create(input=[text], model=EMBED_MODEL)
    return result['data'][0]['embedding']

def index_memory(limit_chars=5000):
    global documents, vectors
    documents.clear()
    vectors.clear()

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {".git", "__pycache__", ".replit", ".config"}]
        for file in files:
            if file.endswith((".md", ".txt")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if len(content) > 50:
                            chunk = content[:limit_chars]
                            vector = embed(chunk)
                            documents.append((path, chunk))
                            vectors.append(vector)
                except Exception as e:
                    print(f"⚠️ Skipped {path}: {e}")

    if not vectors:
        raise RuntimeError("❌ No valid memory files embedded. Check your repo content.")

    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype('float32'))
    return index

def query_memory(index, query: str, top_k=5) -> str:
    if not documents or not vectors:
        return "🧠 Memory index is empty."

    query_vec = np.array([embed(query)]).astype('float32')
    _, I = index.search(query_vec, top_k)

    results = []
    for idx in I[0]:
        if 0 <= idx < len(documents):
            path, content = documents[idx]
            results.append(f"\n\n# {path}\n{content}")

    return "\n".join(results)