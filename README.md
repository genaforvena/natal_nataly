# natal_nataly

Telegram astrology bot that generates natal charts locally using Swiss Ephemeris
and produces AI-assisted readings.

Pipeline:
Telegram webhook → Validation → Natal chart → LLM interpretation → Reply

Run locally:
uvicorn main:app --reload
