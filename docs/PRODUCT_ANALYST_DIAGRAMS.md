# Product Analyst Flow Visualizations

This document contains comprehensive flow diagrams and visualizations for understanding the natal_nataly Telegram bot system.

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [User Journey Flows](#2-user-journey-flows)
3. [Data Flow & Processing Pipeline](#3-data-flow--processing-pipeline)
4. [State Management](#4-state-management)
5. [Sequence Diagrams](#5-sequence-diagrams)
6. [Database Schema](#6-database-schema)
7. [Deployment Architecture](#7-deployment-architecture)

---

## 1. System Architecture

High-level overview of the system components and their interactions.

```mermaid
graph TB
    subgraph "External Services"
        TG[Telegram Bot API]
        LLM[LLM Provider<br/>Groq/DeepSeek]
        SE[Swiss Ephemeris<br/>Astronomical Data]
    end
    
    subgraph "natal_nataly Application"
        WH[Webhook Endpoint<br/>/webhook]
        BOT[Bot Logic<br/>bot.py]
        IR[Intent Router<br/>intent_router.py]
        
        subgraph "Business Logic"
            CB[Chart Builder<br/>chart_builder.py]
            DP[Date Parser<br/>date_parser.py]
            TB[Transit Builder<br/>transit_builder.py]
            LLMINT[LLM Integration<br/>llm.py]
            ASTRO[Astrology Engine<br/>astrology.py]
        end
        
        subgraph "Data Layer"
            DB[(Database<br/>SQLite/PostgreSQL)]
            MC[Message Cache<br/>message_cache.py]
            TM[Thread Manager<br/>thread_manager.py]
        end
        
        UC[User Commands<br/>user_commands.py]
        PM[Prompt Loader<br/>prompt_loader.py]
    end
    
    TG -->|POST /webhook| WH
    WH -->|Process Update| BOT
    BOT -->|Classify Intent| IR
    
    IR -->|Birth Data| DP
    IR -->|Chart Request| CB
    IR -->|Transit Request| TB
    IR -->|Assistant Mode| LLMINT
    
    DP --> LLMINT
    CB --> ASTRO
    TB --> ASTRO
    
    ASTRO --> SE
    LLMINT --> LLM
    LLMINT --> PM
    
    BOT --> UC
    BOT --> DB
    BOT --> MC
    BOT --> TM
    
    BOT -->|Send Response| TG
    
    style TG fill:#0088cc
    style LLM fill:#ff9900
    style SE fill:#66cc66
    style DB fill:#cc66ff
```

### Component Responsibilities

- **Webhook Endpoint**: Receives and validates Telegram updates
- **Bot Logic**: Orchestrates message handling and response generation
- **Intent Router**: Classifies user intent and routes to appropriate handler
- **Chart Builder**: Generates natal chart representations
- **Date Parser**: Extracts and normalizes birth data from natural language
- **Transit Builder**: Calculates and formats transit positions
- **LLM Integration**: Manages all LLM API calls and prompt handling
- **Astrology Engine**: Wraps Swiss Ephemeris for astronomical calculations
- **Database**: Persistent storage for users, profiles, charts, and readings
- **Message Cache**: Deduplication and throttling of webhook messages
- **Thread Manager**: Maintains conversation context and history
- **User Commands**: Handles special commands (/my_data, /profiles, etc.)

---

## 2. User Journey Flows

### 2.1 First-Time User Journey

```mermaid
flowchart TD
    Start([User Sends<br/>Birth Data]) --> Parse[Parse Message<br/>extract_birth_data]
    
    Parse --> CheckComplete{All Fields<br/>Complete?}
    
    CheckComplete -->|No| MissingFields[Set State:<br/>AWAITING_CLARIFICATION]
    MissingFields --> AskClarification[Generate<br/>Clarification Question]
    AskClarification --> SendClarify[Send Question<br/>to User]
    SendClarify --> WaitClarify[Wait for<br/>User Response]
    WaitClarify --> Parse
    
    CheckComplete -->|Yes| ShowConfirm[Show Birth Data<br/>for Confirmation]
    ShowConfirm --> SetConfirmState[Set State:<br/>AWAITING_CONFIRMATION]
    SetConfirmState --> WaitConfirm[Wait for<br/>CONFIRM/EDIT]
    
    WaitConfirm --> CheckConfirm{User<br/>Action?}
    CheckConfirm -->|EDIT| MissingFields
    CheckConfirm -->|CONFIRM| ValidateData[Validate<br/>Birth Data]
    
    ValidateData --> GenChart[Generate<br/>Natal Chart<br/>pyswisseph]
    GenChart --> StoreChart[Store Chart<br/>in Database]
    StoreChart --> GenReading[Generate<br/>Astrological Reading<br/>LLM]
    GenReading --> StoreReading[Store Reading<br/>in Database]
    StoreReading --> SetChartState[Set State:<br/>HAS_CHART]
    SetChartState --> SendReading[Send Reading<br/>to User]
    SendReading --> End([Ready for<br/>Conversations])
    
    style Start fill:#90EE90
    style End fill:#90EE90
    style GenChart fill:#FFD700
    style GenReading fill:#FF9900
```

### 2.2 Returning User Journey (Assistant Mode)

```mermaid
flowchart TD
    Start([User Sends<br/>Message]) --> CheckState{User<br/>State?}
    
    CheckState -->|HAS_CHART| ClassifyIntent[Classify Intent<br/>intent_router]
    
    ClassifyIntent --> IntentType{Intent<br/>Type?}
    
    IntentType -->|Chart Question| RetrieveChart[Retrieve User's<br/>Natal Chart]
    RetrieveChart --> GetThread[Get Conversation<br/>Thread History]
    GetThread --> GenAssistant[Generate Assistant<br/>Response with Context]
    GenAssistant --> UpdateThread[Update Thread<br/>with Q&A]
    UpdateThread --> SendAnswer[Send Response<br/>to User]
    
    IntentType -->|Profile Mgmt| HandleProfile[Handle Profile<br/>Command]
    HandleProfile --> SendAnswer
    
    IntentType -->|Transit Request| ParseDate[Parse Transit<br/>Date]
    ParseDate --> CalcTransit[Calculate<br/>Transit Positions]
    CalcTransit --> FormatTransit[Format Transit<br/>Data]
    FormatTransit --> GenTransitReading[Generate Transit<br/>Interpretation]
    GenTransitReading --> SendAnswer
    
    IntentType -->|General Astro| GenKnowledge[Generate Response<br/>from Astrology KB]
    GenKnowledge --> SendAnswer
    
    CheckState -->|Other| FirstTime[Process as<br/>First-Time User]
    
    SendAnswer --> End([Conversation<br/>Continues])
    
    style Start fill:#90EE90
    style End fill:#90EE90
    style ClassifyIntent fill:#87CEEB
    style GenAssistant fill:#FF9900
```

### 2.3 Multi-Profile Management Flow

```mermaid
flowchart TD
    Start([User Command]) --> CmdType{Command<br/>Type?}
    
    CmdType -->|/profiles| ListProfiles[Query All<br/>User Profiles]
    ListProfiles --> FormatList[Format Profile<br/>List]
    FormatList --> SendList[Send Profile<br/>List to User]
    SendList --> End([Done])
    
    CmdType -->|Switch Profile| FindProfile[Find Profile<br/>by Name/ID]
    FindProfile --> CheckExists{Profile<br/>Exists?}
    CheckExists -->|No| SendError[Send Error:<br/>Profile Not Found]
    SendError --> End
    CheckExists -->|Yes| UpdateActive[Set as Active<br/>Profile]
    UpdateActive --> LoadChart[Load Profile's<br/>Natal Chart]
    LoadChart --> SendConfirm[Send Confirmation<br/>with Chart Summary]
    SendConfirm --> End
    
    CmdType -->|Add Profile| CollectData[Collect Birth<br/>Data for New Profile]
    CollectData --> CreateProfile[Create New<br/>AstroProfile Record]
    CreateProfile --> GenNewChart[Generate Natal<br/>Chart]
    GenNewChart --> StoreProfile[Store Profile<br/>& Chart]
    StoreProfile --> SendSuccess[Send Success<br/>Message]
    SendSuccess --> End
    
    style Start fill:#90EE90
    style End fill:#90EE90
    style CreateProfile fill:#FFD700
```

---

## 3. Data Flow & Processing Pipeline

### 3.1 Message Processing Pipeline

```mermaid
flowchart LR
    subgraph "Stage 1: Ingestion"
        WH[Webhook<br/>Receives Update]
        VT[Verify Secret<br/>Token]
        DDup[Deduplication<br/>Check]
    end
    
    subgraph "Stage 2: Throttling"
        PT[Pending Check<br/>message_cache]
        CM[Combine<br/>Messages]
    end
    
    subgraph "Stage 3: Parsing"
        EX[Extract User<br/>& Message Data]
        ST[Load User<br/>State]
    end
    
    subgraph "Stage 4: Processing"
        RT[Route Based<br/>on State]
        PL[Process<br/>Logic]
    end
    
    subgraph "Stage 5: Response"
        FR[Format<br/>Response]
        SM[Split Long<br/>Messages]
        SD[Send via<br/>Telegram API]
    end
    
    WH --> VT
    VT --> DDup
    DDup -->|New| PT
    DDup -->|Duplicate| Discard([Discard])
    
    PT -->|First Message| EX
    PT -->|Has Pending| CM
    CM --> EX
    
    EX --> ST
    ST --> RT
    RT --> PL
    PL --> FR
    FR --> SM
    SM --> SD
    SD --> MR[Mark as<br/>Replied]
    
    style WH fill:#87CEEB
    style PL fill:#FFD700
    style SD fill:#90EE90
    style Discard fill:#FF6B6B
```

### 3.2 Birth Data Extraction Flow

```mermaid
flowchart TD
    Start([Raw User<br/>Message]) --> LLMExtract[LLM Extract<br/>Birth Data]
    
    LLMExtract --> ParseResult{Parsing<br/>Result?}
    
    ParseResult -->|Complete| HasAll[All Fields:<br/>DOB, Time, Location]
    ParseResult -->|Partial| HasSome[Some Fields<br/>Missing]
    ParseResult -->|Failed| HasNone[No Valid<br/>Data]
    
    HasAll --> ValidateCoords[Validate<br/>Coordinates]
    ValidateCoords --> NormalizeTime[Normalize<br/>Time & Timezone]
    NormalizeTime --> StoreTemp[Store in<br/>pending_birth_data]
    StoreTemp --> ShowConfirm[Show to User<br/>for Confirmation]
    
    HasSome --> IdentifyMissing[Identify<br/>Missing Fields]
    IdentifyMissing --> StoreMissing[Store in<br/>missing_fields]
    StoreMissing --> AskUser[Ask User for<br/>Missing Info]
    
    HasNone --> TryFormat[Try Classic<br/>Format Parser]
    TryFormat --> TryResult{Classic<br/>Format?}
    TryResult -->|Yes| HasAll
    TryResult -->|No| Error[Return Error<br/>Message]
    
    ShowConfirm --> End([Wait for<br/>Confirmation])
    AskUser --> End
    Error --> End
    
    style Start fill:#87CEEB
    style LLMExtract fill:#FF9900
    style ShowConfirm fill:#90EE90
```

### 3.3 Chart Generation Flow

```mermaid
flowchart TD
    Start([Confirmed<br/>Birth Data]) --> ConvertUTC[Convert to<br/>UTC Julian Day]
    
    ConvertUTC --> InitEphe[Initialize<br/>Swiss Ephemeris]
    
    InitEphe --> CalcSun[Calculate<br/>Sun Position]
    CalcSun --> CalcMoon[Calculate<br/>Moon Position]
    CalcMoon --> CalcPlanets[Calculate<br/>All Planets]
    CalcPlanets --> CalcHouses[Calculate<br/>House Cusps]
    CalcHouses --> CalcASC[Calculate<br/>Ascendant]
    
    CalcASC --> FormatJSON[Format as<br/>JSON Structure]
    FormatJSON --> ValidateChart[Validate<br/>Chart Data]
    
    ValidateChart --> StoreDB[Store in<br/>user_natal_charts]
    StoreDB --> LinkProfile[Link to<br/>Active Profile]
    
    LinkProfile --> GenText[Generate<br/>Human-Readable Text]
    GenText --> End([Chart Ready<br/>for Interpretation])
    
    style Start fill:#87CEEB
    style InitEphe fill:#66cc66
    style CalcPlanets fill:#FFD700
    style End fill:#90EE90
```

---

## 4. State Management

### 4.1 User State Transitions

```mermaid
stateDiagram-v2
    [*] --> AWAITING_BIRTH_DATA: New User
    
    AWAITING_BIRTH_DATA --> AWAITING_CLARIFICATION: Missing Fields
    AWAITING_BIRTH_DATA --> AWAITING_CONFIRMATION: Complete Data
    
    AWAITING_CLARIFICATION --> AWAITING_CLARIFICATION: Still Missing
    AWAITING_CLARIFICATION --> AWAITING_CONFIRMATION: Now Complete
    
    AWAITING_CONFIRMATION --> AWAITING_CLARIFICATION: User Requests Edit
    AWAITING_CONFIRMATION --> HAS_CHART: User Confirms
    
    HAS_CHART --> CHATTING_ABOUT_CHART: User Asks Question
    CHATTING_ABOUT_CHART --> CHATTING_ABOUT_CHART: Ongoing Conversation
    CHATTING_ABOUT_CHART --> HAS_CHART: Conversation Ends
    
    HAS_CHART --> AWAITING_EDIT_CONFIRMATION: /edit_birth Command
    AWAITING_EDIT_CONFIRMATION --> HAS_CHART: Confirmed
    AWAITING_EDIT_CONFIRMATION --> AWAITING_CLARIFICATION: Edit Requested
    
    note right of HAS_CHART
        Default state for users
        with complete natal chart
    end note
    
    note right of CHATTING_ABOUT_CHART
        Active conversation mode
        with thread context
    end note
```

### 4.2 Message Processing State Machine

```mermaid
stateDiagram-v2
    [*] --> Received: Webhook Called
    
    Received --> TokenCheck: Verify Token
    TokenCheck --> Rejected: Invalid Token
    TokenCheck --> DupCheck: Valid Token
    
    DupCheck --> Rejected: Duplicate
    DupCheck --> ThrottleCheck: New Message
    
    ThrottleCheck --> Queued: Has Pending
    ThrottleCheck --> Processing: No Pending
    
    Queued --> Combining: More Messages Arrive
    Combining --> Processing: First Message Ready
    
    Processing --> Routing: Parse & Load State
    Routing --> Handler: Determine Handler
    Handler --> Response: Generate Response
    Response --> Sending: Format & Split
    Sending --> Sent: API Call Success
    Sending --> Failed: API Call Error
    
    Sent --> MarkReplied: Update Cache
    MarkReplied --> [*]: Done
    
    Rejected --> [*]: Dropped
    Failed --> Retry: Transient Error
    Failed --> [*]: Permanent Error
    Retry --> Sending: Retry Attempt
```

---

## 5. Sequence Diagrams

### 5.1 First-Time User: Birth Data Extraction

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant W as Webhook
    participant B as Bot
    participant L as LLM
    participant D as Database
    
    U->>T: Send birth data message
    T->>W: POST /webhook
    W->>W: Verify secret token
    W->>W: Check duplicate
    W->>B: handle_telegram_update()
    
    B->>D: Load or create User
    Note over B,D: State: AWAITING_BIRTH_DATA
    
    B->>L: extract_birth_data(message)
    L->>L: Parse with LLM
    L-->>B: Extracted data + missing fields
    
    alt All fields present
        B->>B: Normalize & validate
        B->>D: Store pending_birth_data
        B->>D: Update state → AWAITING_CONFIRMATION
        B->>T: Send confirmation request
        T->>U: Show birth data for review
    else Missing fields
        B->>D: Store missing_fields list
        B->>D: Update state → AWAITING_CLARIFICATION
        B->>L: generate_clarification_question()
        L-->>B: Question text
        B->>T: Send question
        T->>U: Ask for missing info
    end
```

### 5.2 Chart Generation & First Reading

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant B as Bot
    participant A as Astrology Engine
    participant SE as Swiss Ephemeris
    participant L as LLM
    participant D as Database
    
    U->>T: Reply "CONFIRM"
    T->>B: Process confirmation
    
    B->>D: Retrieve pending_birth_data
    B->>A: generate_natal_chart(birth_data)
    
    A->>SE: Calculate Sun position
    SE-->>A: Sun data
    A->>SE: Calculate Moon position
    SE-->>A: Moon data
    A->>SE: Calculate planets
    SE-->>A: Planet positions
    A->>SE: Calculate houses
    SE-->>A: House cusps
    
    A-->>B: Complete natal chart JSON
    
    B->>D: Create UserNatalChart record
    B->>D: Link to AstroProfile
    B->>D: Update state → HAS_CHART
    
    B->>L: interpret_chart(chart_json)
    L->>L: Generate reading with LLM
    L-->>B: Astrological interpretation
    
    B->>D: Store Reading record
    B->>D: Track prompt metadata
    
    B->>T: Send reading (split if needed)
    T->>U: Deliver complete reading
    
    Note over U,D: User now has chart and can chat
```

### 5.3 Assistant Conversation with Context

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant B as Bot
    participant IR as Intent Router
    participant TM as Thread Manager
    participant L as LLM
    participant D as Database
    
    U->>T: "What are my career strengths?"
    T->>B: Process message
    
    B->>D: Load User (state: HAS_CHART)
    B->>D: Load active AstroProfile
    B->>D: Load natal chart
    
    B->>IR: classify_intent(message)
    IR->>L: LLM classification
    L-->>IR: Intent: chart_question
    IR-->>B: Route to assistant handler
    
    B->>TM: get_conversation_thread(user_id)
    TM->>D: Query ConversationThread
    TM-->>B: Last 10 messages with context
    
    B->>L: generate_assistant_response()
    Note over L: Context includes:<br/>- User question<br/>- Natal chart<br/>- Conversation history<br/>- User profile
    L->>L: Generate contextual answer
    L-->>B: Personalized response
    
    B->>TM: add_message_to_thread(question, answer)
    TM->>D: Store in ConversationThread
    
    B->>T: Send response
    T->>U: Deliver answer
    
    Note over U,D: Thread context maintained<br/>for ongoing conversation
```

### 5.4 Message Throttling & Combining

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant W as Webhook
    participant MC as Message Cache
    participant B as Bot
    participant D as Database
    
    U->>T: Send message 1
    T->>W: Webhook call 1
    W->>MC: mark_if_new(msg1)
    MC->>D: INSERT ProcessedMessage (msg1, reply_sent=False)
    MC-->>W: is_new=True
    W->>MC: has_pending_reply(user)?
    MC-->>W: No other pending
    W->>B: Process msg1
    Note over B: Processing takes 3 seconds...
    
    U->>T: Send message 2
    T->>W: Webhook call 2
    W->>MC: mark_if_new(msg2)
    MC->>D: INSERT ProcessedMessage (msg2, reply_sent=False)
    MC-->>W: is_new=True
    W->>MC: has_pending_reply(user)?
    MC->>D: Query WHERE reply_sent=False
    MC-->>W: Yes, msg1 pending
    W-->>T: Return throttled=True
    Note over W,T: msg2 queued, not processed yet
    
    U->>T: Send message 3
    T->>W: Webhook call 3
    W->>MC: mark_if_new(msg3)
    MC->>D: INSERT ProcessedMessage (msg3, reply_sent=False)
    MC-->>W: is_new=True
    W->>MC: has_pending_reply(user)?
    MC-->>W: Yes, still pending
    W-->>T: Return throttled=True
    
    B->>T: Send reply to msg1
    T->>U: Deliver response
    B->>MC: mark_all_pending_as_replied(user)
    MC->>D: UPDATE ProcessedMessage SET reply_sent=True
    
    Note over U,D: Next message will combine msg2 + msg3
```

---

## 6. Database Schema

### 6.1 Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ AstroProfile : "has many"
    User ||--o{ BirthData : "has many (legacy)"
    User ||--o{ Reading : "has many"
    User ||--o{ ProcessedMessage : "has many"
    User ||--o{ ConversationThread : "has many"
    User ||--|| AstroProfile : "active_profile (FK)"
    
    AstroProfile ||--o| UserNatalChart : "has one"
    
    User {
        string telegram_id PK
        datetime first_seen
        datetime last_seen
        string state
        text natal_chart_json "legacy"
        string missing_fields
        int active_profile_id FK
        boolean assistant_mode
        text pending_birth_data
        text pending_normalized_data
        text user_profile
    }
    
    AstroProfile {
        int id PK
        string telegram_id FK
        string name
        string profile_type
        text birth_data_json
        text natal_chart_json "legacy"
        datetime created_at
    }
    
    UserNatalChart {
        int id PK
        string telegram_id FK
        int profile_id FK
        text chart_json
        string chart_hash
        text birth_data_json
        text ephe_version
        datetime created_at
    }
    
    BirthData {
        int id PK
        string telegram_id FK
        string dob
        string time
        float lat
        float lng
        datetime created_at
    }
    
    Reading {
        int id PK
        string telegram_id FK
        int birth_data_id FK
        text reading_text
        boolean delivered
        datetime created_at
        datetime delivered_at
        string prompt_name
        string prompt_hash
        string model_used
    }
    
    ProcessedMessage {
        int id PK
        string telegram_id FK
        int message_id
        datetime processed_at
        boolean reply_sent
        datetime reply_sent_at
        text message_text
    }
    
    ConversationThread {
        int id PK
        string telegram_id FK
        string role
        text content
        datetime created_at
        string metadata
    }
```

### 6.2 Key Database Patterns

**Multi-Profile Architecture:**
- Each `User` can have multiple `AstroProfile` records (self, partner, friends)
- `active_profile_id` points to the currently selected profile
- Each `AstroProfile` can have one `UserNatalChart` with versioned data

**Message Deduplication:**
- `ProcessedMessage` stores every webhook message
- Unique constraint on `(telegram_id, message_id)` prevents duplicates
- `reply_sent` flag enables throttling logic

**Conversation Context:**
- `ConversationThread` stores Q&A pairs with timestamps
- Enables context-aware assistant responses
- Limited to recent messages (e.g., last 10) to manage token usage

**Reading Reproducibility:**
- `Reading` table tracks which prompt template and model were used
- `prompt_hash` enables detection of prompt changes
- Allows re-generating readings with updated prompts

---

## 7. Deployment Architecture

### 7.1 Local Development

```mermaid
graph TB
    subgraph "Developer Machine"
        subgraph "Docker Container"
            APP[FastAPI App<br/>Port 8000]
            SQLITE[(SQLite DB<br/>natal_nataly.sqlite)]
            EPHE[Swiss Ephemeris<br/>ephe/]
        end
        
        NGROK[ngrok<br/>Port 8000]
        ENV[.env File<br/>Local Config]
    end
    
    subgraph "External Services"
        TG[Telegram API]
        GROQ[Groq API<br/>LLM Provider]
    end
    
    TG -->|Webhook via HTTPS| NGROK
    NGROK -->|HTTP Tunnel| APP
    APP -->|API Calls| GROQ
    APP -->|Read/Write| SQLITE
    APP -->|Ephemeris Data| EPHE
    ENV -.->|Environment Variables| APP
    
    style APP fill:#87CEEB
    style SQLITE fill:#cc66ff
    style NGROK fill:#FFD700
```

### 7.2 Production Deployment (Render)

```mermaid
graph TB
    subgraph "Render Cloud Platform"
        subgraph "Web Service"
            APP[FastAPI App<br/>Docker Container]
            EPHE[Swiss Ephemeris<br/>Volume Mount]
        end
        
        POSTGRES[(PostgreSQL<br/>Managed DB)]
        
        LB[Load Balancer<br/>HTTPS]
    end
    
    subgraph "External Services"
        TG[Telegram API]
        GROQ[Groq/DeepSeek API<br/>LLM Provider]
    end
    
    subgraph "Configuration"
        ENV[Environment Variables<br/>Render Dashboard]
        WEBHOOK[Webhook URL<br/>your-app.onrender.com]
    end
    
    TG -->|Webhook HTTPS POST| LB
    LB -->|Forward| APP
    APP -->|SQL Queries| POSTGRES
    APP -->|LLM Requests| GROQ
    APP -->|Ephemeris Data| EPHE
    
    ENV -.->|Config| APP
    WEBHOOK -.->|Registered with| TG
    
    style APP fill:#87CEEB
    style POSTGRES fill:#cc66ff
    style LB fill:#66cc66
    style GROQ fill:#FF9900
```

### 7.3 Data Flow: Development vs Production

```mermaid
graph LR
    subgraph "Development"
        DEV_MSG[Message] --> DEV_NGROK[ngrok]
        DEV_NGROK --> DEV_APP[App]
        DEV_APP --> DEV_SQLITE[(SQLite)]
    end
    
    subgraph "Production"
        PROD_MSG[Message] --> PROD_LB[Load Balancer]
        PROD_LB --> PROD_APP[App]
        PROD_APP --> PROD_PG[(PostgreSQL)]
    end
    
    style DEV_APP fill:#FFD700
    style PROD_APP fill:#66cc66
    style DEV_SQLITE fill:#87CEEB
    style PROD_PG fill:#cc66ff
```

**Key Differences:**

| Aspect | Development | Production |
|--------|-------------|------------|
| Database | SQLite (file-based) | PostgreSQL (managed) |
| HTTPS | ngrok tunnel | Native HTTPS via Render |
| Scalability | Single instance | Auto-scaling capable |
| Persistence | Local file system | Cloud volumes + managed DB |
| Logs | Console output | Render log streaming |
| Env Config | .env file | Render dashboard |

---

## 8. Key Metrics & Analytics Points

For product analysts tracking the system, here are the key metrics available:

### 8.1 User Metrics

```sql
-- Total users
SELECT COUNT(*) FROM users;

-- Users by state
SELECT state, COUNT(*) as count 
FROM users 
GROUP BY state;

-- Active users (last 7 days)
SELECT COUNT(*) FROM users 
WHERE last_seen > NOW() - INTERVAL '7 days';

-- Users with multiple profiles
SELECT COUNT(*) FROM (
  SELECT telegram_id 
  FROM astro_profiles 
  GROUP BY telegram_id 
  HAVING COUNT(*) > 1
) multi_profile_users;
```

### 8.2 Engagement Metrics

```sql
-- Total readings generated
SELECT COUNT(*) FROM readings;

-- Readings per user (distribution)
SELECT telegram_id, COUNT(*) as reading_count 
FROM readings 
GROUP BY telegram_id 
ORDER BY reading_count DESC;

-- Conversation thread depth
SELECT AVG(message_count) as avg_thread_depth
FROM (
  SELECT telegram_id, COUNT(*) as message_count
  FROM conversation_threads
  GROUP BY telegram_id
) threads;

-- Messages processed per day
SELECT DATE(processed_at) as date, COUNT(*) as messages
FROM processed_messages
GROUP BY DATE(processed_at)
ORDER BY date DESC
LIMIT 30;
```

### 8.3 Performance Metrics

```sql
-- Duplicate/throttled message rate
SELECT 
  COUNT(*) as total_messages,
  COUNT(CASE WHEN reply_sent = FALSE THEN 1 END) as throttled
FROM processed_messages;

-- Average time to first chart (user onboarding)
SELECT AVG(
  EXTRACT(EPOCH FROM (created_at - first_seen))
) / 60 as avg_minutes_to_chart
FROM users u
JOIN user_natal_charts c ON u.telegram_id = c.telegram_id
WHERE u.state = 'has_chart';
```

### 8.4 Feature Usage

```sql
-- Command usage (from processed_messages)
SELECT 
  CASE 
    WHEN message_text LIKE '/my_data%' THEN 'my_data'
    WHEN message_text LIKE '/profiles%' THEN 'profiles'
    WHEN message_text LIKE '/my_chart_raw%' THEN 'chart_raw'
    WHEN message_text LIKE '/edit_birth%' THEN 'edit_birth'
    ELSE 'conversation'
  END as command_type,
  COUNT(*) as usage_count
FROM processed_messages
WHERE message_text IS NOT NULL
GROUP BY command_type
ORDER BY usage_count DESC;

-- Profile types distribution
SELECT profile_type, COUNT(*) as count
FROM astro_profiles
GROUP BY profile_type;
```

---

## Summary

This document provides comprehensive visualizations for understanding:

1. **System Architecture**: How components interact and communicate
2. **User Journeys**: Step-by-step flows for different user scenarios  
3. **Data Processing**: How messages flow through the system
4. **State Management**: How user states transition based on actions
5. **Sequence Diagrams**: Detailed interaction patterns for key features
6. **Database Schema**: Data model and relationships
7. **Deployment**: Development vs production architecture
8. **Analytics**: Key metrics and queries for product analysis

All diagrams use Mermaid format for easy rendering in GitHub and other Markdown viewers.

For implementation details, see:
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Codebase organization
- [SETUP.md](SETUP.md) - Local development setup
- [guides/STATEFUL_BOT_GUIDE.md](guides/STATEFUL_BOT_GUIDE.md) - State management details
- [guides/CONVERSATION_THREAD_GUIDE.md](guides/CONVERSATION_THREAD_GUIDE.md) - Thread management
