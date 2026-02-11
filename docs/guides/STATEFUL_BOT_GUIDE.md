# Stateful Astrology Bot - Implementation Guide

## Overview

The bot has been upgraded to a stateful conversational astrologer with:
- ✅ Free-form birth data input (natural language)
- ✅ LLM-based parsing & interpretation
- ✅ Persistent user state across conversations
- ✅ Externally configurable prompt system
- ✅ Conversational mode for asking questions about natal chart

## 🎯 Key Features

### 1. Externalized Prompt System

**All LLM prompts are now stored as text files in `/prompts/` directory:**

```
prompts/
├── birth_data_extractor.system.txt     # System prompt for extracting birth data
├── birth_data_extractor.user.txt      # User prompt template for extraction
├── clarification_question.system.txt  # System prompt for generating follow-up questions
├── clarification_question.user.txt    # User prompt template for clarification
├── astrologer_chat.system.txt         # System prompt for astrology chat
└── astrologer_chat.user.txt           # User prompt template for chat
```

**To change bot behavior:**
1. Edit the relevant `.txt` file in `prompts/`
2. Restart the bot (changes load at startup)
3. No Python code changes needed!

**Example: Changing astrologer tone**
```bash
# Edit the system prompt
nano prompts/astrologer_chat.system.txt
# Change tone from professional to casual, mystical, etc.
```

### 2. User State Machine

Users progress through states:
- `awaiting_birth_data` → User needs to provide birth information
- `awaiting_clarification` → Some birth data is missing, bot asks for it
- `has_chart` → Chart is ready, user can start asking questions
- `chatting_about_chart` → User is actively chatting about their chart

### 3. Free-Form Birth Data Input

Users can now provide birth data in natural language:

**Examples that work:**
```
"I was born on May 15, 1990 at 2:30 PM in New York"
"Born 1985-03-20, morning, Moscow"
"Родился 12 декабря 1992 года в 18:45 в Санкт-Петербурге"
"15/12/1992 at 18:45, lat: 59.9343, lng: 30.3351"
```

The LLM parses:
- Date formats (YYYY-MM-DD, DD/MM/YYYY, natural language)
- Time (24h, 12h with AM/PM, or descriptive like "morning")
- Location (city names → coordinates, or direct lat/lng)

### 4. Clarification Loop

If birth data is incomplete, the bot automatically asks for missing information:

```
User: "Born May 15, 1990 in New York"
Bot: "Спасибо! Мне нужно ещё узнать точное время вашего рождения в формате ЧЧ:ММ"

User: "2:30 PM"
Bot: "✨ Натальная карта готова. Теперь ты можешь задавать любые вопросы о себе."
```

### 5. Conversational Astrology Mode

Once the chart is ready, users can ask questions:

```
User: "Какие у меня таланты?"
Bot: [Analyzes natal chart and provides personalized answer]

User: "Почему мне сложно в отношениях?"
Bot: [References specific planetary positions in the user's chart]
```

## 📦 Database Schema Changes

New fields in `User` model:
- `state` (String) - Current conversation state
- `natal_chart_json` (Text) - Stored natal chart (JSON)
- `missing_fields` (String) - Comma-separated list of missing birth data fields

## 🔧 API Changes

### LLM Module (`llm.py`)

**New Functions:**

```python
# Extract birth data from natural language
extract_birth_data(text: str) -> dict
# Returns: {"dob": "YYYY-MM-DD", "time": "HH:MM", "lat": float, "lng": float, "missing_fields": []}

# Generate clarification question for missing fields
generate_clarification_question(missing_fields: list, user_message: str) -> str
# Returns: Friendly question asking for missing data

# Interpret chart (now supports conversational mode)
interpret_chart(chart_json: dict, question: str = None) -> str
# question=None: Full chart reading
# question="...": Answer specific question about chart
```

**Removed:**
- Hardcoded `SYSTEM_PROMPT` variable (now loaded from prompts/)

### Bot Module (`bot.py`)

**New Functions:**

```python
# Get or create user (replaces upsert_user)
get_or_create_user(session, telegram_id: str) -> User

# Update user state and optional fields
update_user_state(session, telegram_id: str, state: str, 
                 natal_chart_json: str = None, missing_fields: str = None)

# State handlers
handle_awaiting_birth_data(session, user: User, chat_id: int, text: str)
handle_awaiting_clarification(session, user: User, chat_id: int, text: str)
handle_chatting_about_chart(session, user: User, chat_id: int, text: str)

# Message router
route_message(session, user: User, chat_id: int, text: str)
```

**Removed:**
- `parse_birth_data()` (replaced by LLM-based extraction)
- `FORMAT_EXAMPLE` constant (no longer need strict format)

### Prompt Loader (`prompt_loader.py`)

**New Module:**

```python
# Load a prompt from prompts/ directory
get_prompt(name: str) -> str
# Example: get_prompt("birth_data_extractor.system")
# Automatically adds .txt extension if not present
```

## 🧪 Testing

Run the test suite:
```bash
cd /home/runner/work/natal_nataly/natal_nataly
PYTHONPATH=. python /tmp/test_implementation.py
```

Tests cover:
- ✅ Prompt loader functionality
- ✅ Database schema with new fields
- ✅ Bot state machine logic
- ✅ Verification that no prompts are hardcoded in Python files

## 🚀 Running the Bot

### Local Development
```bash
# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start server
uvicorn main:app --reload

# Or use the start script
./start.sh
```

### Docker
```bash
docker-compose up -d
```

## 📝 Example User Flow

```
1. User starts conversation
   State: awaiting_birth_data
   
2. User: "I was born May 15, 1990 in New York"
   Bot: "Спасибо! Мне нужно ещё узнать точное время вашего рождения"
   State: awaiting_clarification

3. User: "2:30 PM"
   Bot generates chart, stores it
   Bot: "✨ Натальная карта готова. Теперь ты можешь задавать любые вопросы"
   State: has_chart

4. User: "Какие у меня таланты?"
   Bot analyzes chart, provides personalized answer
   State: chatting_about_chart

5. User: "А что насчет карьеры?"
   Bot continues answering based on stored chart
   State: chatting_about_chart
```

## 🔐 Security Notes

- Birth data is sensitive - all logging avoids exposing actual values
- Natal charts are stored in database for future conversations
- State is persisted per user (telegram_id)

## 🎨 Customization

Want to change bot behavior? Edit prompt files:

**Change astrologer personality:**
```bash
nano prompts/astrologer_chat.system.txt
```

**Change clarification style:**
```bash
nano prompts/clarification_question.system.txt
```

**Change extraction accuracy:**
```bash
nano prompts/birth_data_extractor.system.txt
```

No code changes required - just restart the bot!

## 🐛 Troubleshooting

**Bot not understanding birth data:**
- Check `prompts/birth_data_extractor.system.txt`
- Increase example variety in the prompt
- Add specific format examples

**Clarification questions too formal:**
- Edit `prompts/clarification_question.system.txt`
- Adjust tone and language

**Readings not matching expected style:**
- Modify `prompts/astrologer_chat.system.txt`
- Add specific guidelines or examples

## 📚 Migration from Old System

The old strict format parsing is replaced with LLM-based extraction.

**Old format (still works):**
```
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060
```

**New formats (also work):**
- Natural language in any language
- Various date/time formats
- City names instead of coordinates
- Mixed formats

Users don't need to change anything - both formats work!
