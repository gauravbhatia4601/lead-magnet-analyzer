"""
FastAPI application for Lead Magnet Analyzer with viral growth features
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Form
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError
import os
import time
import uuid
import secrets
from datetime import datetime
from typing import Optional

from main import analyze_full_site, plot_results
from database import get_db, init_db
from models import User, Analysis, EmailSubscriber

# Initialize FastAPI app
app = FastAPI(
    title="Lead Magnet Analyzer API",
    description="Analyze websites for lead magnet effectiveness",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("🚀 Lead Magnet Analyzer API started successfully")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

# Templates
templates = Jinja2Templates(directory="templates")

# API Key authentication (simple approach for now)
API_KEY = os.environ.get("API_KEY", "secret")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def verify_key(key: Optional[str] = Depends(api_key_header)):
    """Verify API key for authenticated endpoints"""
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return key


def get_or_create_anonymous_user(db: Session) -> User:
    """Get or create anonymous user for free-tier analyses"""
    anonymous_email = "anonymous@leadmagnetanalyzer.com"

    user = db.query(User).filter(User.email == anonymous_email).first()

    if not user:
        user = User(
            email=anonymous_email,
            api_key=secrets.token_urlsafe(32),
            plan="free"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def run_analysis_background(analysis_id: str, url: str, db_session: Session = None):
    """
    Background task to run website analysis
    This runs asynchronously so the user gets immediate response
    """
    from database import SessionLocal

    db = db_session or SessionLocal()

    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

        if not analysis:
            print(f"❌ Analysis {analysis_id} not found")
            return

        print(f"🔍 Starting analysis for {url}")

        # Run the analysis
        total_score, breakdown, pages_scanned = analyze_full_site(url)

        # Generate result file
        os.makedirs("results", exist_ok=True)
        file_name = f"analysis_{analysis_id}.png"
        file_path = os.path.join("results", file_name)

        plot_results(
            breakdown,
            total_score,
            pages_scanned,
            url,
            output_file=file_path,
            show=False
        )

        # Update analysis record
        analysis.mark_completed(total_score, pages_scanned, breakdown, file_name)

        # Update user's analysis count
        if analysis.user_id:
            user = db.query(User).filter(User.id == analysis.user_id).first()
            if user:
                user.analyses_count += 1
                user.last_analysis_at = datetime.utcnow()

        db.commit()

        print(f"✅ Analysis {analysis_id} completed: Score {total_score}/{pages_scanned*9}")

    except Exception as e:
        print(f"❌ Analysis {analysis_id} failed: {str(e)}")

        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.mark_failed(str(e))
            db.commit()

    finally:
        if not db_session:
            db.close()


# ============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, db: Session = Depends(get_db), compare: Optional[str] = None):
    """Landing page with URL input"""
    # Get recent public analyses for social proof
    recent_analyses = db.query(Analysis).filter(
        Analysis.status == "completed",
        Analysis.is_public == 1
    ).order_by(Analysis.created_at.desc()).limit(6).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_analyses": recent_analyses,
        "compare_url": compare
    })


@app.post("/api/analyze-async")
async def analyze_async(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Start website analysis asynchronously (no auth required for free tier)
    Returns immediately with analysis_id, analysis runs in background
    """
    # Validate URL
    if not url.startswith("http"):
        url = "https://" + url

    # Get or create anonymous user
    user = get_or_create_anonymous_user(db)

    # Check if user can analyze (free tier limit)
    if not user.can_analyze:
        raise HTTPException(
            status_code=429,
            detail=f"Free tier limit reached. You've used {user.analyses_count}/10 analyses this month. Upgrade to Pro for unlimited analyses."
        )

    # Create analysis record
    analysis_id = str(uuid.uuid4())
    analysis = Analysis(
        id=analysis_id,
        user_id=user.id,
        url=url,
        status="processing",
        is_public=1  # Free tier analyses are always public (viral mechanic)
    )

    db.add(analysis)
    db.commit()

    # Start background analysis
    background_tasks.add_task(run_analysis_background, analysis_id, url)

    return {
        "analysis_id": analysis_id,
        "status": "processing",
        "report_url": f"/report/{analysis_id}",
        "message": "Analysis started. You'll be redirected to the report page."
    }


