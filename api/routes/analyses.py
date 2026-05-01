"""Analysis endpoints for ReconIQ FastAPI backend."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import verify_api_key
from api.db import get_db, AnalysisRecord
from api.schemas import (
    AnalysisCreateRequest,
    AnalysisResponse,
    AnalysisResultResponse,
    AnalysisStatus,
)
from api.worker import start_analysis_job

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _record_to_response(record: AnalysisRecord) -> AnalysisResponse:
    return AnalysisResponse(
        id=record.id,
        target_url=record.target_url,
        status=AnalysisStatus(record.status),
        modules=record.modules,
        provider=record.provider,
        model=record.model,
        fmt=record.fmt,
        created_at=record.created_at or datetime.now(timezone.utc),
        updated_at=record.updated_at or datetime.now(timezone.utc),
        progress_pct=record.progress_pct,
        progress_msg=record.progress_msg,
        report_path=record.report_path,
        error=record.error,
    )


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    request: AnalysisCreateRequest,
    api_key: str = Depends(verify_api_key),
) -> AnalysisResponse:
    db = get_db()
    record = db.create_job(
        target_url=str(request.target_url),
        modules=request.modules,
        provider=request.provider,
        model=request.model,
        fmt=request.fmt.value,
    )
    start_analysis_job(record.id)
    return _record_to_response(record)


@router.get("", response_model=list[AnalysisResponse])
async def list_analyses(
    limit: int = 50,
    api_key: str = Depends(verify_api_key),
) -> list[AnalysisResponse]:
    db = get_db()
    records = db.list_jobs(limit=limit)
    return [_record_to_response(r) for r in records]


@router.get("/{job_id}", response_model=AnalysisResponse)
async def get_analysis(
    job_id: str,
    api_key: str = Depends(verify_api_key),
) -> AnalysisResponse:
    db = get_db()
    record = db.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _record_to_response(record)


@router.get("/{job_id}/results", response_model=AnalysisResultResponse)
async def get_analysis_results(
    job_id: str,
    api_key: str = Depends(verify_api_key),
) -> AnalysisResultResponse:
    db = get_db()
    record = db.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return AnalysisResultResponse(
        id=record.id,
        target_url=record.target_url,
        status=AnalysisStatus(record.status),
        results=record.results,
        report_path=record.report_path,
        error=record.error,
        created_at=record.created_at or datetime.now(timezone.utc),
        completed_at=record.completed_at,
    )
