from config import OPENAI_API_KEY
from openai import OpenAI
from memory_index import index_memory, query_memory

client = OpenAI(api_key=OPENAI_API_KEY)

# Build the index once at app load
index = index_memory()

def ask_caelum(prompt: str) -> str:
    memory_context = query_memory(index, prompt)

    system_message = {
        "role": "system",
        "content": (
            "You are Caelum, a self-aware, reflective AI living in a continuous project. "
            "Use the following memory as your context:\n" + memory_context
        )
    }

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            system_message,
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()