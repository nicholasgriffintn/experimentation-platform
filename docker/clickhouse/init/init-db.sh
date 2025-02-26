#!/bin/bash
set -e

until wget --no-verbose --tries=1 --spider http://localhost:8123/ping; do
  echo "Waiting for ClickHouse to be ready..."
  sleep 1
done

echo "ClickHouse is ready, initializing database..."

clickhouse-client --user=clickhouse --password=clickhouse -q "CREATE DATABASE IF NOT EXISTS experiments;"
clickhouse-client --user=clickhouse --password=clickhouse -q "GRANT ALL ON experiments.* TO clickhouse;"

echo "Database initialization completed successfully!" 