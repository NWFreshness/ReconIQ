"""SQLite persistence layer for analysis jobs."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    Float,
    Text,
    select,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

DEFAULT_DB_PATH = Path(os.path.expanduser("~")) / ".reconiq" / "reconiq.db"


class AnalysisJob(Base):  # type: ignore[valid-type,misc]
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True)
    target_url = Column(String(2048), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    modules = Column(Text, nullable=False, default="[]")
    provider = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    fmt = Column(String(10), nullable=False, default="md")
    progress_pct = Column(Float, nullable=False, default=0.0)
    progress_msg = Column(Text, nullable=True)
    report_path = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    results = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


@dataclass
class AnalysisRecord:
    id: str
    target_url: str
    status: str
    modules: list[str] = field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    fmt: str = "md"
    progress_pct: float = 0.0
    progress_msg: str | None = None
    report_path: str | None = None
    error: str | None = None
    results: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or str(DEFAULT_DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def create_job(
        self,
        target_url: str,
        modules: list[str],
        provider: str | None,
        model: str | None,
        fmt: str = "md",
    ) -> AnalysisRecord:
        job_id = str(uuid.uuid4())
        with self.get_session() as session:
            job = AnalysisJob(
                id=job_id,
                target_url=target_url,
                status="pending",
                modules=json.dumps(modules),
                provider=provider,
                model=model,
                fmt=fmt,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(job)
            session.commit()
            return self._to_record(job)

    def get_job(self, job_id: str) -> AnalysisRecord | None:
        with self.get_session() as session:
            job = session.get(AnalysisJob, job_id)
            return self._to_record(job) if job else None

    def update_job(
        self,
        job_id: str,
        status: str | None = None,
        progress_pct: float | None = None,
        progress_msg: str | None = None,
        report_path: str | None = None,
        error: str | None = None,
        results: dict[str, Any] | None = None,
    ) -> AnalysisRecord | None:
        with self.get_session() as session:
            job = session.get(AnalysisJob, job_id)
            if not job:
                return None
            if status is not None:
                job.status = status
                if status in ("completed", "failed"):
                    job.completed_at = datetime.now(timezone.utc)
            if progress_pct is not None:
                job.progress_pct = progress_pct
            if progress_msg is not None:
                job.progress_msg = progress_msg
            if report_path is not None:
                job.report_path = report_path
            if error is not None:
                job.error = error
            if results is not None:
                job.results = json.dumps(results)
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._to_record(job)

    def list_jobs(self, limit: int = 50) -> list[AnalysisRecord]:
        with self.get_session() as session:
            stmt = select(AnalysisJob).order_by(AnalysisJob.created_at.desc()).limit(limit)
            jobs = session.execute(stmt).scalars().all()
            return [self._to_record(j) for j in jobs]

    def _to_record(self, job: AnalysisJob) -> AnalysisRecord:
        return AnalysisRecord(
            id=job.id,
            target_url=job.target_url,
            status=job.status,
            modules=json.loads(job.modules) if job.modules else [],
            provider=job.provider,
            model=job.model,
            fmt=job.fmt,
            progress_pct=job.progress_pct,
            progress_msg=job.progress_msg,
            report_path=job.report_path,
            error=job.error,
            results=json.loads(job.results) if job.results else None,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )


# Singleton
_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def reset_db(db_path: str | None = None) -> Database:
    global _db
    _db = Database(db_path)
    return _db
