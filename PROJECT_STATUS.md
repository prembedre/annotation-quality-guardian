# 🛡️ Annotation Quality Guardian (AQG) — Current Project Status

**Repository:** [prembedre/annotation-quality-guardian](https://github.com/prembedre/annotation-quality-guardian)  
**Branch:** `main`  
**Current Milestone:** Phase 3 — Dashboard & Integrations  
**Status Date:** September 7, 2026  
**Overall Phase 3 Status:** 🟡 **Backend & DB 100% Complete | Frontend UI Pending**

---

## 1. Executive Summary

The **Annotation Quality Guardian (AQG)** platform provides automated quality auditing, trust scoring, and anomaly detection for machine learning data annotations.

All **Phase 3 Backend, Database, Scoring, and Integration** objectives have been fully implemented, integrated, and verified:
- **Annotator Leaderboard Service & API:** Calculates rolling accuracy, average trust score, gold accuracy, and throughput per annotator.
- **Inter-Annotator Agreement Heatmap Service & API:** Pairwise annotator agreement matrix computation and disagreement breakdown.
- **Real-Time Webhook Ingestion API:** Direct streaming of annotation payloads (`POST /api/webhook/annotations`) with immediate schema validation, persistence, and trust score recalculation.
- **Configurable Quality Thresholds:** Project-level flagging sensitivity and weight tuning (`GET/PUT /api/projects/{id}/settings`).
- **Enhanced Reviewer Resolution Workflow:** Granular reviewer decisions (`confirm`, `correct`, `escalate`), ground truth assignment, and dynamic trust score adjustments.
- **Automated Test Suite:** 63 passing tests across backend, scoring algorithms, and integrations.

```
Phase 3 Backend, DB & Scoring Completion Tracker:
████████████████████████████████████████  100% (Backend, DB, Scoring & API Complete)
Phase 3 Frontend UI Completion Tracker:
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0% (UI Components Pending)
```

---

## 2. Phase 3 Task Matrix

| # | Task | Deliverable | Backend & DB | Frontend UI | Status |
|---|---|---|:---:|:---:|:---:|
| **1** | **Annotator Leaderboard** | Rolling accuracy & trust score ranking per annotator (`GET /api/dashboard/leaderboard`) | 🟢 **Complete** | 🔴 **Pending** | 🟡 In Progress |
| **2** | **Agreement Heatmap** | Pairwise annotator agreement matrix (`GET /api/dashboard/agreement-heatmap`) | 🟢 **Complete** | 🔴 **Pending** | 🟡 In Progress |
| **3** | **Webhook Live Ingestion** | Real-time external label streaming receiver (`POST /api/webhook/annotations`) | 🟢 **Complete** | ⚪ *N/A (API)* | 🟢 **Complete** |
| **4** | **Configurable Thresholds** | Admin tuning of flagging sensitivity & signal weights (`GET/PUT /api/projects/{id}/settings`) | 🟢 **Complete** | 🔴 **Pending** | 🟡 In Progress |
| **5** | **Reviewer Resolve Workflow** | Enhanced `confirm` / `correct` / `escalate` actions (`POST /api/review/{item_id}/resolve`) | 🟢 **Complete** | 🔴 **Pending** | 🟡 In Progress |

---

## 3. Module & Architectural Status

```mermaid
graph TD
    ExternalTools[External Annotation Tools: Label Studio, CVAT, Prodigy] -->|Real-Time Payload| WebhookAPI[POST /api/webhook/annotations]
    UI[Frontend: React 18 + Vite] -->|1. Upload Dataset| UploadAPI[POST /api/annotations/upload]
    UI -->|2. Trigger Async Jobs| JobsAPI[POST /api/jobs/behavioral | embedding | trust-score]
    UI -->|3. View Flagged Queue| QueueAPI[GET /api/review/queue]
    UI -->|4. Resolve Item| ResolveAPI[POST /api/review/:id/resolve]
    UI -->|5. Leaderboard & Heatmap| DashAPI[GET /api/dashboard/leaderboard | agreement-heatmap]
    UI -->|6. Project Settings| SettingsAPI[GET / PUT /api/projects/:id/settings]
    UI -->|7. Export Labeled Data| ExportAPI[GET /api/projects/:id/export]
    
    WebhookAPI --> WebhookService[webhook_service.py]
    WebhookService --> DB[(PostgreSQL Database)]
    WebhookService --> TrustScoreService[trust_score_service.py]

    JobsAPI --> CeleryWorker[Celery Background Workers + Redis]
    CeleryWorker --> TrustScoreService
    
    UploadAPI --> IngestService[ingestion_service.py]
    IngestService --> DB
    
    DB --> GoldService[gold_standard_service.py]
    DB --> KappaService[kappa_service.py]
    DB --> BehaviorService[behavior_service.py]
    DB --> EmbeddingService[embedding_service.py]
    DB --> HeatmapService[heatmap.py]
    DB --> LeaderboardService[leaderboard/service.py]
    
    GoldService --> TrustScoreService
    KappaService --> TrustScoreService
    BehaviorService --> TrustScoreService
    EmbeddingService --> TrustScoreService
    TrustScoreService --> DB
    
    DB --> QueueAPI
    DB --> ResolveAPI
    DB --> DashAPI
    DB --> SettingsAPI
    DB --> ExportAPI
```

### 3.1 Backend & Scoring Architecture
- **Dashboard Service (`backend/app/services/dashboard_service.py` & `scoring/`):** Computes annotator leaderboard rankings and inter-annotator pairwise agreement heatmaps with disagreement analysis.
- **Webhook Service (`backend/app/services/webhook_service.py`):** Validates incoming payload constraints, checks for duplicate annotations, registers new items/annotators if necessary, and immediately computes the unified Trust Score.
- **Project Settings Service (`backend/app/services/project_settings_service.py`):** Manages project threshold configurations, ensuring weight balances and fallback defaults.
- **Reviewer Workflow Service (`backend/app/api/review.py`):** Supports `confirm`, `correct`, and `escalate` actions, records reviewer decisions, updates gold labels, and recalculates trust scores in real time.

### 3.2 Database Layer (`database/` & `backend/migrations/`)
- Alembic schema migrations up to date:
  - `0001_initial_schema.py` — Core entities (Project, Item, Annotator, Annotation, TrustScore)
  - `0002_phase2_scoring.py` — Behavioral and Embedding score tables
  - `0003_phase3_thresholds_and_reviewer_workflow.py` — `project_thresholds` and `reviewer_decisions` tables

---

## 4. API Endpoints Reference

| Method | Endpoint | Query / Body Params | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/webhook/annotations` | JSON payload (project, item, annotator, label, confidence, etc.) | Real-time live annotation ingestion |
| `GET` | `/api/dashboard/leaderboard` | `project_id` (optional) | Ranked annotator metrics (trust score, accuracy, volume) |
| `GET` | `/api/dashboard/agreement-heatmap` | `project_id` (required) | Pairwise inter-annotator agreement matrix & stats |
| `GET` | `/api/projects/{id}/settings` | `project_id` | Retrieves configurable project scoring thresholds |
| `PUT` | `/api/projects/{id}/settings` | `{"flag_threshold": 0.65, "gold_weight": 0.35, ...}` | Updates project scoring thresholds and weights |
| `POST` | `/api/review/{item_id}/resolve` | `{"action": "confirm"\|"correct"\|"escalate", "correct_label": "...", "notes": "..."}` | Resolves review queue item and recalculates trust score |
| `GET` | `/api/review/queue` | `project_id`, `flagged`, `min_score`, `max_score`, `page`, `page_size` | Returns paginated items requiring human review |
| `POST` | `/api/annotations/upload` | Multipart: `file`, `project_id` | Ingests CSV or JSON annotation datasets |
| `GET` | `/api/annotations/` | `project_id`, `annotator_id`, `limit`, `offset` | Lists individual annotations |
| `POST` | `/api/jobs/behavioral` | `{"project_id": 1, ...}` | Submits background behavioral anomaly score record job |
| `POST` | `/api/jobs/embedding` | `{"project_id": 1, ...}` | Submits background embedding outlier analysis job |
| `POST` | `/api/jobs/trust-score` | `{"project_id": 1, ...}` | Submits background unified trust score computation job |
| `GET` | `/api/jobs/{job_id}` | None | Retrieves status and payload of any background job |
| `GET` | `/api/projects/{id}/export` | `format=csv` or `format=json` | Exports full project dataset with quality scores |
| `GET` | `/api/projects/` | `limit`, `offset` | Lists all projects |
| `POST` | `/api/projects/` | `{"name": "...", "label_set": [...]}` | Creates a new annotation project |
| `GET` | `/api/scores/` | `project_id` | Fetches project-level gold accuracy & Kappa scores |
| `GET` | `/health` | None | Health check & database connection ping |

---

## 5. Test Suite Verification

All **63 test cases** pass with zero errors:

```text
tests\backend\test_behavior_service.py ..                                [  3%]
tests\backend\test_celery.py .....                                       [ 11%]
tests\backend\test_embedding_service.py .                                [ 12%]
tests\backend\test_export.py ....                                        [ 19%]
tests\backend\test_health.py ..                                          [ 22%]
tests\backend\test_ingestion.py .....                                    [ 30%]
tests\backend\test_jobs_api.py ....                                      [ 36%]
tests\backend\test_models.py .......                                     [ 47%]
tests\backend\test_phase3_database.py .....                              [ 55%]
tests\backend\test_phase3_integration.py ...............                 [ 79%]
tests\backend\test_review_queue.py ...                                   [ 84%]
tests\backend\test_trust_score_service.py .....                          [ 92%]
tests\scoring\test_heatmap.py ..                                         [ 95%]
tests\scoring\test_leaderboard.py ...                                    [100%]

====================== 63 passed in 5.55s =======================
```

---

## 6. Next Steps & Pending Work

- **Frontend Dashboard Components:**
  - Build Annotator Leaderboard UI table in `frontend/src/pages/Dashboard.jsx`.
  - Build Inter-Annotator Agreement Heatmap visual component.
- **Frontend Review Queue Workflow:**
  - Add interactive resolution modal/buttons (`Confirm`, `Correct`, `Escalate`) in `frontend/src/components/ReviewQueueTable.jsx`.
- **Frontend Project Settings:**
  - Add Thresholds & Weight Configuration UI in `frontend/src/pages/Projects.jsx`.
