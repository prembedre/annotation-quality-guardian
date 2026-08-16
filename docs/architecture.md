# 🏗️ Architecture — Annotation Quality Guardian

## System Overview

AQG is a modular platform for monitoring data annotation quality. It follows a layered architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend                      │
│              (Dashboard & Reports)                   │
└──────────────────────┬──────────────────────────────┘
                       │  REST API (JSON)
┌──────────────────────▼──────────────────────────────┐
│                 FastAPI Backend                       │
│          (Routes, Auth, Orchestration)                │
└───────┬──────────────────────────────┬──────────────┘
        │                              │
┌───────▼──────────┐         ┌────────▼─────────────┐
│   PostgreSQL DB  │         │   Scoring Engine      │
│  (Data Storage)  │         │  (Quality Metrics)    │
└──────────────────┘         └───────────────────────┘
```

## Component Details

### Frontend (React + Vite)
- **Owner:** Member 4
- **Tech:** React 18, Vite, Axios
- Single-page app with dashboard views for projects, annotators, and quality scores.

### Backend (FastAPI)
- **Owner:** Member 1
- **Tech:** FastAPI, Pydantic, SQLAlchemy (async), asyncpg
- Exposes RESTful endpoints for CRUD operations and score computation triggers.

### Database (PostgreSQL)
- **Owner:** Member 2
- **Tech:** PostgreSQL 15+
- Stores projects, annotators, items, annotations, and computed scores.

### Scoring Engine (Python)
- **Owner:** Member 3
- **Tech:** NumPy, SciPy, scikit-learn
- Four scoring dimensions:
  1. **Gold-standard validation** — accuracy against known answers
  2. **Inter-annotator agreement** — Cohen's κ (2 raters), Fleiss' κ (3+ raters)
  3. **Behavioral anomalies** — speed outliers, repetitive patterns *(planned)*
  4. **Embedding outliers** — semantic drift detection *(planned)*

## Data Flow

1. Annotations are submitted via the frontend or bulk-uploaded via API.
2. Backend validates and persists annotations to PostgreSQL.
3. Score computation is triggered (manually or on schedule).
4. Scoring engine reads annotations, computes metrics, and writes results.
5. Frontend fetches and visualizes quality dashboards.

## API Conventions

- **Base URL:** `http://localhost:8000/api`
- **Format:** JSON
- **Auth:** JWT (planned)
- **Versioning:** URL prefix (`/api/v1/...`) when v2 is introduced
