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
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

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


class ProspectList(Base):  # type: ignore[valid-type,misc]
    __tablename__ = "prospect_lists"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    analysis_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships = relationship("ProspectListMembership", back_populates="list", cascade="all, delete-orphan")


class ProspectListMembership(Base):  # type: ignore[valid-type,misc]
    __tablename__ = "prospect_list_memberships"

    list_id = Column(String(36), ForeignKey("prospect_lists.id", ondelete="CASCADE"), primary_key=True)
    analysis_id = Column(String(36), primary_key=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    list = relationship("ProspectList", back_populates="memberships")


@dataclass
class ProspectListRecord:
    id: str
    name: str
    description: str | None = None
    analysis_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


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

    def delete_job(self, job_id: str) -> bool:
        with self.get_session() as session:
            job = session.get(AnalysisJob, job_id)
            if not job:
                return False
            session.delete(job)
            session.commit()
            return True

    def list_jobs(
        self,
        limit: int = 50,
        status: str | None = None,
        provider: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        min_score: float | None = None,
        error_only: bool = False,
    ) -> list[AnalysisRecord]:
        with self.get_session() as session:
            stmt = select(AnalysisJob)
            if status is not None:
                stmt = stmt.where(AnalysisJob.status == status)
            if provider is not None:
                stmt = stmt.where(AnalysisJob.provider == provider)
            if date_from is not None:
                stmt = stmt.where(AnalysisJob.created_at >= date_from)
            if date_to is not None:
                stmt = stmt.where(AnalysisJob.created_at <= date_to)
            if error_only:
                stmt = stmt.where(AnalysisJob.status == "failed")
            stmt = stmt.order_by(AnalysisJob.created_at.desc()).limit(limit)
            jobs = session.execute(stmt).scalars().all()
            results = [self._to_record(j) for j in jobs]
            if min_score is not None:
                results = self._filter_by_min_score(results, min_score)
            return results

    def _filter_by_min_score(
        self, records: list[AnalysisRecord], min_score: float
    ) -> list[AnalysisRecord]:
        filtered: list[AnalysisRecord] = []
        for r in records:
            ps = (r.results or {}).get("prospect_score") if r.results else None
            if ps and isinstance(ps, dict) and ps.get("overall", 0) >= min_score:
                filtered.append(r)
        return filtered

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

    # ── Prospect Lists CRUD ────────────────────────────────────────────────

    def create_list(
        self,
        name: str,
        description: str | None = None,
    ) -> ProspectListRecord:
        list_id = str(uuid.uuid4())
        with self.get_session() as session:
            lst = ProspectList(
                id=list_id,
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(lst)
            session.commit()
            return self._to_list_record(lst)

    def get_list(self, list_id: str) -> ProspectListRecord | None:
        with self.get_session() as session:
            lst = session.get(ProspectList, list_id)
            return self._to_list_record(lst) if lst else None

    def list_lists(self) -> list[ProspectListRecord]:
        with self.get_session() as session:
            stmt = select(ProspectList).order_by(ProspectList.created_at.desc())
            lists = session.execute(stmt).scalars().all()
            return [self._to_list_record(l) for l in lists]

    def update_list(
        self,
        list_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> ProspectListRecord | None:
        with self.get_session() as session:
            lst = session.get(ProspectList, list_id)
            if not lst:
                return None
            if name is not None:
                lst.name = name
            if description is not None:
                lst.description = description
            lst.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._to_list_record(lst)

    def delete_list(self, list_id: str) -> bool:
        with self.get_session() as session:
            lst = session.get(ProspectList, list_id)
            if not lst:
                return False
            session.delete(lst)
            session.commit()
            return True

    # ── List Memberships ───────────────────────────────────────────────────

    def add_to_list(self, list_id: str, analysis_id: str) -> bool:
        with self.get_session() as session:
            lst = session.get(ProspectList, list_id)
            if not lst:
                return False
            job = session.get(AnalysisJob, analysis_id)
            if not job:
                return False
            # Check if membership already exists (idempotent)
            existing = session.execute(
                select(ProspectListMembership).where(
                    ProspectListMembership.list_id == list_id,
                    ProspectListMembership.analysis_id == analysis_id,
                )
            ).scalar_one_or_none()
            if existing:
                return True
            membership = ProspectListMembership(
                list_id=list_id,
                analysis_id=analysis_id,
                added_at=datetime.now(timezone.utc),
            )
            session.add(membership)
            lst.analysis_count += 1
            lst.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True

    def remove_from_list(self, list_id: str, analysis_id: str) -> bool:
        with self.get_session() as session:
            membership = session.execute(
                select(ProspectListMembership).where(
                    ProspectListMembership.list_id == list_id,
                    ProspectListMembership.analysis_id == analysis_id,
                )
            ).scalar_one_or_none()
            if not membership:
                return False
            session.delete(membership)
            lst = session.get(ProspectList, list_id)
            if lst and lst.analysis_count > 0:
                lst.analysis_count -= 1
                lst.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True

    def list_analyses_in_list(self, list_id: str) -> list[AnalysisRecord]:
        with self.get_session() as session:
            stmt = (
                select(AnalysisJob)
                .join(ProspectListMembership, AnalysisJob.id == ProspectListMembership.analysis_id)
                .where(ProspectListMembership.list_id == list_id)
                .order_by(ProspectListMembership.added_at.desc())
            )
            jobs = session.execute(stmt).scalars().all()
            return [self._to_record(j) for j in jobs]

    def list_lists_for_analysis(self, analysis_id: str) -> list[ProspectListRecord]:
        with self.get_session() as session:
            stmt = (
                select(ProspectList)
                .join(ProspectListMembership, ProspectList.id == ProspectListMembership.list_id)
                .where(ProspectListMembership.analysis_id == analysis_id)
                .order_by(ProspectList.created_at.desc())
            )
            lists = session.execute(stmt).scalars().all()
            return [self._to_list_record(l) for l in lists]

    # ── Internal helpers ───────────────────────────────────────────────────

    def _to_list_record(self, lst: ProspectList) -> ProspectListRecord:
        return ProspectListRecord(
            id=lst.id,
            name=lst.name,
            description=lst.description,
            analysis_count=lst.analysis_count,
            created_at=lst.created_at,
            updated_at=lst.updated_at,
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
