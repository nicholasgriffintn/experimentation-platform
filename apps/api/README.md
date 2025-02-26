# Experimentation Platform API

This is the API service for the experimentation platform. It provides endpoints for managing experiments, metrics, and features.

## Architecture

The API uses the following technologies:

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Relational database for metadata, experiment configuration, and application state
- **ClickHouse**: High-performance columnar database for raw experimental data and analytics
- **Redis**: In-memory data store for caching and real-time operations

## Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose

### Installation

1. Clone the repository
2. Setup the docker environment:

```bash
cd ../..  # Go to root directory
sh ./scripts/run.sh
```

3. Navigate to the API directory:

```bash
cd apps/api
```

4. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

5. Install dependencies:

```bash
pip install -e .
```

6. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your desired settings
```


7. Apply database migrations:

```bash
alembic upgrade head
```

8. Run the API:

```bash
uvicorn src.main:app --reload
```

The API will be available at http://localhost:8000.

## Database Migrations

To create a new migration after modifying models:
```bash
alembic revision --autogenerate -m "description of changes"
```

To apply migrations:
```bash
alembic upgrade head
```

To rollback migrations:
```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

## ClickHouse Management

The API uses ClickHouse for storing and analyzing experimental data. You can interact with ClickHouse directly using the ClickHouse client:

```bash
docker exec -it clickhouse-server clickhouse-client
```

Common ClickHouse commands:

```sql
-- Show databases
SHOW DATABASES;

-- Use experiments database
USE experiments;

-- Show tables
SHOW TABLES;

-- Describe table structure
DESCRIBE TABLE experiments.<experiment_id>_events;

-- Query data
SELECT * FROM experiments.<experiment_id>_events LIMIT 10;
```

## API Documentation

When the API is running, you can access the interactive documentation at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
