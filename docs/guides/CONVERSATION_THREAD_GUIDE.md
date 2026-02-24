# Conversation Context Management

## Overview

The natal_nataly bot maintains per-user conversation context to provide coherent, context-aware LLM responses.  
There are two layers — a **new JSON-based session** (primary) and a **legacy DB-row-per-message thread** (kept for backward compatibility):

| Layer | Module | Storage | Max messages | Notes |
|---|---|---|---|---|
| Session (primary) | `session_manager.py` | `User.conversation_session_json` (JSON column) | 20 | Active, replaces thread |
| Thread (legacy) | `thread_manager.py` | `conversation_messages` table | 10 | Kept in sync; do not rely on for new code |

## Session Manager (Primary)

`src/session_manager.py` stores the last N conversation exchanges as a JSON array directly on the `User` record.

### How It Works

- Messages are stored as a list: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]`
- The list is capped at **20 messages** (FIFO eviction – oldest messages are dropped first)
- Data lives in `User.conversation_session_json` – no extra table required

### API

```python
from src.session_manager import get_session_context, update_session_context, reset_session_context

# Load context
messages = get_session_context(user)  # → list of {role, content} dicts

# Append new exchange and persist
update_session_context(session, user, [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."},
])

# Clear context
reset_session_context(session, user)
```

### Configuration

```python
MAX_SESSION_MESSAGES = 20  # Last N messages kept (in session_manager.py)
```

## Legacy Thread Manager

`src/thread_manager.py` and the `conversation_messages` DB table remain in the codebase for backward compatibility.  
New messages are still written to the legacy table so existing tooling continues to work, but the **session manager is the authoritative source for LLM context**.

### Legacy Thread Features

- **FIFO with fixed first pair**: Maximum 10 messages; first user+assistant pair is never evicted
- **`/reset_thread` command**: Clears the legacy thread (also resets session context)

### Legacy Constants (`thread_manager.py`)

```python
MAX_THREAD_LENGTH = 10  # Maximum messages per legacy thread
FIXED_PAIR_COUNT = 2    # First pair that's never deleted
```

## User Commands

### `/reset_thread`

Clears conversation history (both session JSON and legacy thread) and starts fresh.

**Usage:**
```
/reset_thread
```

**Response:**
```
✅ История разговора очищена! Удалено сообщений: X

Теперь мы начинаем с чистого листа. Задай мне вопрос о своей натальной карте!
```

## Context-Aware LLM Responses

The session context is automatically included in LLM calls:

```python
# In handle_chatting_about_chart()
conversation_history = get_session_context(user)
reading = generate_assistant_response(context, text, conversation_history=conversation_history)
```

## Testing

```bash
# Thread manager unit tests
pytest tests/test_thread_manager.py

# All tests
pytest tests/
```

## Performance Considerations

- No extra DB table reads for the session context (loaded with the User row)
- Automatic FIFO eviction keeps the JSON payload small
- Legacy thread table is indexed on `telegram_id` and `created_at` for fast queries
