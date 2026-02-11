# Docker Testing Guide

This guide covers testing the Docker deployment to ensure it works correctly with the reorganized project structure.

## Quick Test

The CI/CD pipeline automatically runs comprehensive Docker tests on every push. The tests verify:

1. ✅ Module imports work correctly
2. ✅ FastAPI app initializes
3. ✅ All critical modules are accessible
4. ✅ Directory structure is correct
5. ✅ Server can start and respond to health checks

## Manual Testing

### Quick Manual Test

```bash
# Build the image
docker build -t natal-nataly:test .

# Test basic import
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=test_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test_key \
  natal-nataly:test python -c "from src import main; print('✓ Import works')"

# Test server startup
docker run --rm -d --name test-server \
  -e TELEGRAM_BOT_TOKEN=test_token \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test_key \
  -p 8001:8000 \
  natal-nataly:test

# Wait a few seconds for startup
sleep 5

# Check health endpoint
curl http://localhost:8001/health

# Stop the test server
docker stop test-server
```

### Comprehensive Test Suite

Run the comprehensive test script that validates all aspects of the Docker deployment:

```bash
./scripts/test_docker.sh
```

This script performs 9 different tests:

1. **Module Imports** - Verifies basic Python imports work
2. **FastAPI Initialization** - Ensures FastAPI app can be created
3. **Critical Modules** - Tests all core application modules
4. **Directory Structure** - Validates file organization in container
5. **PYTHONPATH** - Confirms environment variable is set correctly
6. **Server Startup** - Tests the application can start and serve requests
7. **Database Init** - Verifies database initialization works
8. **Uvicorn Command** - Checks the startup command is correct
9. **Environment Variables** - Tests variable handling

### Expected Output

If all tests pass, you'll see:

```
==========================================
All Docker tests passed! ✓
==========================================

The Docker image is ready for deployment with:
  • Correct directory structure (src/, scripts/, tests/)
  • Proper PYTHONPATH configuration
  • Working module imports
  • Functional server startup
  • Health endpoint responding
```

## CI/CD Pipeline Tests

The GitHub Actions workflow (`.github/workflows/ci.yml`) includes a `docker-build` job that runs comprehensive tests automatically:

### Tests Performed in CI

1. **Import Test** - Verifies `from src import main` works
2. **App Initialization** - Checks `from src.main import app` succeeds
3. **All Critical Modules** - Tests importing bot, db, models, llm, services
4. **Directory Structure** - Validates container file organization
5. **Server Health Check** - Starts container and hits `/health` endpoint

### Viewing CI Test Results

1. Go to the GitHub repository
2. Click on "Actions" tab
3. Select the latest workflow run
4. Click on "Docker Build Check" job
5. Review the test output

## Common Issues and Solutions

### Issue: Import errors in container

**Symptom:** `ModuleNotFoundError: No module named 'src'`

**Solution:** Ensure `PYTHONPATH=/app` is set in the Dockerfile (line 42)

### Issue: Server won't start

**Symptom:** Container exits immediately or health check fails

**Solutions:**
- Check environment variables are set correctly
- Review container logs: `docker logs <container-name>`
- Verify `CMD uvicorn src.main:app` is correct in Dockerfile

### Issue: Files not found in container

**Symptom:** `FileNotFoundError` for Python modules or templates

**Solution:** Verify the COPY commands in Dockerfile include all necessary directories:
```dockerfile
COPY src ./src
COPY scripts ./scripts
COPY tests ./tests
```

## Deployment Verification

### Local Deployment Test

```bash
# Use docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8000/health

# Stop
docker-compose down
```

### Production Deployment (Render.com)

After deploying to Render:

1. Check the deployment logs in Render dashboard
2. Look for "Database initialized" and "Application startup complete" messages
3. Test the webhook endpoint (requires Telegram bot token)
4. Verify environment variables are set correctly in Render dashboard

## Key Files

- **Dockerfile** - Main Docker image definition
- **docker-compose.yml** - Local development setup
- **.github/workflows/ci.yml** - CI/CD pipeline configuration
- **scripts/test_docker.sh** - Comprehensive test script
- **start.sh** - Local development startup script

## Docker Build Context

The reorganized structure requires these files to be in the Docker build context:

```
natal_nataly/
├── src/              # Application code (REQUIRED)
├── scripts/          # Utility scripts (REQUIRED)
├── tests/            # Test suite (REQUIRED for CI)
├── requirements.txt  # Python dependencies (REQUIRED)
├── Dockerfile        # Docker image definition
└── docker-compose.yml
```

All paths are relative to the repository root.

## Environment Variables

Required for Docker deployment:

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `LLM_PROVIDER` - Either "groq" or "deepseek"
- `GROQ_API_KEY` or `DEEPSEEK_API_KEY` - Corresponding API key

Optional:

- `PORT` - Server port (default: 8000)
- `DATABASE_URL` - Database connection string (defaults to SQLite)
- `DEBUG_MODE` - Enable debug features (default: false)
- `DEVELOPER_TELEGRAM_ID` - For debug commands

## Troubleshooting

### Build Fails

```bash
# Clean build without cache
docker build --no-cache -t natal-nataly:test .

# Check for syntax errors in Dockerfile
docker build --check -t natal-nataly:test .
```

### Container Crashes

```bash
# Run with interactive shell to debug
docker run -it --rm \
  -e TELEGRAM_BOT_TOKEN=test \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=test \
  natal-nataly:test /bin/bash

# Inside container, test imports manually
python -c "from src.main import app; print('OK')"
```

### Port Conflicts

```bash
# Use a different port
docker run -p 8002:8000 natal-nataly:test

# Find containers using port 8000
docker ps | grep 8000
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Project Structure Guide](../PROJECT_STRUCTURE.md)
- [Deployment Guide](../deployment/DOCKER.md)
