# 🛡️ Annotation Quality Guardian (AQG)

**A comprehensive platform for monitoring, scoring, and improving the quality of data annotations.**

AQG helps teams ensure high-quality labeled datasets by combining gold-standard validation, inter-annotator agreement metrics, behavioral anomaly detection, and embedding-based outlier analysis.

---

## 📁 Project Structure

```
annotation-quality-guardian/
│
├── backend/          # FastAPI backend & API integration
├── database/         # Schema definitions & sample data
├── scoring/          # Quality scoring engine (Kappa, gold checks, anomalies)
├── frontend/         # React-based dashboard UI
├── data/             # Shared sample datasets
├── docs/             # Project documentation
└── tests/            # Unit & integration tests
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** — Backend & scoring engine
- **Node.js 18+** — Frontend
- **PostgreSQL 15+** — Database

### 1. Clone the Repository

```bash
git clone https://github.com/Prembedre27/annotation-quality-guardian.git
cd annotation-quality-guardian
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 3. Database Setup

```bash
# Create the database and run the schema
psql -U postgres -c "CREATE DATABASE aqg_db;"
psql -U postgres -d aqg_db -f database/schema.sql
psql -U postgres -d aqg_db -f database/sample_data.sql
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

---

## 🏗️ Architecture

| Component   | Technology       | Owner    |
|-------------|------------------|----------|
| Backend     | FastAPI (Python) | Member 1 |
| Database    | PostgreSQL       | Member 2 |
| Scoring     | Python           | Member 3 |
| Frontend    | React (Vite)     | Member 4 |

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

---

## 🧪 Running Tests

```bash
# Backend tests
pytest tests/backend/

# Scoring tests
pytest tests/scoring/

# Frontend tests
cd frontend && npm test
```

---

## 📄 License

This project is for educational / internal use. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Create a feature branch from `main`
2. Follow the coding standards in [docs/workflow.md](docs/workflow.md)
3. Open a Pull Request with a clear description
4. Request review from at least one team member
