# Experimentation Platform

This is a new free, open source experimentation platform. The purpose is to provide a simple, easy to use, and extensible platform that makes experimentation easy for everyone.

> NOTE: This is mainly a side, personal project of mine. I am building this to learn more about the technologies, however, I do want it to be useful for others. Initially, this will be super basic and not very well put together. I will be building it over time.

## Development Setup

To get started, run the following script:

```bash
sh ./scripts/run.sh
```

This will setup the required services in the background. Once that's done, you can follow the instructions in each of the apps to get the platform running.

## Database Migrations

First you need to navigate to the API directory:

```bash
cd apps/api
```

Then, to create a new migration after modifying models:
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
