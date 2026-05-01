"""Background worker for running analysis jobs."""
from __future__ import annotations

import threading
from typing import Any, Callable

from api.db import get_db
from core.models import AnalysisRequest
from core.services import run_analysis


ProgressCallback = Callable[[str, float], None]


def run_analysis_job(job_id: str) -> None:
    """Run an analysis job in the background and update the database."""
    db = get_db()
    job = db.get_job(job_id)
    if not job:
        return

    db.update_job(job_id, status="running", progress_pct=0.0, progress_msg="Starting analysis")

    def progress(msg: str, pct: float) -> None:
        db.update_job(job_id, progress_pct=pct, progress_msg=msg)

    try:
        enabled_modules = {m: True for m in job.modules}
        request = AnalysisRequest(
            target_url=job.target_url,
            enabled_modules=enabled_modules,
            provider_override=job.provider,
            model_override=job.model,
            fmt=job.fmt,
        )
        result = run_analysis(request, progress_callback=progress)
        db.update_job(
            job_id,
            status="completed",
            progress_pct=100.0,
            progress_msg="Analysis complete",
            report_path=result.report_path,
            results=result.results,
        )
    except Exception as exc:
        db.update_job(
            job_id,
            status="failed",
            progress_msg="Analysis failed",
            error=str(exc),
        )


def start_analysis_job(job_id: str) -> None:
    """Start an analysis job in a background thread."""
    thread = threading.Thread(target=run_analysis_job, args=(job_id,), daemon=True)
    thread.start()
