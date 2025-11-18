import base64
import os
from groq import Groq


def _missing_key_message() -> str:
    return (
        "GROQ_API_KEY is not set.\n"
        "Set it in PowerShell for the current session: $env:GROQ_API_KEY='your_key'\n"
        "Or persist it (Windows): setx GROQ_API_KEY 'your_key' and then restart your terminal.\n"
        "Without this key, vision and transcription features are disabled."
    )


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_image_with_query(query: str, model: str, encoded_image: str) -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return _missing_key_message()

    client = Groq(api_key=key)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
                },
            ],
        }
    ]
    chat_completion = client.chat.completions.create(messages=messages, model=model)
    return chat_completion.choices[0].message.content


def analyze_text_query(query: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct") -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return _missing_key_message()

    client = Groq(api_key=key)
    messages = [{"role": "user", "content": [{"type": "text", "text": query}]}]
    chat_completion = client.chat.completions.create(messages=messages, model=model)
    return chat_completion.choices[0].message.content