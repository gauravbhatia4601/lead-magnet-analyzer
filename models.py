"""
Database models for Lead Magnet Analyzer
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User model for storing user information and API keys"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    plan = Column(String(20), default="free", nullable=False)  # free, pro, agency
    analyses_count = Column(Integer, default=0, nullable=False)
    last_analysis_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', plan='{self.plan}')>"

    @property
    def is_free_tier(self):
        return self.plan == "free"

    @property
    def can_analyze(self):
        """Check if user can perform analysis based on their plan"""
        if self.plan in ["pro", "agency"]:
            return True
        # Free tier: 10 analyses per month
        return self.analyses_count < 10


class Analysis(Base):
    """Analysis model for storing website analysis results"""

    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    url = Column(String(2048), nullable=False, index=True)
    status = Column(
        String(20), default="processing", nullable=False
    )  # processing, completed, failed
    score = Column(Integer, nullable=True)
    pages_scanned = Column(Integer, nullable=True)
    breakdown = Column(JSON, nullable=True)
    error_message = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    is_public = Column(Integer, default=1, nullable=False)  # 1=public, 0=private
    result_file = Column(String(255), nullable=True)
    shares_count = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<Analysis(id='{self.id}', url='{self.url}', status='{self.status}', score={self.score})>"

    @property
    def is_completed(self):
        return self.status == "completed"

    @property
    def is_failed(self):
        return self.status == "failed"

    @property
    def is_processing(self):
        return self.status == "processing"

    def mark_completed(self, score, pages_scanned, breakdown, result_file):
        """Mark analysis as completed with results"""
        self.status = "completed"
        self.score = score
        self.pages_scanned = pages_scanned
        self.breakdown = breakdown
        self.result_file = result_file
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message):
        """Mark analysis as failed with error message"""
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def increment_shares(self):
        """Increment share count (for viral tracking)"""
        self.shares_count += 1


class EmailSubscriber(Base):
    """Email subscribers for marketing and drip campaigns"""

    __tablename__ = "email_subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    source = Column(
        String(50), nullable=True
    )  # landing_page, after_analysis, chrome_extension
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_subscribed = Column(Integer, default=1, nullable=False)  # 1=subscribed, 0=unsubscribed
    first_analysis_id = Column(String(36), nullable=True)

    def __repr__(self):
        return f"<EmailSubscriber(id={self.id}, email='{self.email}', source='{self.source}')>"
