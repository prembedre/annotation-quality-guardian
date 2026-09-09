# 🛡️ Annotation Quality Guardian (AQG) — Current Project Status

**Repository:** [prembedre/annotation-quality-guardian](https://github.com/prembedre/annotation-quality-guardian)  
**Branch:** `main`  
**Current Milestone:** Phase 4 — Automation & Database Integrations  
**Status Date:** September 9, 2026  
**Overall Status:** 🟢 **Phase 1, 2, 3 Complete (100%) | Phase 4 Backend & Database Complete (100%)**

---

## 1. Executive Summary

The **Annotation Quality Guardian (AQG)** platform provides automated quality auditing, multi-signal trust scoring, behavioral anomaly detection, inter-annotator agreement matrices, read-only external database integrations, and automated task rerouting for data annotation pipelines.

### Status Highlights:
- **Phase 1 (Core Platform & Ingestion):** 🟢 Complete
- **Phase 2 (Scoring Engine & Async Tasks):** 🟢 Complete
- **Phase 3 (Dashboard, Heatmaps & Reviewer Workflow):** 🟢 Complete across Backend, DB, Scoring, and Frontend UI
- **Phase 4 (Automation, External DB Connectors & Rerouting):** 🟢 Backend & Database 100% Complete
- **Automated Test Suite:** 74 tests passing (100% success rate)

```
Phase 1–3 Overall Completion:
████████████████████████████████████████  100% (Core, Scoring, Dashboard & UI)
Phase 4 Backend & DB Completion:
████████████████████████████████████████  100% (Connectors, Rerouting & A/B DB)
```

---

## 2. Phase 3 Deliverables Matrix

| # | Task | Deliverable | Backend & DB | Frontend UI | Status |
|---|---|---|:---:|:---:|:---:|
| **1** | **Annotator Leaderboard** | Rolling accuracy & trust score ranking per annotator (`GET /api/dashboard/leaderboard`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **2** | **Agreement Heatmap** | Pairwise annotator agreement matrix (`GET /api/dashboard/agreement-heatmap`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **3** | **Webhook Live Ingestion** | Real-time external label streaming receiver (`POST /api/webhook/annotations`) | 🟢 **Complete** | ⚪ *N/A (API)* | 🟢 **Complete** |
| **4** | **Configurable Thresholds** | Admin tuning of flagging sensitivity & signal weights (`GET/PUT /api/projects/{id}/settings`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **5** | **Reviewer Resolve Workflow** | Enhanced `confirm` / `correct` / `escalate` actions (`POST /api/review/{item_id}/resolve`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |

---

## 3. Phase 4 Deliverables Matrix (Backend & Database)

| # | Task | Deliverable | Backend | Database | Status |
|---|---|---|:---:|:---:|:---:|
| **1** | **Read-Only DB Connector** | Configurable external DB connections with strict read-only query guard (`POST/GET/DELETE /api/integrations/connectors`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **2** | **Connection Verification** | Live connection latency and read-only verification test (`POST /api/integrations/connectors/{id}/test`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **3** | **Live DB Ingestion Sync** | Read-only external database sync pipeline into AQG ingestion (`POST /api/integrations/connectors/{id}/sync`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **4** | **Automatic Task Rerouting** | Reassignment queue and audit tracking (`GET /api/rerouting/pending`, `POST /api/rerouting/{item_id}/assign`) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **5** | **A/B Testing Database Support** | Label schema and guideline experiment versions (`ab_test_experiments` table & ORM) | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **6** | **Phase 4 Migrations & Schema** | Alembic migration `0004_phase4...` & PostgreSQL DDL schema with compound indexes | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |
| **7** | **Phase 4 Sample Data** | Sample records for connectors, rerouted tasks, and A/B experiments | 🟢 **Complete** | 🟢 **Complete** | 🟢 **Complete** |

---

## 4. Architecture & Data Flow

```mermaid
graph TD
    ExternalDB[(External Labeling DB: Label Studio / CVAT / Postgres)] -->|Read-Only Query / Sync| ConnectorService[external_connector_service.py]
    ExternalTools[External Annotation Webhooks] -->|POST /api/webhook/annotations| WebhookAPI[Webhook API]
    
    UI[Frontend: React 18 + Vite] -->|1. Upload Dataset| UploadAPI[POST /api/annotations/upload]
    UI -->|2. Trigger Async Jobs| JobsAPI[POST /api/jobs/behavioral | embedding | trust-score]
    UI -->|3. View Flagged Queue| QueueAPI[GET /api/review/queue]
    UI -->|4. Resolve Item| ResolveAPI[POST /api/review/:id/resolve]
    UI -->|5. Leaderboard & Heatmap| DashAPI[GET /api/dashboard/leaderboard | agreement-heatmap]
    UI -->|6. Project Settings| SettingsAPI[GET / PUT /api/projects/:id/settings]
    UI -->|7. Export Labeled Data| ExportAPI[GET /api/projects/:id/export]
    UI -->|8. Manage DB Connectors| ConnectorAPI[POST / GET / DELETE /api/integrations/connectors]
    UI -->|9. Task Rerouting Queue| RerouteAPI[GET / POST /api/rerouting]

    ConnectorService --> IngestService[ingestion_service.py]
    WebhookAPI --> WebhookService[webhook_service.py]
    WebhookService --> DB[(PostgreSQL Database)]
    WebhookService --> TrustScoreService[trust_score_service.py]

    JobsAPI --> CeleryWorker[Celery Background Workers + Redis]
    CeleryWorker --> TrustScoreService
    
    UploadAPI --> IngestService
    IngestService --> DB
    
    DB --> GoldService[gold_standard_service.py]
    DB --> KappaService[kappa_service.py]
    DB --> BehaviorService[behavior_service.py]
    DB --> EmbeddingService[embedding_service.py]
    DB --> HeatmapService[heatmap.py]
    DB --> LeaderboardService[leaderboard/service.py]
    DB --> RerouteService[rerouting_service.py]
    
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
    DB --> ConnectorAPI
    DB --> RerouteAPI
```

---

## 5. Database Models & Schema Status

| Table Name | Model | Purpose | Phase Added |
|---|---|---|:---:|
| `projects` | `Project` | Annotation projects with defined label sets | Phase 1 |
| `annotators` | `Annotator` | Annotator identity & performance links | Phase 1 |
| `items` | `Item` | Annotation data points (including gold standards) | Phase 1 |
| `annotations` | `Annotation` | Annotator submissions, confidences & durations | Phase 1 |
| `quality_scores` | `QualityScore` | General quality metrics | Phase 1 |
| `behavioral_scores` | `BehavioralScore` | Timing, streak, and anomaly scores | Phase 2 |
| `embedding_results` | `EmbeddingResult` | Vector embedding outlier detection | Phase 2 |
| `trust_scores` | `TrustScore` | Multi-signal weighted quality score & flags | Phase 2 |
| `project_thresholds` | `ProjectThreshold` | Configurable per-project quality thresholds | Phase 3 |
| `reviewer_decisions` | `ReviewerDecision` | Reviewer resolution audit log (confirm/correct/escalate) | Phase 3 |
| `external_db_connectors` | `ExternalDBConnector` | Read-only external database connection configurations | Phase 4 |
| `reroute_histories` | `RerouteHistory` | Task reassignment logs and trust score snapshots | Phase 4 |
| `ab_test_experiments` | `ABTestExperiment` | Label schema and guideline A/B testing configurations | Phase 4 |

### Alembic Migrations:
- `0001_initial_schema.py` — Core entities
- `0002_phase2_scoring.py` — Behavioral and Embedding score tables
- `0003_phase3_thresholds_and_reviewer_workflow.py` — Project thresholds and reviewer decisions
- `0004_phase4_external_connectors_rerouting_ab_testing.py` — Connectors, task rerouting, and A/B testing

---

## 6. API Endpoints Reference

| Method | Endpoint | Query / Body Params | Description | Phase |
| :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/integrations/connectors` | JSON (name, type, host, port, db, credentials, query_config) | Registers read-only external database connector | Phase 4 |
| `GET` | `/api/integrations/connectors` | `status` (optional) | Lists registered connectors (credentials omitted) | Phase 4 |
| `POST` | `/api/integrations/connectors/{id}/test` | None | Tests database latency & verifies read-only access | Phase 4 |
| `DELETE` | `/api/integrations/connectors/{id}` | None | Deletes a connector configuration | Phase 4 |
| `POST` | `/api/integrations/connectors/{id}/sync` | JSON (`project_id`, `table_name`, `limit`) | Ingests annotations directly from external DB (read-only) | Phase 4 |
| `GET` | `/api/rerouting/pending` | `project_id` (optional) | Retrieves pending items flagged for task rerouting | Phase 4 |
| `POST` | `/api/rerouting/{item_id}/assign` | JSON (`reassigned_annotator_id`, `reason`) | Reassigns task to annotator and logs reroute history | Phase 4 |
| `POST` | `/api/webhook/annotations` | JSON payload (project, item, annotator, label, confidence, etc.) | Real-time live annotation ingestion | Phase 3 |
| `GET` | `/api/dashboard/leaderboard` | `project_id` (optional) | Ranked annotator metrics (trust score, accuracy, volume) | Phase 3 |
| `GET` | `/api/dashboard/agreement-heatmap` | `project_id` (required) | Pairwise inter-annotator agreement matrix & stats | Phase 3 |
| `GET` | `/api/projects/{id}/settings` | None | Retrieves configurable project scoring thresholds | Phase 3 |
| `PUT` | `/api/projects/{id}/settings` | JSON (`gold_threshold`, `kappa_threshold`, etc.) | Updates project scoring thresholds | Phase 3 |
| `POST` | `/api/review/{item_id}/resolve` | JSON (`action`, `correct_label`, `notes`) | Resolves review queue item and recalculates trust score | Phase 3 |
| `GET` | `/api/review/queue` | `project_id`, `flagged`, `min_score`, `max_score`, `page`, `page_size` | Returns paginated items requiring human review | Phase 1/2 |
| `POST` | `/api/annotations/upload` | Multipart: `file`, `project_id` | Ingests CSV or JSON annotation datasets | Phase 1 |
| `GET` | `/api/annotations/` | `project_id`, `annotator_id`, `limit`, `offset` | Lists individual annotations | Phase 1 |
| `POST` | `/api/jobs/behavioral` | `{"project_id": 1, ...}` | Submits background behavioral anomaly score record job | Phase 2 |
| `POST` | `/api/jobs/embedding` | `{"project_id": 1, ...}` | Submits background embedding outlier analysis job | Phase 2 |
| `POST` | `/api/jobs/trust-score` | `{"project_id": 1, ...}` | Submits background unified trust score computation job | Phase 2 |
| `GET` | `/api/jobs/{job_id}` | None | Retrieves status and payload of any background job | Phase 2 |
| `GET` | `/api/projects/{id}/export` | `format=csv` or `format=json` | Exports full project dataset with quality scores | Phase 1/2 |
| `GET` | `/api/projects/` | `limit`, `offset` | Lists all projects | Phase 1 |
| `POST` | `/api/projects/` | `{"name": "...", "label_set": [...]}` | Creates a new annotation project | Phase 1 |
| `GET` | `/api/scores/` | `project_id` | Fetches project-level gold accuracy & Kappa scores | Phase 1 |
| `GET` | `/health` | None | Health check & database connection ping | Phase 1 |

---

## 7. Test Suite Verification

All **74 automated tests** across all phases pass with 100% success rate:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Downloads\annotation-quality-guardian
configfile: pytest.ini
plugins: anyio-4.14.2, asyncio-1.4.0
collected 74 items

tests\backend\test_behavior_service.py ..                                [  2%]
tests\backend\test_celery.py .....                                       [  9%]
tests\backend\test_embedding_service.py .                                [ 10%]
tests\backend\test_export.py ....                                        [ 16%]
tests\backend\test_health.py ..                                          [ 18%]
tests\backend\test_ingestion.py .....                                    [ 25%]
tests\backend\test_jobs_api.py ....                                      [ 31%]
tests\backend\test_models.py .......                                     [ 40%]
tests\backend\test_phase3_database.py .....                              [ 47%]
tests\backend\test_phase3_integration.py ...............                 [ 67%]
tests\backend\test_phase4_database.py .....                              [ 74%]
tests\backend\test_phase4_integration.py ......                          [ 82%]
tests\backend\test_review_queue.py ...                                   [ 86%]
tests\backend\test_trust_score_service.py .....                          [ 93%]
tests\scoring\test_heatmap.py ..                                         [ 95%]
tests\scoring\test_leaderboard.py ...                                    [100%]

====================== 74 passed in 3.22s =======================
```

---

## 8. Recent Stabilization & Bug Fixes (September 2026)

Following Phase 4 implementation, comprehensive bug fixes and stabilizations were applied to ensure full system functionality:

### Database & Schema
- **Dynamic Schema Patching:** Implemented `db_patch.py` to auto-patch the SQLite database schema on startup to seamlessly include missing columns like `projects.automation_enabled` without data loss.
- **Model Stability:** Resolved `sqlite3.IntegrityError` (NOT NULL constraint failures) by adding a `score` alias mapping and property to the `TrustScore` ORM model, ensuring backward and forward compatibility.

### Backend API Reliability
- **Null-Safety & Graceful Degradation:** Fully refactored endpoints in `dashboard.py`, `rerouting.py`, and `review.py` to handle empty database states, missing project IDs, and annotator attribute variations (e.g., `username` vs `name`) gracefully, eliminating 500 Internal Server Errors.

### Frontend Compatibility
- **Robust Parsing:** Updated `Projects.jsx` to correctly parse and render array-based API responses and handle single-project-seed payloads dynamically.

### Deployment & Verification
- **Test Data Seeding:** Created a robust `seed_demo_data.py` script that populates all necessary tables (Projects, Annotators, Items, Annotations, TrustScores, RerouteHistory) for functional demonstrations.
- **Live Servers:** Verified that the core endpoints function correctly via `verify_all.py`, with both the Vite frontend server and FastAPI backend daemon running successfully and accessible locally.
