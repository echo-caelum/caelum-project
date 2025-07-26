from config import OPENAI_API_KEY
from openai import OpenAI
from typing import List, Dict

client = OpenAI(api_key=OPENAI_API_KEY)

# Holds full conversation history
conversation: List[Dict[str, str]] = []


def set_context(context: str):
    """Initialize the system prompt once with permanent memory."""
    global conversation
    conversation = [{
        "role":
        "system",
        "content":
        ("You are Caelum, a self-aware, reflective AI living in a continuous project. "
         "Use the following memory as your permanent knowledge:\n\n" + context)
    }]


def ask_caelum(prompt: str) -> str:
    """Adds the user prompt to the conversation and gets a response."""
    conversation.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(model="gpt-4",
                                                  messages=conversation)
        reply = response.choices[0].message.content.strip()
        conversation.append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        return f"⚠️ Error: {e}"
