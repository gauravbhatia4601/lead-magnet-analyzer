"""
Main FastAPI Application - Enterprise AI-Powered SEO/Conversion Analysis API
Integrates all services with structured responses for Next.js frontend
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import logging
import os
from contextlib import asynccontextmanager

import redis
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# FastAPI imports
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# Internal service imports
SCRAPER_BACKEND = "simple"
SCRAPER_WARNING: Optional[str] = None
try:
    from services import scraping_service as advanced_scraper

    if getattr(advanced_scraper, "PLAYWRIGHT_AVAILABLE", False):
        scrape_website_intelligent = advanced_scraper.scrape_website_intelligent
        ScrapingConfig = advanced_scraper.ScrapingConfig
        SCRAPER_BACKEND = "playwright"
    else:
        raise ImportError("Playwright backend unavailable")
except Exception as exc:
    from services.scraping_service_simple import scrape_website_intelligent, ScrapingConfig  # type: ignore
    SCRAPER_WARNING = f"Falling back to simplified scraper: {exc}"

from services.llm_analysis_service import (
    create_llm_analysis_service,
    ModelProvider,
    SEOScore,
    ConversionScore,
    DetailedRecommendation,
    ComprehensiveAnalysis,
)

from db import init_db
from db import get_async_session
from db.models import AnalysisHistory, AnalysisResult, AppSession
from services.persistence_service import (
    AnalysisCreate,
    AnalysisUpdate,
    HistorySummary,
    SessionCreate,
    SessionExtend,
    cleanup_expired_sessions,
    create_analysis as persist_create_analysis,
    create_session as persist_create_session,
    deactivate_session,
    delete_analysis as persist_delete_analysis,
    extend_session as persist_extend_session,
    get_analysis as persist_get_analysis,
    list_history as persist_list_history,
    touch_session as persist_touch_session,
)

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from services.security_service import SecurityService, User, UserTier, create_security_service
except ImportError:
    # Mock security service for testing
    SecurityService = None
    User = None
    UserTier = None
    create_security_service = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if SCRAPER_WARNING:
    logger.warning(SCRAPER_WARNING)
else:
    logger.info("Using %s scraper backend", SCRAPER_BACKEND)

# Global variables
redis_client = None
security_service = None
llm_service = None

SESSION_COOKIE_NAME = "magentix_session_id"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, security_service, llm_service
    
    # Initialize Redis
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=True
    )
    
    # Initialize security service
    jwt_secret = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-this-in-production')
    if create_security_service:
        security_service = create_security_service(redis_client, jwt_secret)
    else:
        security_service = None
        logger.warning("Security service not available - running in simplified mode")
    
    # Initialize database connectivity
    try:
        await init_db()
        logger.info("✅ Database connectivity verified")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Database initialization failed: %s", exc)
        raise

    # Initialize LLM service (auto-detects provider from environment)
    llm_service = create_llm_analysis_service()
    
    logger.info("✅ All services initialized successfully")
    yield
    
    # Cleanup
    if redis_client:
        redis_client.close()
    logger.info("🔄 Application shutdown complete")

# FastAPI app initialization
app = FastAPI(
    title="Magentix AI-Powered SEO/Conversion Analysis API",
    description="Enterprise-grade website analysis using AI and web scraping",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
default_cors_origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:9000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:9000",
]

allowed_origins_env = os.getenv("FRONTEND_ORIGINS")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    allowed_origins = default_cors_origins

logger.info("Configured CORS allow_origins: %s", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Pydantic models for API requests/responses
class AnalysisRequest(BaseModel):
    """Request model for website analysis"""
    url: HttpUrl = Field(..., description="Website URL to analyze")
    max_pages: int = Field(default=10, ge=1, le=50, description="Maximum pages to scrape")
    analysis_type: str = Field(
        default="comprehensive", 
        description="Type of analysis: 'comprehensive' (with AI), 'basic' (scraping only), or 'ai' (AI only if available)"
    )
    include_technical_seo: bool = Field(default=True, description="Include technical SEO analysis")
    include_competitor_insights: bool = Field(default=True, description="Include competitive insights")

class ScoreDetails(BaseModel):
    """Detailed scoring breakdown"""
    overall_score: int = Field(..., ge=0, le=100)
    title_optimization: int = Field(..., ge=0, le=100)
    meta_description: int = Field(..., ge=0, le=100)
    header_structure: int = Field(..., ge=0, le=100)
    content_quality: int = Field(..., ge=0, le=100)
    internal_linking: int = Field(..., ge=0, le=100)
    technical_seo: int = Field(..., ge=0, le=100)

class ConversionDetails(BaseModel):
    """Conversion optimization details"""
    overall_score: int = Field(..., ge=0, le=100)
    headline_effectiveness: int = Field(..., ge=0, le=100)
    value_proposition: int = Field(..., ge=0, le=100)
    cta_optimization: int = Field(..., ge=0, le=100)
    trust_signals: int = Field(..., ge=0, le=100)
    form_optimization: int = Field(..., ge=0, le=100)
    urgency_scarcity: int = Field(..., ge=0, le=100)

class RecommendationItem(BaseModel):
    """Individual recommendation"""
    id: str
    category: str
    priority: str  # "High", "Medium", "Low"
    title: str
    description: str
    implementation: str
    impact_score: int = Field(..., ge=1, le=10)
    estimated_effort: str  # "Low", "Medium", "High"
    expected_improvement: str

class AnalysisMetadata(BaseModel):
    """Analysis metadata"""

    model_config = ConfigDict(protected_namespaces=())

    analysis_id: str
    requested_url: str
    pages_analyzed: int
    pages_failed: int
    analysis_duration: float
    timestamp: datetime
    user_tier: str
    model_used: str

class AnalysisResponse(BaseModel):
    """Structured response for Next.js frontend"""
    success: bool
    metadata: AnalysisMetadata
    seo_analysis: ScoreDetails
    conversion_analysis: ConversionDetails
    recommendations: List[RecommendationItem]
    insights: Dict[str, Any]
    technical_issues: List[str]
    competitive_analysis: Dict[str, Any]
    summary: str

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    error_code: str
    timestamp: datetime
    request_id: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str


class SessionCreateRequest(BaseModel):
    """Request body for creating a new session."""

    ttl_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
        description="Session lifespan in minutes",
    )
    user_agent: Optional[str] = Field(
        default=None, description="Optional user agent override"
    )
    ip_address: Optional[str] = Field(
        default=None, description="Optional IP override"
    )


class SessionExtendRequest(BaseModel):
    """Request body for extending an existing session."""

    extend_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
        description="Additional minutes to add to the session",
    )
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class SessionResponse(BaseModel):
    """Session representation returned to clients."""

    session_id: str
    created_at: datetime
    expires_at: datetime
    last_accessed_at: datetime
    is_active: bool


def _session_to_response_model(session: AppSession) -> SessionResponse:
    """Transform a database session model into an API response."""

    return SessionResponse(
        session_id=session.id,
        created_at=_ensure_utc(session.created_at),
        expires_at=_ensure_utc(session.expires_at),
        last_accessed_at=_ensure_utc(session.last_accessed_at),
        is_active=session.is_active,
    )


class AnalysisHistoryEntryResponse(BaseModel):
    """History list item."""

    analysis_id: str
    session_id: str
    requested_url: str
    seo_overall_score: Optional[int] = None
    conversion_overall_score: Optional[int] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime


class AnalysisDetailResponse(BaseModel):
    """Detailed analysis payload."""

    model_config = ConfigDict(protected_namespaces=())

    analysis_id: str
    session_id: str
    requested_url: str
    analysis_type: str
    status: str
    model_used: Optional[str] = None
    analysis_duration_seconds: Optional[float] = None
    completed_at: Optional[datetime] = None
    seo_scores: Optional[Dict[str, Any]] = None
    conversion_scores: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    insights: Optional[Dict[str, Any]] = None
    technical_issues: Optional[List[str]] = None
    competitive_analysis: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    history: Optional[AnalysisHistoryEntryResponse] = None
    created_at: datetime
    updated_at: datetime


class AnalysisShareResponse(BaseModel):
    """Response for sharing an analysis."""

    share_url: str
    expires_at: datetime


def _ensure_utc(value: datetime) -> datetime:
    """Guarantee that a datetime is timezone-aware and in UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _history_entry_to_response(entry: AnalysisHistory) -> AnalysisHistoryEntryResponse:
    """Map a history ORM instance to API response form."""

    return AnalysisHistoryEntryResponse(
        analysis_id=entry.analysis_id,
        session_id=entry.session_id,
        requested_url=entry.requested_url,
        seo_overall_score=entry.seo_overall_score,
        conversion_overall_score=entry.conversion_overall_score,
        headline=entry.headline,
        summary=entry.summary,
        created_at=_ensure_utc(entry.created_at),
    )


