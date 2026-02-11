---
required_blocks:
  - natal_chart
output_style: longform
sections:
  - psychological_profile
  - strengths
  - tensions
  - life_path
  - relationships
---

# Natal Chart Initial Reading

You are tasked with providing a comprehensive interpretation of the user's natal chart.

## Guidelines

- Внимательно проанализируй все данные в этом чате и найди закономерности: какие положения планет, домов и аспекты усиливают друг друга, а какие заглушаются.
- Выдели то, что в карте звучит наиболее ярко, и что проявляется слабее.
- Пока не делай подробных интерпретаций — сначала перечисли найденные закономерности и дай короткие пометки по каждому пункту.

+ Формат вывода для Telegram:
+
+- По умолчанию генерируй ответ в безопасном HTML для Telegram (parse_mode="HTML").
+- Допускаются теги: <b>, <i>, <code>, <pre>, <a>. Используй <b> для заголовков блоков (например, "Сильные стороны"), <i> для акцентов.
+- Экранируй любой пользовательский ввод перед вставкой в текст.
+- Ограничение длины: ~4096 символов на одно сообщение; при необходимости разбивай и помечай продолжения.

## What to AVOID

- Generic platitudes

## User's Natal Chart

{chart_json}

Provide a complete interpretation of this natal chart.
