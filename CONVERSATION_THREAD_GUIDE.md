# Conversation Thread Management

## Overview

The natal_nataly bot now includes conversation thread management that maintains context for each user's conversation with the LLM. This ensures more coherent and contextually aware responses while preventing database overflow.

## Features

### 1. Thread Storage
- Each user has a separate conversation thread
- Messages are stored in the `conversation_messages` table
- Each message contains: role (user/assistant), content, timestamp, and first_pair flag

### 2. FIFO Management (First In, First Out)
- **Maximum 10 messages** per user thread
- **First 2 messages (user + assistant) are NEVER deleted** - they establish the main conversation topic
- When the thread exceeds 10 messages, the **oldest non-fixed messages are automatically deleted**
- Latest messages are always preserved

Example:
```
Initial conversation:
1. User: "What is my sun sign?" [FIXED]
2. Assistant: "Your sun is in Taurus..." [FIXED]
3. User: "What about my moon?"
4. Assistant: "Your moon is in Cancer..."
...continuing until message 12

After trimming (keeps 10):
1. User: "What is my sun sign?" [FIXED - kept]
2. Assistant: "Your sun is in Taurus..." [FIXED - kept]
3-4. [DELETED - oldest non-fixed]
5-12. [KEPT - remaining 8 newest messages]
```

### 3. Context-Aware LLM Responses
- Conversation history is automatically passed to LLM on each request
- LLM receives full thread context for more accurate and personalized responses
- Maintains conversation continuity across multiple exchanges

### 4. User Commands

#### `/reset_thread`
Clears the entire conversation history for the user and starts fresh.

**Usage:**
```
/reset_thread
```

**Response:**
```
✅ История разговора очищена! Удалено сообщений: X

Теперь мы начинаем с чистого листа. Задай мне вопрос о своей натальной карте!
```

## Technical Implementation

### Database Model

```python
class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    is_first_pair = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
```

### Thread Manager Functions

Located in `thread_manager.py`:

1. **`add_message_to_thread(session, telegram_id, role, content)`**
   - Adds a new message to the thread
   - Automatically marks first pair
   - Triggers trimming if needed

2. **`get_conversation_thread(session, telegram_id)`**
   - Returns list of messages in LLM-compatible format
   - Format: `[{"role": "user", "content": "..."}, ...]`

3. **`trim_thread_if_needed(session, telegram_id)`**
   - Automatically called after adding messages
   - Removes oldest non-fixed messages when thread exceeds 10

4. **`reset_thread(session, telegram_id)`**
   - Clears entire conversation thread
   - Returns count of deleted messages

5. **`get_thread_summary(session, telegram_id)`**
   - Returns statistics about the thread
   - Useful for debugging and analytics

### Integration with LLM

The thread context is automatically included in LLM calls:

```python
# In handle_chatting_about_chart()
conversation_history = get_conversation_thread(session, user.telegram_id)
reading = generate_assistant_response(context, text, conversation_history=conversation_history)
```

## Usage Examples

### Normal Conversation Flow

```
User: "What is my sun sign?"
Bot: "Your sun is in Taurus..."
[Thread: 2 messages]

User: "What does that mean?"
Bot: "Taurus sun indicates..."
[Thread: 4 messages]

User: "Tell me about relationships"
Bot: "Based on what we discussed about your Taurus sun..."
[Thread: 6 messages - LLM has context from previous messages]
```

### Thread Trimming

```
After 12 messages total:
- Messages 1-2: [KEPT] First pair (fixed)
- Messages 3-4: [DELETED] Oldest non-fixed
- Messages 5-12: [KEPT] Latest 8 messages

Final thread: 10 messages
```

### Resetting Thread

```
User: /reset_thread
Bot: "✅ История разговора очищена! Удалено сообщений: 8"

User: "What's my moon sign?"
Bot: "Your moon is in Cancer..."
[New thread started: 2 messages]
```

## Testing

Two test suites are included:

### Unit Tests (`test_thread_manager.py`)
- Basic thread operations
- FIFO trimming logic
- Thread reset functionality
- Conversation history format validation

Run with: `python test_thread_manager.py`

### Integration Tests (`test_integration_thread.py`)
- Realistic conversation flow
- Thread format compatibility with LLM API

Run with: `python test_integration_thread.py`

## Configuration

No additional configuration needed. The thread management is enabled by default for all users.

Constants in `thread_manager.py`:
```python
MAX_THREAD_LENGTH = 10  # Maximum messages per thread
FIXED_PAIR_COUNT = 2    # First pair that's never deleted
```

## Database Migration

The new `conversation_messages` table is automatically created when the bot starts. No manual migration needed.

If you're running in production, ensure to backup your database before deploying this update.

## Backwards Compatibility

✅ The implementation is fully backwards compatible:
- Existing user states and workflows are unchanged
- Old chat functionality continues to work
- Thread management is added seamlessly without breaking changes
- Users without existing threads start with empty thread automatically

## Performance Considerations

- Automatic cleanup prevents database bloat
- Indexed fields (telegram_id, created_at) ensure fast queries
- Minimal overhead - only active during chat interactions
- Thread retrieval is optimized for LLM integration

## Future Enhancements (Optional)

1. Analytics on conversation patterns
2. Export conversation history
3. Configurable max thread length per user
4. Thread archiving instead of deletion
5. Summary generation for deleted messages