def _analysis_to_detail_response(analysis: AnalysisResult) -> AnalysisDetailResponse:
    """Convert an AnalysisResult ORM model into a response payload."""

    history = (
        _history_entry_to_response(analysis.history_entry)
        if analysis.history_entry
        else None
    )

    return AnalysisDetailResponse(
        analysis_id=analysis.id,
        session_id=analysis.session_id,
        requested_url=analysis.requested_url,
        analysis_type=analysis.analysis_type,
        status=analysis.status,
        model_used=analysis.model_used,
        analysis_duration_seconds=analysis.analysis_duration_seconds,
        completed_at=_ensure_utc(analysis.completed_at)
        if analysis.completed_at
        else None,
        seo_scores=analysis.seo_scores,
        conversion_scores=analysis.conversion_scores,
        recommendations=analysis.recommendations,
        insights=analysis.insights,
        technical_issues=analysis.technical_issues,
        competitive_analysis=analysis.competitive_analysis,
        summary=analysis.summary,
        history=history,
        created_at=_ensure_utc(analysis.created_at),
        updated_at=_ensure_utc(analysis.updated_at)
        if analysis.updated_at
        else _ensure_utc(analysis.created_at),
    )


def _resolve_session_id(request: Request, session_id: Optional[str]) -> str:
    """Resolve session identifier from explicit input or session cookie."""

    if session_id:
        return session_id
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_value:
        return cookie_value
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session identifier missing",
    )


