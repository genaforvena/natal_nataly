#!/bin/bash
# Comprehensive Docker deployment testing script
# This script validates that the Docker image is built correctly and can run properly

set -e  # Exit on any error

echo "=========================================="
echo "Docker Deployment Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build the image
echo "Building Docker image..."
docker build -t natal-nataly:test . > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Docker image built successfully"
echo ""

# Test 1: Module imports
echo "Test 1: Checking module imports..."
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=test_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test_key \
  natal-nataly:test python -c "from src import main; print('Import successful')" > /dev/null
echo -e "${GREEN}✓${NC} Basic module import works"

# Test 2: FastAPI app initialization
echo "Test 2: Checking FastAPI app initialization..."
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=test_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test_key \
  natal-nataly:test python -c "from src.main import app; print('FastAPI initialized')" > /dev/null
echo -e "${GREEN}✓${NC} FastAPI app initializes correctly"

# Test 3: All critical modules
echo "Test 3: Checking all critical module imports..."
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=test_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test_key \
  natal-nataly:test python -c "
from src.bot import handle_telegram_update
from src.db import init_db
from src.models import User
from src.llm import call_llm
from src.services.chart_builder import build_natal_chart_text_and_json
print('All modules imported')
" > /dev/null
echo -e "${GREEN}✓${NC} All critical modules import successfully"

# Test 4: Directory structure
echo "Test 4: Verifying container directory structure..."
STRUCTURE_CHECK=$(docker run --rm natal-nataly:test sh -c "
  [ -d /app/src ] && [ -d /app/scripts ] && [ -d /app/tests ] && \
  [ -f /app/src/main.py ] && [ -f /app/src/bot.py ] && \
  echo 'OK' || echo 'FAIL'
")

if [ "$STRUCTURE_CHECK" = "OK" ]; then
  echo -e "${GREEN}✓${NC} Directory structure is correct"
else
  echo -e "${RED}✗${NC} Directory structure verification failed"
  exit 1
fi

# Test 5: PYTHONPATH is set correctly
echo "Test 5: Checking PYTHONPATH configuration..."
PYTHONPATH_CHECK=$(docker run --rm natal-nataly:test sh -c "
  echo \$PYTHONPATH | grep -q '/app' && echo 'OK' || echo 'FAIL'
")

if [ "$PYTHONPATH_CHECK" = "OK" ]; then
  echo -e "${GREEN}✓${NC} PYTHONPATH is configured correctly"
else
  echo -e "${RED}✗${NC} PYTHONPATH configuration failed"
  exit 1
fi

# Test 6: Server startup and health check
echo "Test 6: Testing server startup and health endpoint..."

# Start container
CONTAINER_ID=$(docker run --rm -d \
  --name natal-nataly-test-$$ \
  -e TELEGRAM_BOT_TOKEN=test_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test_key \
  -p 8002:8000 \
  natal-nataly:test)

# Wait for server to start
echo "  Waiting for server to start..."
sleep 8

# Check health endpoint
if curl -f -s http://localhost:8002/health | grep -q "ok"; then
  echo -e "${GREEN}✓${NC} Server started and health check passed"
else
  echo -e "${RED}✗${NC} Server health check failed"
  echo "Container logs:"
  docker logs natal-nataly-test-$$
  docker stop natal-nataly-test-$$ > /dev/null 2>&1
  exit 1
fi

# Check server logs for errors
LOGS=$(docker logs natal-nataly-test-$$ 2>&1)
if echo "$LOGS" | grep -qi "error\|exception\|traceback" | grep -v "TELEGRAM_BOT_TOKEN environment variable is not set"; then
  echo -e "${YELLOW}⚠${NC}  Warning: Found potential errors in logs"
  echo "$LOGS" | grep -i "error\|exception" | head -5
fi

# Stop the container
docker stop natal-nataly-test-$$ > /dev/null 2>&1

# Test 7: Database initialization
echo "Test 7: Testing database initialization..."
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=test_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test_key \
  natal-nataly:test python -c "
from src.db import init_db
init_db()
print('Database initialized')
" > /dev/null
echo -e "${GREEN}✓${NC} Database initialization works"

# Test 8: Check uvicorn command
echo "Test 8: Verifying uvicorn startup command..."
CMD_CHECK=$(docker inspect natal-nataly:test | grep -o "uvicorn src.main:app" || echo "FAIL")

if [ "$CMD_CHECK" != "FAIL" ]; then
  echo -e "${GREEN}✓${NC} Uvicorn command is correct (src.main:app)"
else
  echo -e "${RED}✗${NC} Uvicorn command verification failed"
  exit 1
fi

# Test 9: Environment variables
echo "Test 9: Testing environment variable handling..."
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=custom_token \
  -e LLM_PROVIDER=deepseek \
  -e DEEPSEEK_API_KEY=test_key \
  -e PORT=9000 \
  natal-nataly:test python -c "
import os
assert os.getenv('TELEGRAM_BOT_TOKEN') == 'custom_token'
assert os.getenv('LLM_PROVIDER') == 'deepseek'
assert os.getenv('PORT') == '9000'
print('Environment variables OK')
" > /dev/null
echo -e "${GREEN}✓${NC} Environment variables are handled correctly"

echo ""
echo "=========================================="
echo -e "${GREEN}All Docker tests passed!${NC} ✓"
echo "=========================================="
echo ""
echo "The Docker image is ready for deployment with:"
echo "  • Correct directory structure (src/, scripts/, tests/)"
echo "  • Proper PYTHONPATH configuration"
echo "  • Working module imports"
echo "  • Functional server startup"
echo "  • Health endpoint responding"
echo ""
