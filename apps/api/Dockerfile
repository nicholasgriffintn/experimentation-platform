FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
COPY README.md .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Run migrations and start the application
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload 