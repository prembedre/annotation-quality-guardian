# 🛡️ Annotation Quality Guardian (AQG) — Current Project Status

**Repository:** [prembedre/annotation-quality-guardian](https://github.com/prembedre/annotation-quality-guardian)  
**Branch:** `main`  
**Current Milestone:** Phase 3 — Configurable Thresholds & Reviewer Workflow  
**Status Date:** August 20, 2026  
**Overall Phase 3 Status:** 🟡 **Partially Complete (Database 100%, Backend ~60%)**

---

## 1. Executive Summary

The **Annotation Quality Guardian (AQG)** platform provides automated quality auditing, trust scoring, and anomaly detection for machine learning data annotations.

All Phase 2 Backend & Integration objectives have been fully implemented, integrated, and verified:
- **Asynchronous Task Processing:** Configured Celery + Redis to offload intensive validation tasks.
- **Behavioral Anomaly Engine:** Tracks annotator speeds, click timings, and labeling patterns.
- **Embedding Outlier Service:** Identifies anomalous annotations by measuring vector distance outliers from the project centroid.
- **Unified Multi-Signal Trust Pipeline:** Combines Gold Accuracy, Fleiss' Kappa Agreement, Behavioral Anomalies, and Embedding Outliers with dynamic weight redistribution and review queue flagging.
- **Backward Compatibility:** All existing Phase 1 review queue, export, and ingestion services remain fully operational.

```
Phase 2 Task Completion Tracker:
████████████████████████████████████████  100% (All Phase 2 Tasks Complete)
```

---

## 2. Phase 2 Task Matrix

| # | Task | Deliverable | Status | Owner / Contributor |
|---|---|---|:---:|---|
| **1** | **Celery + Redis Infrastructure** | Setup background workers, JSON serialization, task retry logic | 🟢 **Complete** | Backend & Integration (You) |
| **2** | **Behavioral Anomaly Service** | Track speed, timing anomaly records, and annotator metrics | 🟢 **Complete** | Backend & Integration (You) |
| **3** | **Embedding Outlier Service** | Embed item representations, outlier scoring, and DB persistence | 🟢 **Complete** | Backend & Integration (You) |
| **4** | **Unified Trust Score Pipeline**| Multi-signal combination (Gold, Agreement, Behavioral, Embedding) | 🟢 **Complete** | Backend & Integration (You) |
| **5** | **Async Jobs API** | Endpoints to trigger scoring and query task execution status | 🟢 **Complete** | Backend & Integration (You) |
| **6** | **Review Queue & Export Sync** | Adapt Review Queue & Export to output complete Phase 2 signals | 🟢 **Complete** | Backend & Integration (You) |

---

## 3. Module & Architectural Status

```mermaid
graph TD
    UI[Frontend: React 18 + Vite] -->|1. Upload Dataset| UploadAPI[POST /api/annotations/upload]
    UI -->|2. Trigger Async Jobs| JobsAPI[POST /api/jobs/behavioral | embedding | trust-score]
    UI -->|3. View Flagged Queue| QueueAPI[GET /api/review/queue]
    UI -->|4. Resolve Dispute| ResolveAPI[POST /api/review/:id/resolve]
    UI -->|5. Export Labeled Data| ExportAPI[GET /api/projects/:id/export]
    
    JobsAPI --> CeleryWorker[Celery Background Workers + Redis]
    CeleryWorker --> TrustScoreService[trust_score_service.py]
    
    UploadAPI --> IngestService[ingestion_service.py]
    IngestService --> DB[(PostgreSQL Database)]
    
    DB --> GoldService[gold_standard_service.py]
    DB --> KappaService[kappa_service.py]
    DB --> BehaviorService[behavior_service.py]
    DB --> EmbeddingService[embedding_service.py]
    
    GoldService --> TrustScoreService
    KappaService --> TrustScoreService
    BehaviorService --> TrustScoreService
    EmbeddingService --> TrustScoreService
    TrustScoreService --> DB
    
    DB --> QueueAPI
    DB --> ResolveAPI
    DB --> ExportAPI
```

### 3.1 Backend & Integration (`backend/`)
- **FastAPI Core:** Dual routing for ingestion compatibility, integrated with `jobs` endpoint router.
- **SQLAlchemy ORM Models:** Mapped dynamic relationship bindings (`behavioral_scores` and `embedding_results` relationships) to solve SQLAlchemy 2.0 mapper constraints.
- **Asynchronous Engine:** Celery workers configured to serialize task status JSON objects into the Redis backend.

### 3.2 Database Layer (`database/` & `backend/migrations/`)
- alembic schema migrations applied up to Phase 2 models (`0002_phase2_scoring.py`).
- Automatic fallback to SQLite in-memory engine during testing to avoid local pg connection requirements.

---

## 4. API Endpoints Reference

| Method | Endpoint | Query / Body Params | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/annotations/upload` | Multipart: `file`, `project_id` | Ingests CSV or JSON annotation datasets |
| `POST` | `/api/jobs/behavioral` | `{"project_id": 1, "anomaly_score": 0.85, ...}` | Submits background behavioral anomaly score record job |
| `POST` | `/api/jobs/embedding` | `{"project_id": 1, "model_name": "...", ...}` | Submits background embedding outlier analysis job |
| `POST` | `/api/jobs/trust-score` | `{"project_id": 1, "weights": {...}}` | Submits background unified trust score computation job |
| `GET` | `/api/jobs/{job_id}` | None | Retrieve status and return payload of any Celery job |
| `GET` | `/api/review/queue` | `project_id`, `flagged`, `min_score`, `max_score`, `page`, `page_size` | Returns paginated items requiring human review |
| `POST` | `/api/review/{item_id}/resolve` | `{"ground_truth_label": "...", "notes": "..."}` | Assigns ground truth, unflags item, and marks resolved |
| `GET` | `/api/projects/{id}/export` | `format=csv` or `format=json` | Exports full project dataset with quality scores |
| `GET` | `/api/projects/` | `limit`, `offset` | Lists all projects |
| `POST` | `/api/projects/` | `{"name": "...", "label_set": [...]}` | Creates a new annotation project |
| `GET` | `/api/annotations/` | `project_id`, `annotator_id`, `limit`, `offset` | Lists individual annotations |
| `GET` | `/api/scores/` | `project_id` | Fetches project-level gold accuracy & Kappa scores |
| `GET` | `/health` | None | Health check & database connection ping |

---

## 5. Test Suite Verification

All **38 test cases** pass with zero errors:

```text
tests\backend\test_behavior_service.py ..                                [  5%]
tests\backend\test_celery.py .....                                       [ 18%]
tests\backend\test_embedding_service.py .                                [ 21%]
tests\backend\test_export.py ....                                        [ 31%]
tests\backend\test_health.py ..                                          [ 36%]
tests\backend\test_ingestion.py .....                                    [ 50%]
tests\backend\test_jobs_api.py ....                                      [ 60%]
tests\backend\test_models.py .......                                     [ 78%]
tests\backend\test_review_queue.py ...                                   [ 86%]
tests\backend\test_trust_score_service.py .....                          [100%]

====================== 38 passed in 1.30s =======================
```

---

## 6. Recent Git Commit Log

* `c31b2fe` — `docs: update PROJECT_PROGRESS_REPORT.md to reflect Phase 2 completion`
* `2526e04` — `docs: update PROJECT_STATUS.md to reflect Phase 2 completion`
* `379c58e` — `feat: Phase 2 backend - Celery tasks, behavioral & embedding services, unified trust score pipeline, job APIs, and tests`
* `29ed8c8` — `Refactor review queue and resolve endpoints`
* `0b43bf2` — `Update test_review_queue.py`
* `e61f04f` — `Refactor project export tests for clarity and structure`
* `4350db5` — `Enhance test coverage for scores and results`
* `2e353fc` — `Add BehavioralScore and EmbeddingResult to models`
* `c4f0ec9` — `Remove trust_scores relationship from TrustScore model`
* `15576ad` — `Update trust_score.py`
