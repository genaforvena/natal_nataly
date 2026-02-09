# Unified Natal Chart System - Usage Guide

## Overview

The Nataly bot now uses a **unified JSON chart format** as the single source of truth for all natal chart data. Charts can be either:
- **Generated** from birth data (DOB, time, coordinates) using Swiss Ephemeris
- **Uploaded** by users from external sources like AstroSeek

## Chart Format

All charts (generated or uploaded) use the same standardized JSON structure:

```json
{
  "planets": {
    "Sun": {
      "sign": "Capricorn",
      "deg": 10.50,
      "house": 4,
      "retrograde": false
    },
    "Moon": {
      "sign": "Libra",
      "deg": 10.10,
      "house": 1,
      "retrograde": false
    },
    ...
  },
  "houses": {
    "1": {"sign": "Virgo", "deg": 26.30},
    "2": {"sign": "Libra", "deg": 22.15},
    ...
  },
  "aspects": [
    {
      "from": "Sun",
      "to": "Moon",
      "type": "Square",
      "orb": 0.30,
      "applying": false
    },
    ...
  ],
  "source": "generated",  // or "uploaded"
  "original_input": "DOB: 1990-01-15, Time: 10:30...",
  "engine_version": "swisseph 2.10.03",
  "created_at": "2026-02-10T12:00:00Z"
}
```

## User Commands

### Chart Creation

#### Generate from Birth Data
Send birth data in the format:
```
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060
```

The bot will:
1. Parse your input using LLM
2. Validate and normalize data
3. Generate natal chart using Swiss Ephemeris
4. Store in unified format
5. Ask for confirmation

#### Upload Existing Chart
```
/upload_chart
```

Then send your chart in AstroSeek format:
```
Sun: 10°30' Capricorn, House 4
Moon: 10°10' Libra, House 1
Mercury: 5°45' Capricorn, House 4
Venus: 15°48' Capricorn, House 4
Mars: 20°15' Sagittarius, House 3
Jupiter: 8°22' Cancer, House 10 (R)
...

House 1: 26°30' Virgo
House 2: 22°15' Libra
...

Sun Square Moon (orb: 0.3)
Sun Conjunction Venus (orb: 5.4)
...
```

The bot will:
1. Parse the chart text
2. Validate structure and data
3. Store in unified format
4. Show summary with key planets

### View Your Data

#### /my_data
View your birth data and chart information:
- Chart source (generated or uploaded)
- Engine version
- Key planets (Sun, Moon, Ascendant)
- Birth data (if generated from birth data)
- Timezone info (if available)

#### /my_chart_raw
Get complete chart JSON:
- Full planet positions
- House cusps
- Aspects
- Metadata

Perfect for:
- Exporting your chart
- Verifying on AstroSeek or other services
- Debugging

#### /my_readings
List all your readings:
- Shows reading ID, date, model used
- Shows which chart was used for each reading
- Use `/my_readings <id>` to view specific reading

### Modify Your Chart

#### /edit_birth
Update your birth data and regenerate chart:
1. Shows current data
2. Prompts for new data
3. Generates new chart from Swiss Ephemeris
4. Replaces current active chart

#### /upload_chart
Replace current chart with an uploaded one:
1. Enter upload mode
2. Send chart text
3. Validates and stores new chart
4. Deactivates previous chart

### Help

#### /help
Shows all available commands and tips

## Key Features

### 1. Single Source of Truth
All chart operations (readings, questions, analysis) use the stored JSON chart from the `user_natal_charts` table. The bot **never regenerates** the chart unless you explicitly request it via `/edit_birth`.

### 2. Support for Both Generated and Uploaded Charts
- **Generated**: Precise calculations using Swiss Ephemeris
- **Uploaded**: Use charts from professional astrology software like AstroSeek

### 3. Chart Versioning
Each chart stores:
- Creation timestamp
- Source (generated/uploaded)
- Engine version (for reproducibility)
- Original input (for debugging)

### 4. Active Chart Management
Only one chart is active at a time per user. When you:
- Generate a new chart → Previous chart is deactivated
- Upload a new chart → Previous chart is deactivated

Old charts are preserved in the database for history.

### 5. Readings Linked to Charts
Each reading can be traced back to:
- Which chart was used
- When the chart was created
- Chart source (generated vs uploaded)

## Example Workflows

### Workflow 1: New User with Birth Data
1. User: Send birth data
2. Bot: Validates and asks for confirmation
3. User: "CONFIRM"
4. Bot: Generates chart using Swiss Ephemeris
5. Bot: Stores in unified format
6. User: Can now ask questions about their chart

### Workflow 2: User with AstroSeek Chart
1. User: `/upload_chart`
2. Bot: Explains format and waits for chart
3. User: Pastes chart from AstroSeek
4. Bot: Parses and validates chart
5. Bot: Stores in unified format
6. User: Can now ask questions about their chart

### Workflow 3: User Updates Birth Data
1. User: `/edit_birth`
2. Bot: Shows current data
3. User: Sends new birth data
4. Bot: Generates new chart
5. Bot: Deactivates old chart, activates new one
6. All future readings use new chart

### Workflow 4: Switching Between Charts
Users can have multiple charts in their history:
- Only one is active at a time
- Future feature: Switch between charts via command

## Technical Details

### Database Schema
- **Table**: `user_natal_charts`
- **Primary Key**: `id`
- **Fields**:
  - `telegram_id`: User identifier
  - `chart_json`: Complete chart in JSON format
  - `source`: "generated" or "uploaded"
  - `original_input`: Original text from user
  - `engine_version`: Software version used
  - `is_active`: Boolean (only one active per user)
  - `created_at`: Timestamp
  - `updated_at`: Timestamp

### Chart Generation Pipeline
1. **RAW_INPUT**: User sends message
2. **PARSE**: LLM extracts birth data
3. **NORMALIZE**: System validates and enriches data
4. **CHART_GENERATED**: Swiss Ephemeris calculates positions
5. **READING_SENT**: AI interprets and responds

### Chart Upload Pipeline
1. **RAW_INPUT**: User uploads chart text
2. **PARSE**: Chart parser extracts positions
3. **VALIDATE**: System checks structure and ranges
4. **CHART_STORED**: Saved in unified format
5. **CONFIRMATION**: User sees summary

## Supported Chart Formats

### AstroSeek Format (Primary)
```
Planet: degree°minutes' Sign, House number (optional R)
House number: degree°minutes' Sign
Planet1 AspectType Planet2 (orb: value)
```

Example:
```
Sun: 10°30' Capricorn, House 4
Jupiter: 8°22' Cancer, House 10 (R)
House 1: 26°30' Virgo
Sun Square Moon (orb: 0.3)
```

### Future Formats
- Astro.com format
- JSON import
- CSV import

## Benefits

1. **Consistency**: Same chart format everywhere
2. **Flexibility**: Support both generated and uploaded charts
3. **Traceability**: Track which chart was used for each reading
4. **Debugging**: Full pipeline visibility for developers
5. **User Trust**: Users can verify and upload their own charts
6. **Reproducibility**: Chart versioning ensures consistent results

## Notes

- Charts are never regenerated unless explicitly requested
- Old charts are preserved (not deleted)
- Only one chart is active per user at a time
- All readings reference the active chart at the time of generation
- Debug commands (for developers only) provide full pipeline visibility
