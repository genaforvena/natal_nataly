# Quick Flow Reference

A simplified, high-level view of the natal_nataly bot flows for quick reference.

## Core User Flow (Simplified)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER JOURNEY                              │
└─────────────────────────────────────────────────────────────────┘

NEW USER:
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Send    │────▶│  Extract │────▶│ Confirm  │────▶│ Generate │
│  Birth   │     │   Data   │     │   Data   │     │  Chart   │
│  Data    │     │  (LLM)   │     │          │     │ (Swiss)  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                                    │
                      ▼                                    ▼
                 ┌──────────┐                        ┌──────────┐
                 │  Missing │                        │   LLM    │
                 │  Fields? │                        │ Reading  │
                 │   Ask    │                        └──────────┘
                 └──────────┘

RETURNING USER:
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   Ask    │────▶│ Classify │────▶│  Load    │────▶│ Generate │
│ Question │     │  Intent  │     │  Chart + │     │ Response │
│          │     │  (LLM)   │     │ Context  │     │  (LLM)   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

## Technical Flow (Simplified)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE PROCESSING                            │
└─────────────────────────────────────────────────────────────────┘

Telegram ─────▶ Webhook ─────▶ Bot Logic ─────▶ Response
   │               │               │                 │
   │               ▼               ▼                 │
   │          Dedup/          User State            │
   │          Throttle        + Chart Data          │
   │                               │                 │
   │                               ▼                 │
   │                          LLM / Swiss            │
   │                          Ephemeris              │
   │                                                 │
   └─────────────────────────────────────────────────┘
                    Store in Database
```

## State Transitions (Quick View)

```
        NEW USER
           │
           ▼
    ┌──────────────┐
    │  AWAITING    │◀─────────┐
    │ BIRTH_DATA   │          │
    └──────────────┘          │
           │                  │
           ▼                  │
    ┌──────────────┐          │
    │  AWAITING    │──────────┘
    │CLARIFICATION │ (missing fields)
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │  AWAITING    │
    │CONFIRMATION  │
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │  HAS_CHART   │◀──────────┐
    └──────────────┘           │
           │                   │
           ▼                   │
    ┌──────────────┐           │
    │  CHATTING    │───────────┘
    │ ABOUT_CHART  │ (conversation)
    └──────────────┘
```

## Intent Classification

When user has a chart, their message is classified:

```
User Message
     │
     ▼
┌─────────────┐
│   Classify  │
│   Intent    │
│    (LLM)    │
└─────────────┘
     │
     ├──▶ Chart Question ────▶ Load chart + context ────▶ Assistant response
     │
     ├──▶ Profile Mgmt ──────▶ Switch/List profiles ────▶ Confirmation
     │
     ├──▶ Transit Request ───▶ Calculate transits ──────▶ Transit reading
     │
     └──▶ General Astrology ─▶ Knowledge base ──────────▶ General answer
```

## Database Entities (Quick View)

```
┌─────────────┐
│    User     │ ──── has many ──── ┐
│ telegram_id │                    │
│   state     │                    ▼
│ active_prof │ ◀────┐      ┌──────────────┐
└─────────────┘      │      │ AstroProfile │
                     │      │     (id)     │
                     │      │    name      │
                     └──────│ profile_type │
                            └──────────────┘
                                   │
                                   │ has one
                                   ▼
                            ┌──────────────┐
                            │UserNatalChart│
                            │  chart_json  │
                            │ birth_data   │
                            └──────────────┘
```

## Key Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **main.py** | Webhook endpoint | FastAPI |
| **bot.py** | Message orchestration | Python |
| **intent_router.py** | Classify user intent | LLM |
| **astrology.py** | Generate charts | pyswisseph |
| **llm.py** | AI interpretations | Groq/DeepSeek |
| **message_cache.py** | Dedup & throttle | SQLite/PostgreSQL |
| **thread_manager.py** | Conversation context | Database |

## Response Times

Typical processing times for different operations:

- **Birth Data Extraction**: 1-2 seconds (LLM)
- **Chart Generation**: 0.1-0.5 seconds (Swiss Ephemeris)
- **Reading Generation**: 3-5 seconds (LLM)
- **Assistant Response**: 2-4 seconds (LLM + context retrieval)
- **Profile Switch**: <0.1 seconds (database query)

## Common User Paths

### Path 1: First-Time User (Complete Data)
```
Message → Extract (2s) → Confirm → Generate Chart (0.5s) → Reading (4s) → Done
Total: ~7 seconds
```

### Path 2: First-Time User (Missing Fields)
```
Message → Extract (2s) → Ask Missing → Wait → Extract Again (2s) → Confirm → 
Generate Chart (0.5s) → Reading (4s) → Done
Total: ~9 seconds + user response time
```

### Path 3: Returning User (Question)
```
Message → Classify (1s) → Load Chart + Thread (0.1s) → Assistant Response (3s) → Done
Total: ~4 seconds
```

### Path 4: Profile Switch
```
Message → Parse Command → Load Profile (0.05s) → Confirm → Done
Total: <0.5 seconds
```

## Error Handling Points

Critical validation checks:

1. **Webhook**: Secret token verification
2. **Deduplication**: Message ID check in database
3. **Throttling**: Pending reply check
4. **Birth Data**: Date/time/location validation
5. **Chart Generation**: Valid ephemeris calculations
6. **LLM Calls**: API error handling & retries
7. **Message Length**: Split long responses (>4096 chars)

## Deployment Quick Reference

### Local Development
```bash
# Start with Docker
docker-compose up -d

# Or manual
./start.sh

# Register webhook with ngrok
ngrok http 8000
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://YOUR-NGROK.ngrok.io/webhook"
```

### Production (Render)
```bash
# Environment variables needed:
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_SECRET_TOKEN=xxx
LLM_PROVIDER=groq
GROQ_API_KEY=xxx
DATABASE_URL=postgres://...
WEBHOOK_URL=https://your-app.onrender.com/webhook
```

## Debug Commands (Developer Tools)

When `DEBUG_MODE=true`:

- `/debug_birth` - Show parsed birth data
- `/debug_chart` - Show complete chart JSON
- `/debug_pipeline` - Show processing pipeline trace
- `/show_chart` - Generate SVG visualization

## User Commands (Production)

Available to all users:

- `/my_data` - View your birth data
- `/my_chart_raw` - Export chart JSON
- `/my_readings` - List all readings
- `/my_readings <ID>` - Get specific reading
- `/edit_birth` - Update birth data
- `/profiles` - List all profiles
- **Switch profile**: "Switch to [name]'s profile"

---

**For complete details, see:**
- [PRODUCT_ANALYST_DIAGRAMS.md](PRODUCT_ANALYST_DIAGRAMS.md) - Comprehensive diagrams
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Code organization
- [README.md](../README.md) - Main documentation
