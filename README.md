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
├── backend/             # FastAPI application and API services
├── frontend/            # React/Vite dashboard
├── database/            # PostgreSQL schema and sample data
├── scoring/             # Quality scoring engine
├── data/                # Shared sample datasets
├── docs/                # Architecture and workflow documentation
├── tests/               # Backend and scoring tests
├── docker-compose.yml   # Local backend, frontend, PostgreSQL, and Redis stack
└── README.md
```

## 🚀 Quick Start with Docker

### Prerequisites

- Docker Desktop, or Docker Engine with Docker Compose
- Git

Clone the repository and start the complete development stack:

```bash
git clone https://github.com/prembedre/annotation-quality-guardian.git
cd annotation-quality-guardian
docker compose up --build
```

The services will be available at:

| Service | URL |
|---|---|
| Frontend dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger API docs | http://localhost:8000/docs |
| ReDoc API docs | http://localhost:8000/redoc |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

Stop the services:

```bash
docker compose down
```

Stop the services and remove the PostgreSQL data volume:

```bash
docker compose down -v
```

> The default Docker credentials are intended for local development only. Change the database password and `SECRET_KEY` before using the application in a shared or production environment.

## 🛠️ Manual Development Setup

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\\Scripts\\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### Database

```bash
psql -U postgres -c "CREATE DATABASE aqg_db;"
psql -U postgres -d aqg_db -f database/schema.sql
psql -U postgres -d aqg_db -f database/sample_data.sql
```

### Frontend

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
