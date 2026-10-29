# Vercel deployment guide

This repository is configured as one Vercel project with two independently built services:

- **frontend** — React + Vite from `frontend/`
- **backend** — FastAPI from `backend/`, entered at `app.main:app`

The public rewrite table sends `/api/*`, `/auth/*`, and `/health` to FastAPI; all other paths go to the frontend SPA. The frontend already calls same-origin `/api` and `/auth` paths, so a service binding is not needed for browser-to-API requests. Do not change these calls to a deployment-specific hostname.

> Vercel Services may require the project to have the Services framework enabled. In Vercel, import this repository and select **Services** as the project framework. Keep the project root at the repository root so Vercel can read the root `vercel.json`.

## Before production traffic

1. **Keep the existing database intact.** Use a managed PostgreSQL database and take a backup/snapshot before applying any schema changes. Do not point production at a local SQLite file or the development Docker database.
2. **Set backend environment variables** for Production (and separately for Preview if you intend to test there):
   - `ENV=production`
   - `DEBUG=false`
   - `SECRET_KEY` — a long, unique, randomly generated secret; never commit it
   - `DATABASE_URL` — managed PostgreSQL connection string, including SSL options required by the provider
   - `REDIS_URL` — managed Redis URL reachable from the backend
   - `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` — set to the worker's shared Redis/broker endpoints if different from `REDIS_URL`
   - `CORS_ORIGINS` — the exact public frontend origin(s), comma-separated; do not use `*` for authenticated production traffic
3. Use a provider-supported connection pool or conservative database connection limits. Serverless instances can scale horizontally, so avoid assuming a single long-lived process.
4. Apply the project's reviewed database migrations using the migration workflow your team normally uses. **Do not rely on application startup to create or migrate production tables.** Verify the migration against a backup/staging copy first.
5. Deploy a Preview and verify the checks below before promoting it to production.

## Background jobs: separate runtime required

The API submits jobs through Celery (`task.delay()`) and reads their results from the Celery backend. Vercel request handlers do not run a persistent Celery worker. Run the existing worker command on a separate persistent worker host using the same code version, PostgreSQL database, and Redis/broker configuration:

```sh
celery -A app.celery_app.celery_app worker -l info
```

The worker needs the backend's Python dependencies and import path (the repository's `backend/` working directory). Configure `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` consistently on the worker and API. Do not assume asynchronous job endpoints work until a worker is running and tested. Do not set eager mode as a substitute without testing job status/result persistence.

## Smoke-test checklist

- [ ] `/` serves the frontend and client-side routes load on refresh.
- [ ] `/health` returns HTTP 200 and reports the database as connected.
- [ ] A known `/api/...` endpoint reaches FastAPI (not the SPA fallback).
- [ ] Login and an authenticated API request work over HTTPS.
- [ ] CORS allows only the expected frontend origin(s).
- [ ] A background job can be queued, processed by the external worker, and queried for its final result.
- [ ] Database writes persist across new requests and a backup/restore procedure is documented.
- [ ] Production secrets are stored in Vercel/provider environment settings, not in Git.

## Rollback and data safety

A Vercel deployment rollback restores application code/routing, **not** database contents or schema. Back up the database before migrations, prefer backward-compatible migrations, and retain the previous working deployment. Never run destructive data/schema changes as part of an unverified deployment.

## Known limitation

This configuration prepares the repository for Vercel's multi-service build; it does not itself create provider accounts, provision PostgreSQL/Redis, start the external Celery worker, set secrets, or verify a live deployment. Heavy scientific Python dependencies may also hit runtime/build limits; verify a real Preview build and function startup before sending production traffic.
