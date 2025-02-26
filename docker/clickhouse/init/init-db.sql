-- Create experiments database
CREATE DATABASE IF NOT EXISTS experiments;

-- Create a user for the API
CREATE USER IF NOT EXISTS clickhouse IDENTIFIED BY 'clickhouse';

-- Grant permissions to the user
GRANT ALL ON experiments.* TO clickhouse;
