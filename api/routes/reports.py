"""Report endpoints for ReconIQ FastAPI backend."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from api.auth import verify_api_key
from api.db import get_db

router = APIRouter(prefix="/reports", tags=["reports"])

MIME_TYPES = {
    ".md": "text/markdown",
    ".html": "text/html",
    ".pdf": "application/pdf",
}


@router.get("/{job_id}")
async def download_report(
    job_id: str,
    api_key: str = Depends(verify_api_key),
) -> FileResponse:
    db = get_db()
    record = db.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    if not record.report_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not yet generated",
        )
    path = Path(record.report_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found",
        )
    ext = path.suffix
    return FileResponse(
        path=str(path),
        media_type=MIME_TYPES.get(ext, "application/octet-stream"),
        filename=path.name,
    )
