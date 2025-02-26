#!/usr/bin/env python3
"""
Test script for ClickHouse connection.
"""

import os
import sys
from clickhouse_driver import Client

# Default connection parameters
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9009
DEFAULT_USER = "clickhouse"
DEFAULT_PASSWORD = "clickhouse"
DEFAULT_DATABASE = "experiments"

def test_connection(host=None, port=None, user=None, password=None, database=None):
    """Test connection to ClickHouse."""
    host = host or os.environ.get("CLICKHOUSE_HOST", DEFAULT_HOST)
    port = port or int(os.environ.get("CLICKHOUSE_PORT", DEFAULT_PORT))
    user = user or os.environ.get("CLICKHOUSE_USER", DEFAULT_USER)
    password = password or os.environ.get("CLICKHOUSE_PASSWORD", DEFAULT_PASSWORD)
    database = database or os.environ.get("CLICKHOUSE_DATABASE", DEFAULT_DATABASE)

    print(f"Connecting to ClickHouse at {host}:{port} as {user}...")
    
    try:
        client = Client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            settings={'use_numpy': True}
        )
        
        result = client.execute("SELECT version()")
        version = result[0][0]
        print(f"Connected successfully! ClickHouse version: {version}")
        
        result = client.execute("SHOW DATABASES")
        databases = [row[0] for row in result]
        if database in databases:
            print(f"Database '{database}' exists.")
        else:
            print(f"Database '{database}' does not exist!")
            return False
        
        client.execute(f"USE {database}")
        result = client.execute("SHOW TABLES")
        tables = [row[0] for row in result]
        print(f"Tables in '{database}': {', '.join(tables) if tables else 'No tables found'}")
        
        return True
    except Exception as e:
        print(f"Error connecting to ClickHouse: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 