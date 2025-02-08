# Experimentation Platform API

This is the API service for the experimentation platform. It provides endpoints for managing experiments, metrics, and feature definitions.

## Development Setup

1. Start the infrastructure services from the root directory:
```bash
cd ../..  # Go to root directory
./scripts/run.sh
```

2. Create a virtual environment:
```bash
cd apps/api  # Return to API directory
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your desired settings
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Run the development server:
```bash
uvicorn src.main:app --reload
```

The API will be available at http://localhost:8000

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