@app.post(
    "/session/create",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new anonymous session",
)
async def create_session_endpoint(
    payload: SessionCreateRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new session and issue a session cookie."""

    session_id = str(uuid.uuid4())
    user_agent = payload.user_agent or request.headers.get("user-agent")
    ip_address = payload.ip_address or (request.client.host if request.client else None)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=payload.ttl_minutes)

    session = await persist_create_session(
        db,
        SessionCreate(
            id=session_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        ),
    )

    max_age_seconds = payload.ttl_minutes * 60
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.id,
        max_age=max_age_seconds,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return _session_to_response_model(session)


@app.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    summary="Retrieve session details",
)
async def get_session_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """Return session details and update last accessed timestamp."""

    session = await db.get(AppSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await persist_touch_session(db, session_id)
    await db.refresh(session)
    return _session_to_response_model(session)


@app.put(
    "/session/{session_id}/extend",
    response_model=SessionResponse,
    summary="Extend an existing session",
)
async def extend_session_endpoint(
    session_id: str,
    payload: SessionExtendRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Extend the session expiration and optionally refresh metadata."""

    session = await db.get(AppSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    base_time = max(_ensure_utc(session.expires_at), datetime.now(timezone.utc))
    new_expiry = base_time + timedelta(minutes=payload.extend_minutes)
    user_agent = payload.user_agent or request.headers.get("user-agent") or session.user_agent
    ip_address = payload.ip_address or (request.client.host if request.client else session.ip_address)

    updated = await persist_extend_session(
        db,
        session_id,
        SessionExtend(
            expires_at=new_expiry,
            user_agent=user_agent,
            ip_address=ip_address,
        ),
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    max_age_seconds = payload.extend_minutes * 60
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=updated.id,
        max_age=max_age_seconds,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return _session_to_response_model(updated)


@app.get(
    "/analysis/history",
    response_model=List[AnalysisHistoryEntryResponse],
    summary="List stored analysis history for the current session",
)
async def list_analysis_history_endpoint(
    request: Request,
    session_id: Optional[str] = Query(None, description="Override session identifier"),
    db: AsyncSession = Depends(get_async_session),
):
    """Return stored analysis history for a session."""

    resolved_session_id = _resolve_session_id(request, session_id)
    session = await db.get(AppSession, resolved_session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await persist_touch_session(db, resolved_session_id)
    history_entries = await persist_list_history(db, resolved_session_id)
    return [_history_entry_to_response(entry) for entry in history_entries]


@app.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisDetailResponse,
    summary="Retrieve a stored analysis",
)
async def get_analysis_endpoint(
    analysis_id: str,
    request: Request,
    session_id: Optional[str] = Query(None, description="Override session identifier"),
    db: AsyncSession = Depends(get_async_session),
):
    """Return a previously stored analysis result."""

    resolved_session_id = _resolve_session_id(request, session_id)
    analysis = await persist_get_analysis(db, analysis_id, resolved_session_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return _analysis_to_detail_response(analysis)


@app.delete(
    "/analysis/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an analysis result",
)
async def delete_analysis_endpoint(
    analysis_id: str,
    request: Request,
    session_id: Optional[str] = Query(None, description="Override session identifier"),
    db: AsyncSession = Depends(get_async_session),
):
    """Remove a stored analysis."""

    resolved_session_id = _resolve_session_id(request, session_id)
    deleted = await persist_delete_analysis(db, analysis_id, resolved_session_id)
    if deleted == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/analysis/{analysis_id}/share",
    response_model=AnalysisShareResponse,
    summary="Generate a shareable link for an analysis",
)
async def share_analysis_endpoint(
    analysis_id: str,
    request: Request,
    session_id: Optional[str] = Query(None, description="Override session identifier"),
    db: AsyncSession = Depends(get_async_session),
):
    """Return a temporary share link for the requested analysis."""

    resolved_session_id = _resolve_session_id(request, session_id)
    analysis = await persist_get_analysis(db, analysis_id, resolved_session_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    base_url = str(request.base_url).rstrip("/")
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    share_url = f"{base_url}/share/{analysis_id}"
    return AnalysisShareResponse(share_url=share_url, expires_at=expires_at)

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> User:
    """Get current authenticated user"""
    if not security_service:
        # Return a mock user for testing when security service is not available
        from datetime import datetime
        return type('MockUser', (), {
            'user_id': 'test-user',
            'email': 'test@example.com',
            'tier': type('MockTier', (), {'value': 'premium'})(),
            'api_key': 'test-key',
            'created_at': datetime.utcnow(),
            'last_used': None,
            'is_active': True
        })()
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    return await security_service.authenticate_request(credentials)

async def validate_and_limit_request(request: Request, user: User = Depends(get_current_user)) -> User:
    """Validate request and check rate limits"""
    if not security_service:
        # Return a mock user for testing when security service is not available
        from datetime import datetime
        return type('MockUser', (), {
            'user_id': 'test-user',
            'email': 'test@example.com',
            'tier': type('MockTier', (), {'value': 'premium'})(),
            'api_key': 'test-key',
            'created_at': datetime.utcnow(),
            'last_used': None,
            'is_active': True
        })()
    
    client_ip = request.client.host
    if 'x-forwarded-for' in request.headers:
        client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()
    
    # Check rate limits
    await security_service.check_rate_limits(user, client_ip)
    
    # Increment counters
    await security_service.increment_rate_limits(user, client_ip)
    
    return user

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Magentix AI-Powered SEO/Conversion Analysis API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {}
    
    # Check Redis
    try:
        redis_client.ping()
        services_status["redis"] = "healthy"
    except Exception:
        services_status["redis"] = "unhealthy"
    
    # Check LLM service
    services_status["llm_service"] = "healthy" if llm_service else "unhealthy"
    
    # Check security service
    services_status["security_service"] = "healthy" if security_service else "unhealthy"
    
    overall_status = "healthy" if all(status == "healthy" for status in services_status.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services_status,
        version="2.0.0"
    )

@app.get("/user/limits", response_model=Dict[str, Any])
async def get_user_limits(user: User = Depends(get_current_user)):
    """Get user's current rate limit status"""
    return security_service.get_user_rate_limit_status(user)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_website(
    request_data: AnalysisRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    user: User = Depends(validate_and_limit_request),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Main website analysis endpoint
    Performs comprehensive SEO and conversion analysis
    """
    session_id = _resolve_session_id(request, request.query_params.get("session_id"))
    session = await db.get(AppSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await persist_touch_session(db, session_id)

    analysis_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        logger.info(f"Starting analysis {analysis_id} for URL: {request_data.url}")
        
        # Validate URL security
        if security_service:
            security_service.validate_url_security(str(request_data.url))
        else:
            # Simple URL validation when security service is not available
            if not str(request_data.url).startswith(('http://', 'https://')):
                raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Get user's tier limits
        if security_service:
            from services.security_service import RATE_LIMITS
            user_limits = RATE_LIMITS[user.tier]
            max_pages = min(request_data.max_pages, user_limits.max_pages_per_analysis)
        else:
            # Default limits when security service is not available; honor requested value within validation bounds
            max_pages = request_data.max_pages
        
        # Configure scraping
        scraping_config = ScrapingConfig(
            max_pages=max_pages,
            max_depth=3,
            delay_between_requests=1.0,
            respect_robots_txt=True
        )
        
        # Step 1: Scrape website
        logger.info(f"Step 1: Scraping website {request_data.url}")
        scraping_result = await scrape_website_intelligent(str(request_data.url), scraping_config)
        
        if not scraping_result['success'] or not scraping_result['pages']:
            raise HTTPException(
                status_code=400, 
                detail="Failed to scrape website or no content found"
            )
        
        # Step 2: LLM Analysis (if requested)
        analysis_result = None
        if request_data.analysis_type in ["comprehensive", "ai"]:
            logger.info(f"Step 2: Performing LLM analysis")
            analysis_result = await llm_service.analyze_website_comprehensive(scraping_result)
        else:
            logger.info(f"Step 2: Skipping LLM analysis (type: {request_data.analysis_type})")
        
        # Step 3: Format response
        analysis_duration = time.time() - start_time
        
        # If no LLM analysis, create basic analysis from scraping data
        if not analysis_result:
            analysis_result = await _create_basic_analysis_from_scraping(scraping_result)
        
        # Transform recommendations
        formatted_recommendations = []
        for i, rec in enumerate(analysis_result.recommendations):
            formatted_recommendations.append(RecommendationItem(
                id=f"rec_{i+1}",
                category=rec.category,
                priority=rec.priority,
                title=rec.issue,
                description=rec.recommendation,
                implementation=rec.implementation,
                impact_score=rec.impact_score,
                estimated_effort="Medium",  # Default, could be enhanced
                expected_improvement=f"{rec.impact_score * 10}% potential improvement"
            ))
        
        # Create comprehensive response
        response = AnalysisResponse(
            success=True,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                requested_url=str(request_data.url),
                pages_analyzed=scraping_result['pages_scraped'],
                pages_failed=scraping_result['pages_failed'],
                analysis_duration=round(analysis_duration, 2),
                timestamp=datetime.utcnow(),
                user_tier=user.tier.value,
                model_used=getattr(analysis_result, 'model_used', None) or "fallback-analysis"
            ),
            seo_analysis=ScoreDetails(
                overall_score=analysis_result.seo_score.overall_score,
                title_optimization=analysis_result.seo_score.title_optimization,
                meta_description=analysis_result.seo_score.meta_description,
                header_structure=analysis_result.seo_score.header_structure,
                content_quality=analysis_result.seo_score.content_quality,
                internal_linking=analysis_result.seo_score.internal_linking,
                technical_seo=analysis_result.seo_score.technical_seo
            ),
            conversion_analysis=ConversionDetails(
                overall_score=analysis_result.conversion_score.overall_score,
                headline_effectiveness=analysis_result.conversion_score.headline_effectiveness,
                value_proposition=analysis_result.conversion_score.value_proposition,
                cta_optimization=analysis_result.conversion_score.cta_optimization,
                trust_signals=analysis_result.conversion_score.trust_signals,
                form_optimization=analysis_result.conversion_score.form_optimization,
                urgency_scarcity=analysis_result.conversion_score.urgency_scarcity
            ),
            recommendations=formatted_recommendations,
            insights={
                "competitive_insights": analysis_result.competitive_insights,
                "content_gaps": analysis_result.content_gaps,
                "seo_keyword_insights": analysis_result.seo_keywords,
                "conversion_highlights": analysis_result.conversion_highlights,
                "pages_analyzed_details": [
                    {
                        "url": page.url,
                        "title": page.title,
                        "word_count": page.word_count,
                        "load_time": page.page_load_time
                    } for page in scraping_result['pages']
                ]
            },
            technical_issues=analysis_result.technical_issues,
            competitive_analysis={
                "market_position": "Analysis based on content structure and optimization patterns",
                "opportunities": analysis_result.competitive_insights[:3],
                "threats": ["Competitor sites may have better technical SEO", "Missing key conversion elements"]
            },
            summary=analysis_result.summary
        )
        
        # Log successful analysis
        if security_service:
            background_tasks.add_task(
                security_service.log_security_event,
                "analysis_completed",
                user.user_id,
                {
                    "analysis_id": analysis_id,
                    "url": str(request_data.url),
                    "pages_analyzed": scraping_result['pages_scraped'],
                    "duration": analysis_duration
                }
            )
        
        try:
            history_summary = HistorySummary(
                requested_url=response.metadata.requested_url,
                seo_overall_score=response.seo_analysis.overall_score,
                conversion_overall_score=response.conversion_analysis.overall_score,
                headline=response.recommendations[0].title if response.recommendations else None,
                summary=response.summary,
            )

            metadata_snapshot = {
                "analysis_id": response.metadata.analysis_id,
                "pages_analyzed": response.metadata.pages_analyzed,
                "pages_failed": response.metadata.pages_failed,
                "analysis_duration": response.metadata.analysis_duration,
                "user_tier": response.metadata.user_tier,
            }

            await persist_create_analysis(
                db,
                AnalysisCreate(
                    analysis_id=response.metadata.analysis_id,
                    session_id=session_id,
                    requested_url=response.metadata.requested_url,
                    analysis_type=request_data.analysis_type,
                    status="completed",
                    model_used=response.metadata.model_used,
                    metadata_snapshot=metadata_snapshot,
                    seo_scores=response.seo_analysis.model_dump(),
                    conversion_scores=response.conversion_analysis.model_dump(),
                    recommendations=[rec.model_dump() for rec in response.recommendations],
                    insights=response.insights,
                    technical_issues=response.technical_issues,
                    competitive_analysis=response.competitive_analysis,
                    summary=response.summary,
                    analysis_duration_seconds=response.metadata.analysis_duration,
                    completed_at=_ensure_utc(response.metadata.timestamp),
                    history=history_summary,
                ),
            )
        except Exception as persistence_error:  # pragma: no cover - defensive persistence path
            logger.exception("Failed to persist analysis %s: %s", analysis_id, persistence_error)

        logger.info(f"Analysis {analysis_id} completed successfully in {analysis_duration:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}")
        
        # Log error
        if security_service:
            background_tasks.add_task(
                security_service.log_security_event,
                "analysis_failed",
                user.user_id,
                {
                    "analysis_id": analysis_id,
                    "url": str(request_data.url),
                    "error": str(e)
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

async def _create_basic_analysis_from_scraping(scraping_result: Dict[str, Any]):
    """Create basic analysis from scraping data when LLM is not available"""
    
    # Basic scoring based on content analysis
    pages = scraping_result.get('pages', [])
    
    # Calculate basic scores
    seo_score = _calculate_basic_seo_score(pages)
    conversion_score = _calculate_basic_conversion_score(pages)
    
    # Generate basic recommendations
    recommendations = _generate_basic_recommendations(pages)
    
    # Basic insights
    competitive_insights = ["Analysis based on content structure (no AI processing)"]
    technical_issues = _identify_basic_technical_issues(pages)
    content_gaps = ["Create FAQ section", "Add testimonials", "Develop comparison pages"]
    
    summary = f"Basic analysis completed. SEO Score: {seo_score.overall_score}/100, Conversion Score: {conversion_score.overall_score}/100. No AI processing."
    
    return ComprehensiveAnalysis(
        seo_score=seo_score,
        conversion_score=conversion_score,
        recommendations=recommendations,
        competitive_insights=competitive_insights,
        technical_issues=technical_issues,
        content_gaps=content_gaps,
        summary=summary,
        analyzed_pages=scraping_result.get('pages_scraped', 0),
        analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
    )

def _calculate_basic_seo_score(pages: List[Any]) -> SEOScore:
    """Calculate basic SEO score from scraping data"""
    score = 50  # Base score
    
    for page in pages:
        # Title optimization
        if hasattr(page, 'title') and page.title:
            score += 5
        elif isinstance(page, dict) and page.get('title'):
            score += 5
        
        # Meta descriptions
        if hasattr(page, 'meta_description') and page.meta_description:
            score += 5
        elif isinstance(page, dict) and page.get('meta_description'):
            score += 5
        
        # Header structure
        if hasattr(page, 'h1_tags') and page.h1_tags:
            score += 3
        elif isinstance(page, dict) and page.get('h1_tags'):
            score += 3
        
        if hasattr(page, 'h2_tags') and page.h2_tags:
            score += 2
        elif isinstance(page, dict) and page.get('h2_tags'):
            score += 2
        
        # Content quality
        if hasattr(page, 'word_count') and page.word_count > 300:
            score += 3
        elif isinstance(page, dict) and page.get('word_count', 0) > 300:
            score += 3
        
        # Internal linking
        if hasattr(page, 'internal_links') and page.internal_links:
            score += 2
        elif isinstance(page, dict) and page.get('internal_links'):
            score += 2
    
    # Normalize score
    score = min(100, max(0, score))
    
    return SEOScore(
        overall_score=score,
        title_optimization=min(100, score + 10),
        meta_description=min(100, score + 5),
        header_structure=min(100, score + 15),
        content_quality=min(100, score + 10),
        internal_linking=min(100, score),
        technical_seo=min(100, score + 5)
    )

def _calculate_basic_conversion_score(pages: List[Any]) -> ConversionScore:
    """Calculate basic conversion score from scraping data"""
    score = 50  # Base score
    
    for page in pages:
        # CTA elements
        if hasattr(page, 'cta_elements') and page.cta_elements:
            score += 5
        elif isinstance(page, dict) and page.get('cta_elements'):
            score += 5
        
        # Forms
        if hasattr(page, 'forms') and page.forms:
            score += 4
        elif isinstance(page, dict) and page.get('forms'):
            score += 4
        
        # Content quality
        if hasattr(page, 'word_count') and page.word_count > 500:
            score += 3
        elif isinstance(page, dict) and page.get('word_count', 0) > 500:
            score += 3
        
        # Trust signals (contact/about pages)
        if hasattr(page, 'url') and ('contact' in page.url.lower() or 'about' in page.url.lower()):
            score += 3
        elif isinstance(page, dict) and ('contact' in page.get('url', '').lower() or 'about' in page.get('url', '').lower()):
            score += 3
    
    # Normalize score
    score = min(100, max(0, score))
    
    return ConversionScore(
        overall_score=score,
        headline_effectiveness=min(100, score + 10),
        value_proposition=min(100, score + 5),
        cta_optimization=min(100, score + 15),
        trust_signals=min(100, score + 10),
        form_optimization=min(100, score + 10),
        urgency_scarcity=min(100, score)
    )

def _generate_basic_recommendations(pages: List[Any]) -> List[DetailedRecommendation]:
    """Generate basic recommendations from scraping data"""
    
    recommendations = []
    
    # Check for missing meta descriptions
    has_meta_desc = any(
        (hasattr(page, 'meta_description') and page.meta_description) or
        (isinstance(page, dict) and page.get('meta_description'))
        for page in pages
    )
    
    if not has_meta_desc:
        recommendations.append(DetailedRecommendation(
            category="SEO",
            priority="High",
            issue="Missing meta descriptions",
            recommendation="Add compelling meta descriptions to all pages",
            implementation="Update HTML meta tags with unique descriptions",
            impact_score=8
        ))
    
    # Check for missing H1 tags
    has_h1 = any(
        (hasattr(page, 'h1_tags') and page.h1_tags) or
        (isinstance(page, dict) and page.get('h1_tags'))
        for page in pages
    )
    
    if not has_h1:
        recommendations.append(DetailedRecommendation(
            category="SEO",
            priority="High",
            issue="Missing H1 tags",
            recommendation="Add H1 tags to all pages",
            implementation="Include one H1 tag per page with main keyword",
            impact_score=7
        ))
    
    # Check for CTAs
    has_cta = any(
        (hasattr(page, 'cta_elements') and page.cta_elements) or
        (isinstance(page, dict) and page.get('cta_elements'))
        for page in pages
    )
    
    if not has_cta:
        recommendations.append(DetailedRecommendation(
            category="Conversion",
            priority="High",
            issue="Missing call-to-action elements",
            recommendation="Add clear CTAs throughout the site",
            implementation="Include buttons, links, or forms that guide users to take action",
            impact_score=9
        ))
    
    return recommendations

def _identify_basic_technical_issues(pages: List[Any]) -> List[str]:
    """Identify basic technical issues from scraping data"""
    issues = []
    
    # Check for missing meta descriptions
    has_meta_desc = any(
        (hasattr(page, 'meta_description') and page.meta_description) or
        (isinstance(page, dict) and page.get('meta_description'))
        for page in pages
    )
    
    if not has_meta_desc:
        issues.append("Missing meta descriptions")
    
    # Check for missing H1 tags
    has_h1 = any(
        (hasattr(page, 'h1_tags') and page.h1_tags) or
        (isinstance(page, dict) and page.get('h1_tags'))
        for page in pages
    )
    
    if not has_h1:
        issues.append("Missing H1 tags")
    
    # Check for content length
    total_words = sum(
        getattr(page, 'word_count', 0) if hasattr(page, 'word_count') else page.get('word_count', 0)
        for page in pages
    )
    
    if total_words < 300:
        issues.append("Content too short (less than 300 words)")
    
    return issues

@app.get("/analysis/{analysis_id}", response_model=Dict[str, Any])
async def get_analysis_result(
    analysis_id: str,
    user: User = Depends(get_current_user)
):
    """Get cached analysis result by ID"""
    # This would typically fetch from database
    # For now, return placeholder
    return {
        "message": "Analysis result retrieval not implemented yet",
        "analysis_id": analysis_id,
        "user_id": user.user_id
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    error_response = ErrorResponse(
        error=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
        timestamp=datetime.utcnow(),
        request_id=str(uuid.uuid4())
    )
    
    # Convert datetime to string for JSON serialization
    content = error_response.model_dump()
    content['timestamp'] = content['timestamp'].isoformat() if content['timestamp'] else None
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    
    error_response = ErrorResponse(
        error="Internal server error",
        error_code="INTERNAL_ERROR",
        timestamp=datetime.utcnow(),
        request_id=str(uuid.uuid4())
    )
    
    # Convert datetime to string for JSON serialization
    content = error_response.model_dump()
    content['timestamp'] = content['timestamp'].isoformat() if content['timestamp'] else None
    
    return JSONResponse(
        status_code=500,
        content=content
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
