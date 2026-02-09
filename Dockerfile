# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for pyswisseph
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
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
COPY *.py .

# Set environment variable for database path
ENV DB_PATH=/app/data/natal_nataly.sqlite

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
