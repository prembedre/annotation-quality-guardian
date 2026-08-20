"""
API routes for asynchronous background jobs (Celery + Redis).
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from celery.result import AsyncResult

from app.celery_app import celery_app
from app.tasks.behavioral_tasks import compute_behavioral_score_task
from app.tasks.embedding_tasks import process_project_embeddings_task
from app.tasks.trust_score_tasks import compute_project_trust_scores_task, compute_item_trust_score_task
from app.schemas.jobs import (
    BehavioralJobRequest,
    EmbeddingJobRequest,
    TrustScoreJobRequest,
    JobStatusResponse,
)

router = APIRouter(
    prefix="/jobs",
    tags=["Async Jobs"],
)


@router.post("/behavioral", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_behavioral_job(payload: BehavioralJobRequest):
    """
    Trigger an asynchronous behavioral anomaly computation job.
    """
    try:
        task = compute_behavioral_score_task.delay(
            project_id=payload.project_id,
            annotator_id=payload.annotator_id,
            anomaly_score=payload.anomaly_score,
            item_id=payload.item_id,
            time_score=payload.time_score,
            streak_score=payload.streak_score,
            anomaly_flag=payload.anomaly_flag,
            reason=payload.reason,
            details=payload.details,
        )
        return JobStatusResponse(
            job_id=task.id,
            status="PENDING",
            task_name=task.name or "compute_behavioral_score_task",
            created_at=datetime.utcnow(),
            result_available=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to submit behavioral job to background queue: {str(exc)}",
        )


@router.post("/embedding", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_embedding_job(payload: EmbeddingJobRequest):
    """
    Trigger an asynchronous embedding outlier calculation job for a project.
    """
    try:
        task = process_project_embeddings_task.delay(
            project_id=payload.project_id,
            model_name=payload.model_name,
            outlier_threshold=payload.outlier_threshold,
        )
        return JobStatusResponse(
            job_id=task.id,
            status="PENDING",
            task_name=task.name or "process_project_embeddings_task",
            created_at=datetime.utcnow(),
            result_available=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to submit embedding job to background queue: {str(exc)}",
        )


@router.post("/trust-score", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_trust_score_job(payload: TrustScoreJobRequest):
    """
    Trigger an asynchronous multi-signal unified trust score calculation job.
    """
    try:
        if payload.item_id is not None:
            task = compute_item_trust_score_task.delay(
                project_id=payload.project_id,
                item_id=payload.item_id,
                weights=payload.weights,
            )
        else:
            task = compute_project_trust_scores_task.delay(
                project_id=payload.project_id,
                weights=payload.weights,
            )

        return JobStatusResponse(
            job_id=task.id,
            status="PENDING",
            task_name=task.name or "compute_trust_scores_task",
            created_at=datetime.utcnow(),
            result_available=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to submit trust score job to background queue: {str(exc)}",
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Retrieve current status, completion timestamp, and result of an async background job.
    """
    try:
        res = AsyncResult(job_id, app=celery_app)

        # Map Celery internal states to standard states
        state_mapping = {
            "PENDING": "PENDING",
            "STARTED": "RUNNING",
            "RETRY": "RUNNING",
            "SUCCESS": "COMPLETED",
            "FAILURE": "FAILED",
            "REVOKED": "FAILED",
        }
        mapped_status = state_mapping.get(res.status, res.status)

        result_data = None
        error_msg = None

        if res.successful():
            result_data = res.result
        elif res.failed():
            error_msg = str(res.result)

        return JobStatusResponse(
            job_id=job_id,
            status=mapped_status,
            result_available=res.ready(),
            result=result_data,
            error=error_msg,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying job status: {str(exc)}",
        )
