"""
OPSIGHT database configuration.
Provides SQLAlchemy 2.0 engine, declarative Base, and session factory (Alembic-friendly).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default PostgreSQL URL; override via environment (e.g. DATABASE_URL) in production.
DATABASE_URL = "postgresql://localhost/opsight"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that yields a DB session; close after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
