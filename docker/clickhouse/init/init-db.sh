#!/bin/bash
set -e

until wget --no-verbose --tries=1 --spider http://localhost:8123/ping; do
  echo "Waiting for ClickHouse to be ready..."
  sleep 1
done

echo "ClickHouse is ready, initializing database..."

clickhouse-client --user=clickhouse --password=clickhouse -q "CREATE DATABASE IF NOT EXISTS experiments;"

clickhouse-client --user=clickhouse --password=clickhouse -q "CREATE TABLE IF NOT EXISTS experiments.events (
    event_id String,
    experiment_id String,
    timestamp DateTime64(3),
    user_id String,
    variant_id String,
    event_type String,
    event_value Nullable(Float64),
    client_id Nullable(String),
    metadata Map(String, String)
) ENGINE = MergeTree()
PARTITION BY (experiment_id, toYYYYMMDD(timestamp))
ORDER BY (experiment_id, timestamp, user_id);"

clickhouse-client --user=clickhouse --password=clickhouse -q "CREATE TABLE IF NOT EXISTS experiments.metrics (
    metric_id String,
    experiment_id String,
    timestamp DateTime64(3),
    user_id String,
    variant_id String,
    metric_name String,
    metric_value Float64,
    client_id Nullable(String),
    metadata Map(String, String)
) ENGINE = MergeTree()
PARTITION BY (experiment_id, toYYYYMMDD(timestamp))
ORDER BY (experiment_id, timestamp, user_id);"

clickhouse-client --user=clickhouse --password=clickhouse -q "CREATE TABLE IF NOT EXISTS experiments.assignments (
    assignment_id String,
    experiment_id String,
    timestamp DateTime64(3),
    user_id String,
    variant_id String,
    context Map(String, String)
) ENGINE = MergeTree()
PARTITION BY (experiment_id, toYYYYMMDD(timestamp))
ORDER BY (experiment_id, timestamp, user_id);"

clickhouse-client --user=clickhouse --password=clickhouse -q "CREATE TABLE IF NOT EXISTS experiments.results (
    result_id String,
    experiment_id String,
    timestamp DateTime64(3),
    user_id String,
    variant_id String,
    result_value Float64,
    client_id Nullable(String),
    metadata Map(String, String)
) ENGINE = MergeTree()
PARTITION BY (experiment_id, toYYYYMMDD(timestamp))
ORDER BY (experiment_id, timestamp, user_id);"

echo "Database initialization completed successfully!" 