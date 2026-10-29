"""
database.py
SQLAlchemy Database setup for SQLite (default) or configurable PostgreSQL/MySQL.
Provides session generator and DeclarativeBase.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "burnout_system.db")

# Default SQLite database URL with check_same_thread=False for FastAPI concurrency
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency for database session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
