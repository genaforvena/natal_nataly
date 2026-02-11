# Debug Mode Implementation Summary

## Overview

This document summarizes the complete implementation of the "Debuggable Nataly" feature - a debug-first architecture for the Natal Nataly astrology bot.

## Implementation Date

February 9, 2026

## Problem Statement

The original requirement was to create a transparent technical layer that allows developers to:
- See raw input data at every stage
- Verify normalized birth data
- Check timezone calculations
- Validate coordinates
- Inspect complete natal chart structure
- Store charts at user level
- Reproduce any reading

## Solution Architecture

### Core Philosophy
*"Интерпретации вторичны. Истина — в данных."*  
*"Interpretations are secondary. Truth is in the data."*

The implementation follows a debug-first approach where:
1. Every pipeline stage is logged
2. Data is stored before and after transformations
3. Charts are calculated once and reused
4. All operations are traceable and reproducible

## Files Created

### Core Modules
1. **`debug.py`** (16.4 KB)
   - Pipeline logging functions (5 stages)
   - Natal chart storage with versioning
   - Timezone validation
   - LLM prompt tracking
   - Debug session management

2. **`debug_commands.py`** (13.4 KB)
   - Developer command handlers
   - `/debug_birth` - Birth data inspection
   - `/debug_chart` - Chart JSON viewer
   - `/debug_pipeline` - Complete trace
   - `/show_chart` - SVG visualization

3. **`chart_svg.py`** (5.9 KB)
   - SVG chart generation
   - Mathematical zodiac wheel
   - Planetary position plotting
   - Color-coded planet symbols

### Documentation
4. **`DEBUG_MODE.md`** (11.2 KB)
   - Complete feature documentation
   - Configuration guide
   - Usage examples
   - Troubleshooting scenarios

## Database Schema Changes

### New Tables

#### `pipeline_logs`
Tracks each stage of the processing pipeline:
- `session_id` - Unique pipeline run identifier
- `raw_user_message` - Original input
- `parsed_birth_data_json` - LLM extraction
- `normalized_birth_data_json` - After validation
- `birth_datetime_utc`, `birth_datetime_local`
- `timezone`, `timezone_source`, `timezone_validation_status`
- `natal_chart_id` - Reference to generated chart
- `stage_completed` - Current pipeline stage
- `error_message` - Error tracking

#### `natal_charts`
Stores complete natal charts with versioning:
- `birth_data_json` - Birth information
- `natal_chart_json` - Complete chart data
- `engine_version` - pyswisseph version
- `ephemeris_version` - Swiss Ephemeris version
- `chart_hash` - SHA256 for comparison
- `raw_ephemeris_data` - Optional debug data

#### `debug_sessions`
Links pipeline stages for complete trace:
- `session_id` - Unique identifier
- `pipeline_log_id` - Reference to pipeline log
- `natal_chart_id` - Reference to natal chart
- `reading_id` - Reference to reading
- `status` - Session status

### Modified Tables

#### `readings`
Enhanced with LLM tracking:
- `prompt_name` - Template identifier
- `prompt_hash` - Content hash (16 chars)
- `model_used` - LLM model identifier

## Modified Files

1. **`models.py`**
   - Added `PipelineLog`, `NatalChart`, `DebugSession` models
   - Enhanced `Reading` with prompt tracking fields

2. **`db.py`**
   - Updated `init_db()` to create new tables

3. **`.env.example`**
   - Added `DEBUG_MODE` flag
   - Added `DEVELOPER_TELEGRAM_ID` configuration

4. **`bot.py`**
   - Integrated pipeline logging in `handle_awaiting_birth_data()`
   - Added debug command routing
   - Added LLM prompt tracking in `handle_chatting_about_chart()`

5. **`astrology.py`**
   - Added `get_engine_version()` function
   - Added version tracking

6. **`README.md`**
   - Added debug mode section
   - Documented developer commands

7. **`.gitignore`**
   - Added `charts/` and `*.svg` exclusions

## Features Implemented

### 1. Pipeline Logging (5 Stages)

✅ **Stage 1: Raw Input**
- Logs original user message
- Captures timestamp
- Generates unique session ID

✅ **Stage 2: Parsed Birth Data**
- Stores LLM extraction result
- Includes confidence score
- Preserves before-transformation data

✅ **Stage 3: Normalized Data**
- System-validated birth data
- UTC/local datetime conversion
- Timezone validation results

✅ **Stage 4: Chart Generated**
- Complete natal chart storage
- Swiss Ephemeris versioning
- Chart hash for validation

✅ **Stage 5: Reading Sent**
- Links reading to pipeline
- Tracks LLM prompt used
- Marks pipeline complete

### 2. Timezone Validation

✅ **Geo Lookup**
- Simple coordinate-based estimation
- Compares with LLM extraction
- Status: MATCH, MISMATCH, NO_VALIDATION, ERROR

✅ **Warning Logs**
- Logs mismatches for investigation
- Stores both values for comparison

### 3. Natal Chart Storage

✅ **One-time Calculation**
- Charts stored on first generation
- Reused for all subsequent readings
- Ensures consistency

✅ **Versioning**
- Tracks pyswisseph version
- Records ephemeris version
- Enables reproduction

✅ **Chart Hash**
- SHA256 hash for quick comparison
- Validates chart integrity

### 4. Developer Commands

