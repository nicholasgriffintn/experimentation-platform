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

# Verify services
echo "Verifying services..."

# Check ClickHouse
echo "Checking ClickHouse..."
if curl -s -f http://localhost:8123/ping > /dev/null; then
    echo "✅ ClickHouse is running"
else
    echo "❌ ClickHouse is not responding"
fi

echo "Setup complete! Services are running."
echo "You can access:"
echo "- ClickHouse HTTP: http://localhost:8123"
echo "- ClickHouse UI: http://localhost:5521"
echo "Please start the frontend and api services separately with the command 'pnpm run dev'."