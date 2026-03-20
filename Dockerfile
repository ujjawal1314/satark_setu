# SatarkSetu - Docker Container
# Multi-stage build for optimized image size

# Stage 1: Base image with Python
FROM python:3.13-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Application
FROM dependencies as application

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Generate mock data (optional - can be mounted as volume)
RUN python data_generator.py

# Expose ports
# 8501 for Streamlit dashboard
# 8000 for FastAPI backend
EXPOSE 8501 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command (run dashboard)
CMD ["streamlit", "run", "dashboard_enhanced.py", "--server.address=0.0.0.0"]

# Alternative commands (uncomment as needed):
# Run backend: CMD ["python", "backend.py"]
# Run tests: CMD ["pytest", "tests/", "-v", "-m", "not slow"]
