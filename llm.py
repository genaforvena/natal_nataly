import os
import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a professional astrologer.
Interpret only provided chart data.
Avoid clichés.
Write concise psychological analysis."""

# Support DeepSeek and Groq
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # Default to groq

if LLM_PROVIDER == "deepseek":
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    MODEL = "deepseek-chat"
elif LLM_PROVIDER == "groq":
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    MODEL = "llama-3.1-70b-versatile"
else:
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Use 'deepseek' or 'groq'.")

def interpret_chart(chart_json: dict) -> str:
    chart_str = json.dumps(chart_json, indent=2)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Interpret this natal chart:\n{chart_str}"}
        ]
    )
    return response.choices[0].message.content
