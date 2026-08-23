# Alembic Migrations

This directory contains the Alembic migration environment for SecureOps.

Run Alembic from the `secureops/` project directory:

```bash
alembic -c alembic.ini current
alembic -c alembic.ini revision --autogenerate -m "initial secureops schema"
alembic -c alembic.ini upgrade head
```

The database URL is loaded from `app.config.settings.database_url`, so local
commands use the same `DATABASE_URL` configuration as the application.

