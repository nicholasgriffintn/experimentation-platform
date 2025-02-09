#!/bin/bash
set -e

# Create hive database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-'EOSQL'
CREATE DATABASE hive;
EOSQL

# Set basic UTF8 encoding
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "hive" <<-'EOSQL'
ALTER DATABASE hive SET client_encoding TO 'UTF8';
EOSQL
