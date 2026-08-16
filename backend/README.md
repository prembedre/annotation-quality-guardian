# 🛠️ Backend — Annotation Quality Guardian

FastAPI backend providing REST APIs, database connectivity, and data models for scoring data annotations.

---

## 📁 Structure

```
backend/
├── app/
│   ├── api/            # Route endpoints (health, annotations, projects, scores)
│   ├── core/           # Config (BaseSettings) and DB session/engine setup
│   ├── models/         # SQLAlchemy ORM models (Item, Annotator, Annotation, TrustScore)
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic
│   ├── utils/          # General helpers
│   └── main.py         # FastAPI application entry point
├── migrations/         # Alembic database migrations
├── .env.example        # Environment variable template
├── alembic.ini         # Alembic migration configuration
└── requirements.txt    # Python package dependencies
```

---

## ⚙️ Setup & Installation

### 1. Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and adjust the variables:

```bash
cp .env.example .env
```

Key environment variables:
- `ENV`: `development` | `staging` | `production`
- `DATABASE_URL`: e.g. `postgresql://postgres:postgres@localhost:5432/aqg_db` (or SQLite `sqlite:///./aqg_dev.db`)
- `REDIS_URL`: `redis://localhost:6379/0`
- `SECRET_KEY`: Random secret string
- `CORS_ORIGINS`: Comma-separated allowed frontend URLs

---

## 🗄️ Database Migrations (Alembic)

```bash
# Run all pending migrations
alembic upgrade head

# Generate a new migration after editing models
alembic revision --autogenerate -m "describe_changes"

# Rollback one migration
alembic downgrade -1
```

---

## 🚀 Running the Server

```bash
# Run from within the backend directory:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Docs (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Testing

```bash
# From workspace root or backend directory:
pytest tests/backend/
```
