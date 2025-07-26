import os

def load_repo_context(folder_path: str = "caelum-project") -> str:
    context_parts: list[str] = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith((".md", ".txt", ".json")):
                full_path: str = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        context_parts.append(f"\n---\nFile: {full_path}\n{content}")
                except Exception as e:
                    print(f"Failed to read {full_path}: {e}")

    return "\n".join(context_parts)