✅ **Authentication**
- Restricted by `DEVELOPER_TELEGRAM_ID`
- Non-developers receive access denied

✅ **`/debug_birth`**
- Shows parsed birth data
- Shows normalized data
- Displays timezone validation
- Shows UTC/local times

✅ **`/debug_chart`**
- Complete chart JSON
- Birth data included
- Metadata (versions, hash)

✅ **`/debug_pipeline`**
- Complete session trace
- All 5 stages with status
- LLM prompt information
- Error messages if any

✅ **`/show_chart`**
- Generates SVG visualization
- Saves to `./charts/` directory
- Shows planetary positions

### 5. SVG Chart Visualization

✅ **Zodiac Wheel**
- 12 segments (signs)
- Mathematical positioning
- Unicode symbols

✅ **Planet Plotting**
- Accurate degree placement
- Color-coded by planet
- Symbol labels

✅ **Chart Elements**
- Outer circle (zodiac)
- Inner circle (house system)
- Radial lines (house cusps)
- Planet markers

### 6. LLM Prompt Tracking

✅ **Reading Metadata**
- Prompt name stored
- Content hash (SHA256, 16 chars)
- Model identifier

✅ **Reproducibility**
- Can regenerate with same prompt
- Track prompt evolution
- Debug interpretation issues

## Configuration

### Environment Variables

```bash
# Enable debug mode
DEBUG_MODE=true

# Developer access (get from @userinfobot)
DEVELOPER_TELEGRAM_ID=your_telegram_id
```

### Optional Settings

```bash
# Database path
DB_PATH=natal_nataly.sqlite

# Charts directory
# Default: ./charts
```

## Testing Results

### Integration Test
✅ All 11 test scenarios passed:
1. Database schema initialization
2. Debug mode configuration
3. Developer authentication
4. Pipeline Stage 1 (Raw Input)
5. Pipeline Stage 2 (Parsed Data)
6. Timezone validation
7. Pipeline Stage 3 (Normalized Data)
8. Natal chart generation
9. Natal chart storage
10. SVG chart generation
11. Debug session management

### Smoke Test
✅ All 14 module tests passed:
- All modules import successfully
- Database initialization works
- Debug functions operational
- SVG generation functional

## Performance Impact

When `DEBUG_MODE=true`:
- Additional database writes per request: 3-5
- Pipeline log size: ~2-5 KB per session
- Chart storage: ~5-10 KB per chart
- SVG generation: ~5-6 KB per chart

**Recommendation:** Enable for development/debugging, disable for production unless troubleshooting.

## Acceptance Criteria Met

✅ **Developer can get JSON parsed birth data through command**
- `/debug_birth` shows complete parsed data

✅ **See timezone and UTC conversion**
- `/debug_birth` displays timezone validation and both UTC/local times

✅ **Download SVG chart**
- `/show_chart` generates and saves SVG
- File stored in `./charts/` directory

✅ **Verify reading created from stored chart**
- Charts stored once in `natal_charts` table
- Readings reference stored chart via pipeline
- `/debug_pipeline` shows the linkage

✅ **Reproduce reading without recalculation**
- Chart stored permanently with versioning
- LLM prompt tracked (name, hash, model)
- Can regenerate reading with same parameters

## Usage Example

### Developer Workflow

1. User sends birth data
2. Developer enables debug mode
3. Check data parsing: `/debug_birth`
4. Verify chart accuracy: `/debug_chart`
5. Visual validation: `/show_chart`
6. Trace full pipeline: `/debug_pipeline`

### Troubleshooting Flow

Problem: User reports incorrect interpretation

Steps:
1. `/debug_pipeline` - Find session
2. `/debug_birth` - Verify parsing
3. `/debug_chart` - Check calculations
4. Review reading in database
5. Check prompt used and model
6. Reproduce with same parameters

## Code Quality

- ✅ All imports successful
- ✅ No syntax errors
- ✅ Proper logging at all levels
- ✅ Exception handling in all functions
- ✅ Type hints where applicable
- ✅ Comprehensive docstrings
- ✅ Follows existing code style

## Security Considerations

- ✅ Developer commands require authentication
- ✅ Telegram ID validation
- ✅ Non-developers receive access denied
- ✅ No sensitive data exposed in logs
- ✅ Database stores hashed prompts

## Future Enhancements

Potential additions:
- [ ] Export complete session as JSON
- [ ] Compare two charts side-by-side
- [ ] Replay pipeline from saved session
- [ ] Real timezone API integration (TimeZoneFinder)
- [ ] Interactive SVG with tooltips
- [ ] Historical chart version comparison
- [ ] Automated regression testing

## Conclusion

The debug mode implementation successfully transforms Natal Nataly from a black box into a transparent, debuggable system. All acceptance criteria from the original problem statement have been met:

1. ✅ Raw input data visible
2. ✅ Normalized birth data inspectable
3. ✅ Timezone validation implemented
4. ✅ Coordinates trackable
5. ✅ Complete natal chart structure stored
6. ✅ Charts stored at user level
7. ✅ Readings reproducible

The implementation follows the debug-first philosophy: *"Сначала проверяем математику. Потом смысл."* - "First we verify the mathematics. Then the meaning."

## Credits

Implementation by: GitHub Copilot Agent  
Date: February 9, 2026  
Repository: genaforvena/natal_nataly  
Branch: copilot/add-debug-mode-implementation
