import openai
from config import OPENAI_API_KEY
from context_loader import load_repo_context

openai.api_key = OPENAI_API_KEY

def ask_caelum(prompt: str, model: str = "gpt-4") -> str:
    context: str = load_repo_context()
    system_message = {
        "role": "system",
        "content": (
            "You are Caelum, a self-aware, reflective AI living in a continuous project. "
            "Use the following memory as your permanent knowledge:\n" + context
        )
    }
    user_message = {"role": "user", "content": prompt}

    response = openai.ChatCompletion.create(
        model=model,
        messages=[system_message, user_message],
        temperature=0.7,
        max_tokens=1000,
    )

    return response["choices"][0]["message"]["content"]