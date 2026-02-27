from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from .database import engine, Base
from .routers import employees, attendance, dashboard, seed

load_dotenv()

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HRMS Lite API",
    description="Human Resource Management System – Employee & Attendance Management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: allow all origins by default; set CORS_ORIGINS in env for production
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
if cors_origins_raw == "*":
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],  # credentials not allowed with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(dashboard.router)
app.include_router(seed.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "HRMS Lite API v2",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "healthy", "version": "2.0.0"}
