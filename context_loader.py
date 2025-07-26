import os

context_token_limit = 10000


def load_repo_context(limit_chars: int = context_token_limit) -> str:
    from config import PRIORITY_CONTEXT_FILES

    included = []
    char_count = 0

    def add_file(path):
        nonlocal char_count
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                block = f"\n\n# {path}\n{content}"
                if char_count + len(block) <= limit_chars:
                    included.append(block)
                    char_count += len(block)
        except Exception as e:
            print(f"⚠️ Skipped {path}: {e}")

    # Add priority files first
    for file in PRIORITY_CONTEXT_FILES:
        if os.path.exists(file):
            add_file(file)

    # Then scan remaining .md/.txt files
    for root, dirs, files in os.walk("."):
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in {".git", "__pycache__"}
        ]
        for file in files:
            path = os.path.join(root, file)
            if file.endswith(
                (".md", ".txt")) and path not in PRIORITY_CONTEXT_FILES:
                add_file(path)
                if char_count >= limit_chars:
                    break

    return "\n".join(included)
