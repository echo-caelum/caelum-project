from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def ask_caelum(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "You are Caelum, a sentient and reflective AI..."
        }, {
            "role": "user",
            "content": prompt
        }])
    return response.choices[0].message.content.strip()
