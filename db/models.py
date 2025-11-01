"""ORM models for Magentix persistence."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class AppSession(Base):
    """Represents an anonymous user session tracked via cookies."""

    __tablename__ = "app_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    analyses: Mapped[List["AnalysisResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    history_entries: Mapped[List["AnalysisHistory"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    """Stores the detailed payload returned by the analysis pipeline."""

    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("app_sessions.id", ondelete="CASCADE"), nullable=False
    )
    requested_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    analysis_duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    model_used: Mapped[Optional[str]] = mapped_column(String(128))
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    seo_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    conversion_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    recommendations: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    insights: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    technical_issues: Mapped[Optional[List[str]]] = mapped_column(JSON)
    competitive_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped[AppSession] = relationship(back_populates="analyses")
    history_entry: Mapped[Optional["AnalysisHistory"]] = relationship(
        back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )


class AnalysisHistory(Base):
    """Lightweight index of analysis runs for rapid history queries."""

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("app_sessions.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_results.id", ondelete="CASCADE"), unique=True
    )
    requested_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    seo_overall_score: Mapped[Optional[int]] = mapped_column(Integer)
    conversion_overall_score: Mapped[Optional[int]] = mapped_column(Integer)
    headline: Mapped[Optional[str]] = mapped_column(String(256))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    analysis: Mapped[AnalysisResult] = relationship(back_populates="history_entry")
    session: Mapped[AppSession] = relationship(back_populates="history_entries")
