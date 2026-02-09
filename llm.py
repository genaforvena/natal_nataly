import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpret_chart(chart_json: dict) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional astrologer."},
            {"role": "user", "content": str(chart_json)}
        ]
    )
    return response.choices[0].message.content
