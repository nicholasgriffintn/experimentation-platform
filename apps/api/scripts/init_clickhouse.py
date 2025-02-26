#!/usr/bin/env python3
"""
Initialize ClickHouse database for the experimentation platform.

NOTE: This script is designed to be run in environments other than Docker.
"""

import os
import sys
from clickhouse_driver import Client

# Default connection parameters
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9000
DEFAULT_USER = "default"
DEFAULT_PASSWORD = ""
DEFAULT_DATABASE = "experiments"


def init_clickhouse():
    """Initialize ClickHouse database."""
    host = os.environ.get("CLICKHOUSE_HOST", DEFAULT_HOST)
    port = int(os.environ.get("CLICKHOUSE_PORT", DEFAULT_PORT))
    user = os.environ.get("CLICKHOUSE_USER", DEFAULT_USER)
    password = os.environ.get("CLICKHOUSE_PASSWORD", DEFAULT_PASSWORD)
    database = os.environ.get("CLICKHOUSE_DATABASE", DEFAULT_DATABASE)

    print(f"Connecting to ClickHouse at {host}:{port} as {user}...")
    
    try:
        client = Client(
            host=host,
            port=port,
            user=user,
            password=password,
            settings={'use_numpy': True}
        )
        
        # Create database if it doesn't exist
        client.execute("CREATE DATABASE IF NOT EXISTS experiments")
        print("Created database 'experiments'")
        
        # Create user if it doesn't exist
        client.execute("CREATE USER IF NOT EXISTS clickhouse IDENTIFIED BY 'clickhouse'")
        print("Created user 'clickhouse'")
        
        # Grant permissions
        client.execute("GRANT ALL ON experiments.* TO clickhouse")
        print("Granted permissions to user 'clickhouse'")
        
        # Switch to experiments database
        client.execute("USE experiments")
        
        print("ClickHouse initialization completed successfully!")
        return True
    except Exception as e:
        print(f"Error initializing ClickHouse: {str(e)}")
        return False


if __name__ == "__main__":
    success = init_clickhouse()
    sys.exit(0 if success else 1) 