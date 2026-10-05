# 🛡️ Annotation Quality Guardian (AQG)

**Automated annotation quality control and auditing system for monitoring, scoring, and improving labeled datasets.**

AQG combines gold-standard validation, inter-annotator agreement metrics, behavioral anomaly detection, and embedding-based outlier analysis to help teams maintain reliable annotation quality.

## ✨ Features

- FastAPI backend with interactive Swagger documentation
- React and Vite dashboard frontend
- PostgreSQL persistence with SQLAlchemy and Alembic migrations
- Redis integration for caching and background processing
- Annotation, project, scoring, review, ingestion, export, and dashboard APIs
- Quality scoring based on agreement, gold checks, trust signals, and anomalies
- Docker Compose setup for local full-stack development

## 📁 Project Structure

```text
annotation-quality-guardian/
├── backend/               # FastAPI application and API services
├── frontend/              # React/Vite dashboard
├── database/              # PostgreSQL schema and sample data
├── scoring/               # Quality scoring engine
├── data/                  # Shared sample datasets
├── docs/                  # Architecture and workflow documentation
├── tests/                 # Backend and scoring tests
├── docker-compose.yml     # Production full stack (FastAPI, Nginx, PostgreSQL, Redis, Celery)
├── docker-compose.dev.yml # Live development override (Vite HMR & Uvicorn reload)
├── Makefile               # CLI shortcuts for Docker operations
├── .env.example           # Configuration template
└── README.md
```

## 🐳 Docker Usage & Architecture

AQG provides fully containerized configurations for both production-ready deployments and live hot-reloading development workflows.

### 🌟 Key Container Architecture Highlights
- **Multi-Stage Frontend Build**: Static React SPA built with Node 20 and served via an ultra-lightweight Nginx Alpine proxy with gzip compression and client-side routing.
- **Hardened Backend**: Python 3.11-slim container running as a dedicated non-root user (`appuser`, UID 10001) with multi-package pythonpath (`backend` + `scoring`).
- **Self-Healing Entrypoint**: The backend automatically waits for PostgreSQL readiness, runs Alembic migrations (`alembic upgrade head`), and optionally seeds demo data.
- **Asynchronous Task Workers**: Celery background worker container connected to Redis for compute-intensive scoring jobs.
- **Built-in Healthchecks**: Native healthchecks on all services (`pg_isready`, `redis-cli ping`, Python urllib on `/health`, and Nginx ping).

---

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) or Docker Engine + Docker Compose v2 (Linux)
- Git

### 2. Environment Setup
Create your local environment file from the template:
```bash
cp .env.example .env
```
*(Optionally adjust port mappings, credentials, or generate a production `SECRET_KEY`.)*

### 3. Production Stack (Recommended)
Start the complete stack (PostgreSQL, Redis, Backend API, Celery Worker, and Frontend Nginx proxy):

```bash
docker compose up --build -d
```

Check the health status of all containers:
```bash
docker compose ps
```

The services will be available at:
| Service | URL | Description |
|---|---|---|
| **Frontend Application** | [http://localhost](http://localhost) (port 80) | Nginx reverse proxy & React SPA |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI REST service |
| **Interactive Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI documentation |
| **ReDoc API Docs** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative API documentation |
| **PostgreSQL** | `localhost:5432` | Relational storage |
| **Redis** | `localhost:6379` | Cache & Celery broker |

### 4. Development Stack (Live Code Hot-Reloading)
To develop locally with bind mounts and instant hot-reloading for both React (Vite HMR) and FastAPI (Uvicorn `--reload`):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```
In development mode, the Vite dev server runs at [http://localhost:5173](http://localhost:5173).

### 5. Running Tests Inside Docker
Execute the full pytest suite inside the isolated backend container environment:
```bash
docker compose exec backend pytest
```

### 6. Seeding Demo Data
To re-seed or manually trigger demo data population inside the container:
```bash
docker compose exec backend python -m app.core.seed_demo_data
```

### 7. Viewing Logs
Stream real-time logs from all or specific services:
```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Celery worker only
docker compose logs -f celery_worker
```

### 8. Stopping and Teardown
Stop all containers:
```bash
docker compose down
```

Stop containers and purge named database/cache volumes:
```bash
docker compose down -v
```

### 9. Troubleshooting
- **Port Conflict on 80 or 8000**: Change `FRONTEND_PORT` or `BACKEND_PORT` in `.env`.
- **Database Connection Retries**: The backend container automatically retries up to 45 seconds while waiting for PostgreSQL initialization.
- **Windows LF Endings**: Ensure `backend/entrypoint.sh` maintains Unix LF line endings.

## 🛠️ Manual Development Setup

### Backend

```bash
cd backend
python -m venv venv

# Windows (Command Prompt or PowerShell)
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### Database (PostgreSQL)

From the project root directory:

```bash
psql -U postgres -c "CREATE DATABASE aqg_db;"
psql -U postgres -d aqg_db -f database/schema.sql
psql -U postgres -d aqg_db -f database/sample_data.sql
```

*(Alternatively, to run with SQLite for rapid local prototyping without PostgreSQL, leave `DATABASE_URL=sqlite:///./aqg_dev.db` in `backend/.env` and run `python seed_demo_data.py`).*

### Frontend

From the project root directory:

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## 🧪 Testing

Run backend and scoring tests from the project root:

```bash
pytest tests/backend/
pytest tests/scoring/
```

Run frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

## 🏗️ Architecture

| Component | Technology |
|---|---|
| Backend | FastAPI, Python, SQLAlchemy |
| Frontend | React, Vite, JavaScript |
| Database | PostgreSQL |
| Cache and task queue | Redis, Celery |
| Migrations | Alembic |
| Scoring | Python, NumPy, SciPy, scikit-learn |

See [docs/architecture.md](docs/architecture.md) for more information.

## 🔧 Configuration

Backend configuration is loaded from environment variables or `backend/.env`. See [`backend/.env.example`](backend/.env.example) for available settings, including:

- `ENV`
- `DEBUG`
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`

## 🤝 Contributing

1. Create a feature branch from `main`.
2. Follow the project workflow in [docs/workflow.md](docs/workflow.md).
3. Run the relevant tests and checks.
4. Open a pull request with a clear description.
5. Request a review from at least one team member.

## 📄 License

This project is for educational and internal use. See [LICENSE](LICENSE) for details.
