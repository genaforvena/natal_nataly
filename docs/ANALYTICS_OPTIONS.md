# Analytics Options for Natal Nataly

This document explores free options for collecting analytics on user interactions in the Natal Nataly Telegram bot, focusing on user retention and message tracking.

## Comparison of Free Options

| Feature | SQL-based (Implemented) | PostHog | Telemetree |
|---------|--------------------------|---------|------------|
| **Focus** | Data Ownership | Product Analytics | Telegram Specific |
| **Free Tier** | 100% Free | 1M events/mo | Generous free tier |
| **Dashboard** | Custom SQL / Metabase | Very Powerful | Native Telegram UI |
| **Retention** | Manual SQL Queries | Built-in Cohorts | Built-in Retention |
| **Ease of Setup** | Native Integration | Moderate (SDK) | Easy (SDK) |
| **Privacy** | **Highest (In-house)** | Third-party | Third-party |

---

## 1. SQL-based Analytics (Current Implementation)
We have implemented a native SQL-based analytics solution to ensure all user data remains in-house, fulfilling privacy and data ownership requirements.

### Key Features:
- **No Third-party Tracking**: All events are stored in your own PostgreSQL/SQLite database.
- **Data Transparency**: You have full access to the raw events.
- **Minimal Overhead**: Uses the existing SQLAlchemy setup and models with short-lived sessions per event.

### Tracked Events:
- `message_received`: Captured at the webhook level for every incoming message.
- `profile_created`: Tracked when a new astrology profile is created.
- `chart_generated`: Tracked when a natal chart is successfully generated.
- `reading_sent`: Tracked when the bot delivers a reading to the user.

### Sample Analytics Queries:

#### Daily Active Users (DAU)
```sql
SELECT
    date(created_at) as day,
    count(distinct telegram_id) as active_users
FROM analytics_events
GROUP BY 1
ORDER BY 1 DESC;
```

#### User Retention (Day 1)

**PostgreSQL:**
```sql
WITH user_first_day AS (
    SELECT telegram_id, date(first_seen) as join_day
    FROM users
)
SELECT
    join_day,
    count(distinct u.telegram_id) as new_users,
    count(distinct CASE WHEN date(e.created_at) = join_day + interval '1 day' THEN u.telegram_id END) as day_1_retention
FROM user_first_day u
LEFT JOIN analytics_events e ON u.telegram_id = e.telegram_id
GROUP BY 1
ORDER BY 1 DESC;
```

**SQLite:**
```sql
WITH user_first_day AS (
    SELECT telegram_id, date(first_seen) as join_day
    FROM users
)
SELECT
    join_day,
    count(distinct u.telegram_id) as new_users,
    count(distinct CASE WHEN date(e.created_at) = date(join_day, '+1 day') THEN u.telegram_id END) as day_1_retention
FROM user_first_day u
LEFT JOIN analytics_events e ON u.telegram_id = e.telegram_id
GROUP BY 1
ORDER BY 1 DESC;
```

---

## 2. PostHog
Excellent for tracking user journeys if you are comfortable with third-party hosting. Provides powerful built-in dashboards.

---

## 3. Telemetree
Specifically designed for Telegram bots. Good for quick bot-centric metrics without custom SQL.

---

## Implementation Details
The `AnalyticsService` in `src/services/analytics.py` uses the `SQLProvider` by default. It saves events to the `analytics_events` table defined in `src/models.py`.
