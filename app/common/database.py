from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.common.config import settings

# Database URL construction
DATABASE_URL = f"mysql+pymysql://{settings.database.username}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.database}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=settings.api.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models - enables flexibility for schema changes
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables - for development use"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables - for development use"""
    Base.metadata.drop_all(bind=engine)