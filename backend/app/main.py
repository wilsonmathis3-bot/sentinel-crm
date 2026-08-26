from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import engine, Base
from app.auth import get_current_active_user
from app.routers import contacts, deals, tasks, dashboard, agents, nli, auth, import_contacts, ops, creator

# Create tables
Base.metadata.create_all(bind=engine)

_prod = os.getenv("ENVIRONMENT") == "production"
_docs_on = (not _prod) or os.getenv("ENABLE_DOCS") == "true"
app = FastAPI(
    title="Sentinel CRM",
    version="1.0.0",
    docs_url="/docs" if _docs_on else None,
    openapi_url="/openapi.json" if _docs_on else None,
)

# CORS - explicit allowlist only (never wildcard)
_default_origins = "http://localhost:3000,http://localhost:5173,https://crm-web-production-7065.up.railway.app"
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers on every response
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# Auth routes (public)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# Protected routes
app.include_router(
    contacts.router,
    prefix="/api/contacts",
    tags=["contacts"],
    dependencies=[Depends(get_current_active_user)]
)
app.include_router(
    deals.router,
    prefix="/api/deals",
    tags=["deals"],
    dependencies=[Depends(get_current_active_user)]
)
app.include_router(
    tasks.router,
    prefix="/api/tasks",
    tags=["tasks"],
    dependencies=[Depends(get_current_active_user)]
)
app.include_router(
    dashboard.router,
    prefix="/api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_active_user)]
)
app.include_router(
    agents.router,
    prefix="/api/agents",
    tags=["agents"],
    dependencies=[Depends(get_current_active_user)]
)
app.include_router(
    nli.router,
    prefix="/api/nli",
    tags=["nli"],
    dependencies=[Depends(get_current_active_user)]
)
app.include_router(
    ops.router,
    prefix="/api/ops",
    tags=["ops"],
    dependencies=[Depends(get_current_active_user)]
)

app.include_router(
    creator.router,
    prefix="/api/creator",
    tags=["creator"],
    dependencies=[Depends(get_current_active_user)]
)

@app.get("/")
def root():
    return {"message": "Sentinel CRM API", "version": "1.0.0", "auth": "JWT + Passkey enabled", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

app.include_router(
    import_contacts.router,
    prefix="/api/contacts",
    tags=["import"],
    dependencies=[Depends(get_current_active_user)]
)

# ---------------------------------------------------------------------------
# Startup: APScheduler with EOD sweep
# ---------------------------------------------------------------------------
_scheduler = None

@app.on_event("startup")
def startup_event():
    global _scheduler
    _scheduler = BackgroundScheduler()
    # EOD sweep: daily at 17:00 America/Los_Angeles
    _scheduler.add_job(
        _run_eod_sweep_job,
        "cron",
        hour=17,
        minute=0,
        timezone="America/Los_Angeles",
        id="eod_sweep_job",
        replace_existing=True
    )
    _scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()

def _run_eod_sweep_job():
    """Wrapper to run async sweep in sync scheduler context."""
    from app.database import SessionLocal
    from app.ops.eod_sweep import run_eod_sweep
    db = SessionLocal()
    try:
        asyncio.run(run_eod_sweep(db))
    finally:
        db.close()
