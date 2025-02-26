#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
if ! command_exists wget; then
    echo "wget is required but not installed. Please install wget first."
    exit 1
fi

if ! command_exists docker; then
    echo "docker is required but not installed. Please install docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "docker-compose is required but not installed. Please install docker-compose first."
    exit 1
fi

# Run setup script
echo "Running setup script..."
chmod +x scripts/setup.sh
./scripts/setup.sh

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Initialize database
echo "Initializing database..."
docker-compose exec -T api alembic upgrade head

# Verify services
echo "Verifying services..."

# Check ClickHouse
echo "Checking ClickHouse..."
if curl -s -f http://localhost:8123/ping > /dev/null; then
    echo "✅ ClickHouse is running"
else
    echo "❌ ClickHouse is not responding"
fi

# Check Spark
echo "Checking Spark..."
if curl -s -f http://localhost:8080 > /dev/null; then
    echo "✅ Spark is running"
else
    echo "❌ Spark is not responding"
fi

# Check MinIO
echo "Checking MinIO..."
if curl -s -f http://localhost:9000/minio/health/live > /dev/null; then
    echo "✅ MinIO is running"
else
    echo "❌ MinIO is not responding"
fi

echo "Setup complete! Services are running."
echo "You can access:"
echo "- API: http://localhost:8000"
echo "- MinIO Console: http://localhost:9001"
echo "- Spark UI: http://localhost:8080"
echo "- ClickHouse HTTP: http://localhost:8123"
echo "Please start the frontend and api services separately with the command 'pnpm run dev'."