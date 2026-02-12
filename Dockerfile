# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for pyswisseph and postgresql
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create ephemeris directory required by pyswisseph
RUN mkdir -p ephe

# Create data directory for persistent database
RUN mkdir -p data

# Copy application code
COPY src ./src
COPY scripts ./scripts
COPY tests ./tests

# Copy Alembic migration files
COPY alembic ./alembic
COPY alembic.ini .

# Copy entrypoint script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Set environment variable for database path (fallback for SQLite)
ENV DB_PATH=/app/data/natal_nataly.sqlite

# Default port (can be overridden by environment variable)
ENV PORT=8000

# Expose common ports (8000 for local, 10000 for Render)
EXPOSE 8000 10000

# Add src to PYTHONPATH so imports work correctly
ENV PYTHONPATH=/app

# Use entrypoint script that runs migrations before starting the app
ENTRYPOINT ["./docker-entrypoint.sh"]
