"""
Database configuration and session management
"""

import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finwave:finwave@localhost:5432/finwave"
)

# Handle different database types
if DATABASE_URL.startswith("postgres://"):
    # Handle Heroku-style postgres:// URLs
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
elif DATABASE_URL.startswith("duckdb://"):
    # DuckDB support for development
    # Format: duckdb:///path/to/file.duckdb or duckdb:///:memory:
    pass  # SQLAlchemy handles this natively
elif DATABASE_URL.startswith("sqlite://"):
    # SQLite support for development
    pass  # SQLAlchemy handles this natively

# Create engine with appropriate settings for each database type
if DATABASE_URL.startswith("sqlite://"):
    # SQLite doesn't support these pool settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
else:
    # PostgreSQL/DuckDB settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get DB session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for scripts and non-FastAPI code
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Initialize database tables
    """
    # Import all models to register them
    from models.workspace import Base as WorkspaceBase
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DATABASE_URL}")

def drop_db():
    """
    Drop all database tables (use with caution!)
    """
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped")