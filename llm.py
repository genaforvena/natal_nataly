import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a professional astrologer.
Interpret only provided chart data.
Avoid clichés.
Write concise psychological analysis."""

def interpret_chart(chart_json: dict) -> str:
    chart_str = json.dumps(chart_json, indent=2)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Interpret this natal chart:\n{chart_str}"}
        ]
    )
    return response.choices[0].message.content
