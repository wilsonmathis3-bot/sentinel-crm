from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine, Base
from app.auth import get_current_active_user
from app.routers import contacts, deals, tasks, dashboard, agents, nli, auth

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sentinel CRM", version="1.0.0")

# CORS - allow all origins in production (Railway) or localhost for dev
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "https://localhost:3000",
]

# Add Railway domains if in production
if os.getenv("RAILWAY_STATIC_URL"):
    origins.append(os.getenv("RAILWAY_STATIC_URL"))
if os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    origins.append(f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "production" else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def root():
    return {"message": "Sentinel CRM API", "version": "1.0.0", "auth": "JWT + Passkey enabled", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
