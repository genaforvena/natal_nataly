# Kerykeion Migration Guide

## Overview

This document describes the migration from direct Swiss Ephemeris (pyswisseph) to Kerykeion library for natal chart generation.

## What Changed

### Before (Old Implementation)
- **Module**: `astrology.py`
- **Function**: `generate_natal_chart(dob, time, lat, lng, original_input)`
- **Backend**: Direct pyswisseph calls
- **Output**: JSON with planets, houses, aspects

### After (New Implementation)
- **Module**: `services/chart_builder.py`
- **Function**: `build_natal_chart_text_and_json(name, year, month, day, hour, minute, lat, lng, city, nation, tz_str)`
- **Backend**: Kerykeion (which uses Swiss Ephemeris internally)
- **Output**: Dictionary with:
  - `text_export`: AstroSeek-compatible text format
  - `chart_json`: Structured JSON with planets, houses, aspects, angles, metadata

## Key Improvements

1. **Better Timezone Handling**: Automatically determines timezone from coordinates using `timezonefinder`
2. **Text Export**: Generates human-readable text export in AstroSeek format
3. **Richer Data**: Includes angles (ASC, MC) and more detailed aspect information
4. **Maintained Compatibility**: Output format is compatible with existing LLM integration

## Dependencies Added

```txt
kerykeion
timezonefinder
```

## Integration in bot.py

The new `generate_natal_chart_kerykeion()` function in `bot.py`:
1. Parses birth data (dob: "YYYY-MM-DD", time: "HH:MM")
2. Calls `build_natal_chart_text_and_json()` from Kerykeion
3. Converts output to old format for LLM compatibility
4. Stores both text export and JSON in the chart data

## Data Format Conversion

### New Format (Kerykeion Output)
```json
{
  "planets": [
    {"name": "Sun", "sign": "Taurus", "position": 24.39, "house": 9, "retrograde": false}
  ],
  "houses": [
    {"number": 1, "sign": "Virgo", "position": 19.27}
  ],
  "aspects": [
    {"planet1": "Sun", "planet2": "Moon", "aspect": "Trine", "orb": 5.51, "applying": false}
  ],
  "angles": {
    "asc": {"sign": "Virgo", "position": 19.27},
    "mc": {"sign": "Gemini", "position": 17.46}
  },
  "meta": {
    "city": "New York",
    "nation": "US",
    "lat": 40.7128,
    "lng": -74.006,
    "timezone": "America/New_York",
    "engine": "kerykeion_swisseph"
  }
}
```

### Old Format (LLM Compatible)
```json
{
  "planets": {
    "Sun": {"sign": "Taurus", "deg": 24.39, "house": 9, "retrograde": false},
    "Ascendant": {"sign": "Virgo", "deg": 19.27, "house": 1, "retrograde": false}
  },
  "houses": {
    "1": {"sign": "Virgo", "deg": 19.27}
  },
  "aspects": [
    {"from": "Sun", "to": "Moon", "type": "Trine", "orb": 5.51, "applying": false}
  ],
  "source": "generated",
  "original_input": "DOB: 1990-05-15, Time: 14:30, Lat: 40.7128, Lng: -74.006",
  "engine_version": "kerykeion_swisseph",
  "created_at": "2026-02-10T01:33:52.187Z",
  "_kerykeion_data": { ... },
  "_text_export": "..."
}
```

## Text Export Format

The text export follows AstroSeek format:

```
City: New York
Country: US
Latitude, Longitude: 40.7128, -74.006
House system: Placidus system

Planets:
Sun in Taurus 24°39', in 9th House
Moon in Aquarius 0°30', in 5th House
Mercury in Taurus 7°58', Retrograde, in 8th House
...

Angles:
ASC in Virgo 19°27'
MC in Gemini 17°46'

Houses:
1st House in Virgo 19°27'
2nd House in Libra 14°33'
...

Aspects:
Sun Trine Moon (Orb: 5°51', Separating)
Sun Trine Saturn (Orb: 0°35', Applying)
...
```

## Testing

Run the test script to validate chart generation:

```bash
python3 test_chart_builder.py
```

## Backward Compatibility

The migration maintains full backward compatibility:
- Old chart format is still supported by the LLM
- Database structure unchanged
- API endpoints unchanged
- Text export can be used for future enhancements

## Files Modified

1. **requirements.txt** - Added kerykeion, timezonefinder
2. **services/chart_builder.py** - New chart generation module (created)
3. **services/__init__.py** - Package initialization (created)
4. **bot.py** - Updated to use new chart builder
5. **astrology.py** - Marked as deprecated with migration notice

## Files Removed

None. The old `astrology.py` is kept for reference.

## Future Improvements

1. Use text export for enhanced LLM prompts
2. Store text export separately in database for quick retrieval
3. Add support for synastry and composite charts (Kerykeion supports these)
4. Leverage Kerykeion's built-in report generation features

## Rollback Plan

If issues arise, rollback is straightforward:
1. Revert bot.py import: `from astrology import generate_natal_chart`
2. Replace `generate_natal_chart_kerykeion()` calls with `generate_natal_chart()`
3. Remove kerykeion imports

The old code is still present in `astrology.py` and functional.
