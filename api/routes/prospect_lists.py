"""Prospect List endpoints for ReconIQ FastAPI backend."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.auth import verify_api_key
from api.db import get_db
from api.schemas import (
    AddAnalysisToListRequest,
    AnalysisResponse,
    ProspectListCreateRequest,
    ProspectListResponse,
    ProspectListUpdateRequest,
)
from api.routes.analyses import _record_to_response

router = APIRouter(prefix="/prospect-lists", tags=["prospect-lists"])


def _list_to_response(record) -> ProspectListResponse:
    return ProspectListResponse(
        id=record.id,
        name=record.name,
        description=record.description,
        analysis_count=record.analysis_count,
        created_at=record.created_at or datetime.now(timezone.utc),
        updated_at=record.updated_at or datetime.now(timezone.utc),
    )


# ── CRUD: Lists ─────────────────────────────────────────────────────────────


@router.post("", response_model=ProspectListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    request: ProspectListCreateRequest,
    api_key: str = Depends(verify_api_key),
) -> ProspectListResponse:
    db = get_db()
    record = db.create_list(
        name=request.name,
        description=request.description,
    )
    return _list_to_response(record)


@router.get("", response_model=list[ProspectListResponse])
async def list_lists(
    api_key: str = Depends(verify_api_key),
) -> list[ProspectListResponse]:
    db = get_db()
    records = db.list_lists()
    return [_list_to_response(r) for r in records]


@router.get("/{list_id}", response_model=ProspectListResponse)
async def get_list(
    list_id: str,
    api_key: str = Depends(verify_api_key),
) -> ProspectListResponse:
    db = get_db()
    record = db.get_list(list_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect list not found")
    return _list_to_response(record)


@router.put("/{list_id}", response_model=ProspectListResponse)
async def update_list(
    list_id: str,
    request: ProspectListUpdateRequest,
    api_key: str = Depends(verify_api_key),
) -> ProspectListResponse:
    db = get_db()
    record = db.update_list(
        list_id=list_id,
        name=request.name,
        description=request.description,
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect list not found")
    return _list_to_response(record)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: str,
    api_key: str = Depends(verify_api_key),
) -> None:
    db = get_db()
    deleted = db.delete_list(list_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect list not found")


# ── Membership: analyses in lists ───────────────────────────────────────────


@router.get("/{list_id}/analyses", response_model=list[AnalysisResponse])
async def list_analyses_in_list(
    list_id: str,
    api_key: str = Depends(verify_api_key),
) -> list[AnalysisResponse]:
    db = get_db()
    if not db.get_list(list_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect list not found")
    records = db.list_analyses_in_list(list_id)
    return [_record_to_response(r) for r in records]


@router.post("/{list_id}/analyses")
async def add_analysis_to_list(
    list_id: str,
    request: AddAnalysisToListRequest,
    response: Response,
    api_key: str = Depends(verify_api_key),
) -> dict:
    db = get_db()
    if not db.get_list(list_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect list not found")
    # Check if already in list before adding
    existing_lists = db.list_lists_for_analysis(request.analysis_id)
    is_new = any(l.id == list_id for l in existing_lists)
    if is_new:
        response.status_code = status.HTTP_200_OK
        return {"status": "already_in_list"}
    success = db.add_to_list(list_id, request.analysis_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    response.status_code = status.HTTP_201_CREATED
    return {"status": "added"}


@router.delete("/{list_id}/analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_analysis_from_list(
    list_id: str,
    analysis_id: str,
    api_key: str = Depends(verify_api_key),
) -> None:
    db = get_db()
    removed = db.remove_from_list(list_id, analysis_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
