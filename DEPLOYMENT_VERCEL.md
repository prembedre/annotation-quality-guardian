# Vercel Deployment & Hosted Database Guide

This repository is configured as a multi-service Vercel deployment:

- **frontend** — React + Vite SPA from `frontend/`
- **backend** — FastAPI backend from `backend/`, entrypoint `main:app`

The public rewrite table in `vercel.json` routes `/api/*`, `/auth/*`, and `/health` to FastAPI; all SPA routes are routed to Vite.

---

## 1. Production Database Architecture

Production deployments **must** use a persistent hosted PostgreSQL database (such as **Neon**, **Supabase**, or **AWS RDS**).

> **Critical Note on Ephemeral SQLite**:
> Serverless platforms like Vercel instantiate ephemeral Lambda environments where `/tmp` is wiped between cold starts and instances do not share local filesystem state. SQLite fallback is disabled in production to protect data integrity and avoid silent data loss.

---

## 2. Setting Up Hosted PostgreSQL (Neon / Supabase)

### Option A: Neon Serverless PostgreSQL (Recommended)
1. Go to [https://neon.tech](https://neon.tech) and create a free project named `aqg-production`.
2. Neon provides a pooled connection URI formatted as:
   ```text
   postgresql://<user>:<password>@ep-<project-name>-pooler.<region>.aws.neon.tech/neondb?sslmode=require
   ```
3. Copy the connection string.

### Option B: Supabase Managed PostgreSQL
1. Go to [https://supabase.com](https://supabase.com) and create a project.
2. In Project Settings -> Database -> Connection string, select **URI** (or Transaction Pooler on port 6543):
   ```text
   postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require
   ```
3. If Supabase provides a string starting with `postgres://`, AQG automatically normalizes it to `postgresql://`.

---

## 3. Configuring Vercel Environment Variables

In your Vercel Dashboard -> Project Settings -> **Environment Variables**, set:

| Variable | Value | Notes |
|---|---|---|
| `ENV` | `production` | Enables production safeguards |
| `DEBUG` | `false` | Disables debug logs and API docs |
| `SECRET_KEY` | *(generate via `python -c "import secrets; print(secrets.token_urlsafe(32))"`)* | Never commit secrets to Git |
| `DATABASE_URL` | `postgresql://...` | Hosted PostgreSQL URI with `sslmode=require` |
| `CORS_ORIGINS` | `https://annotation-quality-guardian-jfrfhejmc-aqg1.vercel.app` | Comma-separated allowed origins |

---

## 4. Migrating Local Data (SQLite to Hosted PostgreSQL)

To push existing localhost data (Project 1, 4 annotators, items, 40 annotations, trust scores, users, and rules) from `aqg_dev.db` into the hosted PostgreSQL database, run:

```bash
# Direct command with your remote DATABASE_URL:
python scripts/migrate_sqlite_to_postgres.py --sqlite-path aqg_dev.db --postgres-url "postgresql://<user>:<password>@<host>/<dbname>?sslmode=require"
```

Or set the environment variable:
```bash
export DATABASE_URL="postgresql://<user>:<password>@<host>/<dbname>?sslmode=require"
python scripts/migrate_sqlite_to_postgres.py
```

### Dry Run Validation
To preview table records without committing writes:
```bash
python scripts/migrate_sqlite_to_postgres.py --dry-run --postgres-url "postgresql://..."
```

---

## 5. Deployment Smoke-Test Checklist

- [ ] `/health` returns HTTP 200 with `"database": "connected"` and `"database_type": "postgresql"`.
- [ ] `/auth/login` successfully issues a JWT token.
- [ ] `/api/projects` returns `[{"id": 1, "name": "Project 1", ...}]`.
- [ ] Active project restores in sidebar and topbar (`Project 1 • Default`).
- [ ] Annotator Leaderboard displays 4 active annotators (Prem, Rahul, Sidharth, Venkatesh).
- [ ] Peak Trust Score displays `96.4%`.
- [ ] Quality & Agreement Trend displays historical telemetry.
- [ ] Data persists across browser refresh and subsequent serverless cold starts.