@app.get("/report/{analysis_id}", response_class=HTMLResponse)
async def get_report(analysis_id: str, request: Request, db: Session = Depends(get_db)):
    """Public report page - no authentication required (viral feature)"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # If still processing, show processing page
    if analysis.is_processing:
        return templates.TemplateResponse("processing.html", {
            "request": request,
            "analysis": analysis
        })

    # If failed, show error
    if analysis.is_failed:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {analysis.error_message}")

    # Show completed report
    return templates.TemplateResponse("report.html", {
        "request": request,
        "analysis": analysis
    })


@app.post("/api/track-share/{analysis_id}")
async def track_share(analysis_id: str, db: Session = Depends(get_db)):
    """Track when a report is shared (for viral metrics)"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if analysis:
        analysis.increment_shares()
        db.commit()
        return {"success": True, "shares_count": analysis.shares_count}

    return {"success": False}


@app.post("/subscribe")
async def subscribe_email(
    email: str = Form(...),
    source: str = Form("landing_page"),
    analysis_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Email subscription endpoint
    Captures emails for marketing and creates user accounts
    """
    # Validate email
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email address")

    # Check if email already exists
    existing_subscriber = db.query(EmailSubscriber).filter(
        EmailSubscriber.email == email
    ).first()

    if not existing_subscriber:
        # Create new subscriber
        subscriber = EmailSubscriber(
            email=email,
            source=source,
            first_analysis_id=analysis_id
        )
        db.add(subscriber)

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user
        user = User(
            email=email,
            api_key=secrets.token_urlsafe(32),
            plan="free"
        )
        db.add(user)

    db.commit()

    # TODO: Send welcome email via SendGrid/Mailgun

    return {
        "success": True,
        "message": "Thanks for subscribing! Check your email for your API key.",
        "api_key": user.api_key if user else None
    }


@app.get("/badge/{analysis_id}.svg")
async def get_badge(analysis_id: str, db: Session = Depends(get_db)):
    """
    Generate SVG badge for embedding
    Example: <img src="/badge/abc123.svg" />
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis or not analysis.is_completed:
        raise HTTPException(status_code=404, detail="Analysis not found")

    score = analysis.score
    max_score = 9  # Maximum possible score

    # Determine color based on score
    if score >= 7:
        color = "#10b981"  # Green
    elif score >= 5:
        color = "#3b82f6"  # Blue
    elif score >= 3:
        color = "#f59e0b"  # Orange
    else:
        color = "#ef4444"  # Red

    svg = f'''<svg width="200" height="80" xmlns="http://www.w3.org/2000/svg">
  <rect fill="{color}" width="200" height="80" rx="8"/>
  <text x="100" y="30" text-anchor="middle" fill="white" font-size="14" font-family="Arial, sans-serif">
    Lead Magnet Score
  </text>
  <text x="100" y="60" text-anchor="middle" fill="white" font-size="28" font-weight="bold" font-family="Arial, sans-serif">
    {score}/{max_score}
  </text>
</svg>'''

    return Response(content=svg, media_type="image/svg+xml")


# ============================================================================
# AUTHENTICATED API ENDPOINTS (Require API key)
# ============================================================================

@app.post("/analyze")
def analyze(url: str, key: str = Depends(verify_key), db: Session = Depends(get_db)):
    """
    Legacy synchronous analysis endpoint (for backward compatibility)
    Requires API key authentication
    """
    total_score, breakdown, pages_scanned = analyze_full_site(url)

    os.makedirs("results", exist_ok=True)
    file_name = f"analysis_{int(time.time())}.png"
    file_path = os.path.join("results", file_name)

    plot_results(
        breakdown, total_score, pages_scanned, url, output_file=file_path, show=False
    )

    return {
        "total_score": total_score,
        "pages_scanned": pages_scanned,
        "score_breakdown": breakdown,
        "result_file": file_name,
    }


@app.get("/files/{file_name}")
def get_file(file_name: str):
    """Serve result image files (public access for shareable reports)"""
    file_path = os.path.join("results", file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="image/png", filename=file_name)


@app.get("/api/analyses")
def get_user_analyses(
    key: str = Depends(verify_key),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get user's analysis history (requires authentication)"""
    user = db.query(User).filter(User.api_key == key).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    analyses = db.query(Analysis).filter(
        Analysis.user_id == user.id
    ).order_by(Analysis.created_at.desc()).limit(limit).all()

    return {
        "user": {
            "email": user.email,
            "plan": user.plan,
            "analyses_count": user.analyses_count
        },
        "analyses": [
            {
                "id": a.id,
                "url": a.url,
                "status": a.status,
                "score": a.score,
                "created_at": a.created_at,
                "report_url": f"/report/{a.id}"
            }
            for a in analyses
        ]
    }


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Public stats endpoint for social proof"""
    total_analyses = db.query(Analysis).filter(Analysis.status == "completed").count()
    total_users = db.query(User).count()

    return {
        "total_analyses": total_analyses,
        "total_users": total_users,
        "total_pages_scanned": total_analyses * 10  # Approximate
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
