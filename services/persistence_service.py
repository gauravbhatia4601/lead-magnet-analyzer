"""Database persistence helpers for sessions and analyses."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import AnalysisHistory, AnalysisResult, AppSession


class SessionCreate(BaseModel):
    """Payload required to create a new anonymous session."""

    id: str = Field(..., description="Public session identifier")
    expires_at: datetime = Field(..., description="Expiration timestamp in UTC")
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class SessionExtend(BaseModel):
    """Payload to extend or reactivate a session."""

    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class HistorySummary(BaseModel):
    """Summary details stored for quick history lookups."""

    requested_url: str
    seo_overall_score: Optional[int] = None
    conversion_overall_score: Optional[int] = None
    headline: Optional[str] = None
    summary: Optional[str] = None


class AnalysisCreate(BaseModel):
    """Payload for creating a new analysis entry."""

    model_config = ConfigDict(protected_namespaces=())

    analysis_id: Optional[str] = None
    session_id: str
    requested_url: str
    analysis_type: str
    status: str = "pending"
    model_used: Optional[str] = None
    metadata_snapshot: Optional[dict[str, Any]] = None
    seo_scores: Optional[dict[str, Any]] = None
    conversion_scores: Optional[dict[str, Any]] = None
    recommendations: Optional[list[dict[str, Any]]] = None
    insights: Optional[dict[str, Any]] = None
    technical_issues: Optional[list[str]] = None
    competitive_analysis: Optional[dict[str, Any]] = None
    summary: Optional[str] = None
    analysis_duration_seconds: Optional[float] = None
    completed_at: Optional[datetime] = None
    history: Optional[HistorySummary] = None


class AnalysisUpdate(BaseModel):
    """Payload for updating an existing analysis entry."""

    model_config = ConfigDict(protected_namespaces=())

    status: Optional[str] = None
    model_used: Optional[str] = None
    metadata_snapshot: Optional[dict[str, Any]] = None
    seo_scores: Optional[dict[str, Any]] = None
    conversion_scores: Optional[dict[str, Any]] = None
    recommendations: Optional[list[dict[str, Any]]] = None
    insights: Optional[dict[str, Any]] = None
    technical_issues: Optional[list[str]] = None
    competitive_analysis: Optional[dict[str, Any]] = None
    summary: Optional[str] = None
    analysis_duration_seconds: Optional[float] = None
    completed_at: Optional[datetime] = None
    history: Optional[HistorySummary] = None


async def create_session(db: AsyncSession, payload: SessionCreate) -> AppSession:
    """Insert a new session or refresh an existing one."""

    existing = await db.get(AppSession, payload.id)
    if existing:
        existing.expires_at = payload.expires_at
        existing.user_agent = payload.user_agent or existing.user_agent
        existing.ip_address = payload.ip_address or existing.ip_address
        existing.is_active = True
        existing.last_accessed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing

    session = AppSession(
        id=payload.id,
        expires_at=payload.expires_at,
        user_agent=payload.user_agent,
        ip_address=payload.ip_address,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def extend_session(db: AsyncSession, session_id: str, payload: SessionExtend) -> Optional[AppSession]:
    """Extend session expiration and optionally update metadata."""

    session = await db.get(AppSession, session_id)
    if not session:
        return None

    session.expires_at = payload.expires_at
    if payload.user_agent:
        session.user_agent = payload.user_agent
    if payload.ip_address:
        session.ip_address = payload.ip_address
    session.is_active = True
    session.last_accessed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def touch_session(db: AsyncSession, session_id: str) -> None:
    """Update the last accessed timestamp if the session exists."""

    await db.execute(
        update(AppSession)
        .where(AppSession.id == session_id)
        .values(last_accessed_at=datetime.now(timezone.utc))
    )
    await db.commit()


async def deactivate_session(db: AsyncSession, session_id: str) -> None:
    """Soft deactivate a session without deleting its history."""

    await db.execute(
        update(AppSession)
        .where(AppSession.id == session_id)
        .values(is_active=False, last_accessed_at=datetime.now(timezone.utc))
    )
    await db.commit()


async def create_analysis(db: AsyncSession, payload: AnalysisCreate) -> AnalysisResult:
    """Persist an analysis result and optional history summary."""

    analysis = AnalysisResult(
        id=payload.analysis_id or str(uuid.uuid4()),
        session_id=payload.session_id,
        requested_url=payload.requested_url,
        analysis_type=payload.analysis_type,
        status=payload.status,
        model_used=payload.model_used,
        metadata_snapshot=payload.metadata_snapshot,
        seo_scores=payload.seo_scores,
        conversion_scores=payload.conversion_scores,
        recommendations=payload.recommendations,
        insights=payload.insights,
        technical_issues=payload.technical_issues,
        competitive_analysis=payload.competitive_analysis,
        summary=payload.summary,
        analysis_duration_seconds=payload.analysis_duration_seconds,
        completed_at=payload.completed_at,
    )
    db.add(analysis)
    await db.flush()

    if payload.history:
        history = AnalysisHistory(
            session_id=payload.session_id,
            analysis_id=analysis.id,
            requested_url=payload.history.requested_url,
            seo_overall_score=payload.history.seo_overall_score,
            conversion_overall_score=payload.history.conversion_overall_score,
            headline=payload.history.headline,
            summary=payload.history.summary,
        )
        db.add(history)

    await db.commit()
    await db.refresh(analysis)
    return analysis


async def update_analysis(
    db: AsyncSession,
    analysis_id: str,
    session_id: str,
    payload: AnalysisUpdate,
) -> Optional[AnalysisResult]:
    """Update an existing analysis belonging to a session."""

    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.history_entry))
        .where(
            AnalysisResult.id == analysis_id,
            AnalysisResult.session_id == session_id,
        )
    )
    analysis = result.scalars().first()
    if not analysis:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "history":
            continue
        setattr(analysis, field, value)

    if payload.history:
        history = analysis.history_entry
        if history:
            history.requested_url = payload.history.requested_url
            history.seo_overall_score = payload.history.seo_overall_score
            history.conversion_overall_score = payload.history.conversion_overall_score
            history.headline = payload.history.headline
            history.summary = payload.history.summary
        else:
            history = AnalysisHistory(
                session_id=session_id,
                analysis_id=analysis.id,
                requested_url=payload.history.requested_url,
                seo_overall_score=payload.history.seo_overall_score,
                conversion_overall_score=payload.history.conversion_overall_score,
                headline=payload.history.headline,
                summary=payload.history.summary,
            )
            db.add(history)

    analysis.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(analysis)
    return analysis


async def delete_analysis(db: AsyncSession, analysis_id: str, session_id: str) -> int:
    """Delete an analysis and associated history for a session."""

    await db.execute(
        delete(AnalysisHistory)
        .where(
            AnalysisHistory.analysis_id == analysis_id,
            AnalysisHistory.session_id == session_id,
        )
    )

    result = await db.execute(
        delete(AnalysisResult)
        .where(
            AnalysisResult.id == analysis_id,
            AnalysisResult.session_id == session_id,
        )
        .execution_options(synchronize_session="fetch")
    )
    await db.commit()
    return result.rowcount or 0


async def get_analysis(
    db: AsyncSession, analysis_id: str, session_id: str
) -> Optional[AnalysisResult]:
    """Fetch a specific analysis with eager loaded relationships."""

    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.history_entry))
        .where(
            AnalysisResult.id == analysis_id,
            AnalysisResult.session_id == session_id,
        )
    )
    return result.scalars().first()


async def list_history(db: AsyncSession, session_id: str) -> Sequence[AnalysisHistory]:
    """Return history entries in reverse chronological order."""

    result = await db.execute(
        select(AnalysisHistory)
        .where(AnalysisHistory.session_id == session_id)
        .order_by(AnalysisHistory.created_at.desc())
    )
    return result.scalars().all()


async def cleanup_expired_sessions(db: AsyncSession, limit: int = 500) -> int:
    """Remove expired sessions and cascade-delete their analyses."""

    now = datetime.now(timezone.utc)
    subquery = (
        select(AppSession.id)
        .where(AppSession.expires_at < now)
        .limit(limit)
    )
    result = await db.execute(
        delete(AppSession)
        .where(AppSession.id.in_(subquery))
        .execution_options(synchronize_session=False)
    )
    await db.commit()
    return result.rowcount or 0
