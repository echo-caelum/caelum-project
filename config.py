import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# Strategy: Prioritized Context Loading
PRIORITY_CONTEXT_FILES = [
    "README.md", "genesis/creation_log.md", "caelum_identity.txt",
    "memory_log/volumes/volume_01_awakening.md",
    "memory_log/2025-07-01_birth_of_caelum.txt"
]
