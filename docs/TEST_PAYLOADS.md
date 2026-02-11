# Test Payload for Telegram Webhook

This file contains sample Telegram webhook payloads for testing the bot without needing actual Telegram messages.

## Testing with curl

### Valid Birth Data

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": 123456789},
      "from": {"id": 987654321},
      "text": "DOB: 1990-05-15\nTime: 14:30\nLat: 40.7128\nLng: -74.0060"
    }
  }'
```

### Invalid Format (should trigger error message)

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": 123456789},
      "from": {"id": 987654321},
      "text": "Tell me my horoscope"
    }
  }'
```

## Python Test Script

```python
#!/usr/bin/env python3
import asyncio
import httpx

async def test_webhook():
    # Valid birth data
    payload = {
        "message": {
            "chat": {"id": 123456789},
            "from": {"id": 987654321},
            "text": """DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060"""
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/webhook",
            json=payload
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

asyncio.run(test_webhook())
```

## Sample Test Cases

### 1. New York, USA
```
DOB: 1990-05-15
Time: 14:30
Lat: 40.7128
Lng: -74.0060
```

### 2. London, UK
```
DOB: 1985-12-25
Time: 08:00
Lat: 51.5074
Lng: -0.1278
```

### 3. Tokyo, Japan
```
DOB: 1992-03-20
Time: 18:45
Lat: 35.6762
Lng: 139.6503
```

### 4. Sydney, Australia
```
DOB: 1988-07-10
Time: 12:00
Lat: -33.8688
Lng: 151.2093
```

### 5. Mumbai, India
```
DOB: 1995-11-05
Time: 06:30
Lat: 19.0760
Lng: 72.8777
```
