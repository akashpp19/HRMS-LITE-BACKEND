from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Supports both PostgreSQL and SQLite.
# For local dev without Postgres, use:  DATABASE_URL=sqlite:///./hrms.db
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./hrms.db",   # local fallback → creates hrms.db next to main.py
)

# Render/Railway may return "postgres://" — SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_is_sqlite      = DATABASE_URL.startswith("sqlite")
_is_serverless  = bool(os.getenv("VERCEL") or os.getenv("VERCEL_URL"))

if _is_sqlite:
    # SQLite: disallow multi-thread check so FastAPI threads can share the session
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
elif _is_serverless:
    from sqlalchemy.pool import NullPool
    engine = create_engine(DATABASE_URL, poolclass=NullPool, pool_pre_ping=True)
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
