# API

This folder contains the FastAPI application for the Néovolt grid platform.

## Setup

1. Install dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```

2. Ensure `.env` exists in the repository root and contains PostgreSQL credentials:
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_DB`

## Run

```bash
uvicorn api.main:app --reload
```

## Run in Docker

To launch the API container after the database is ready, run:

```bash
docker compose up --build --force-recreate api
```

## Endpoints

- `GET /` - API status check
- `GET /health/db` - PostgreSQL connectivity health check
