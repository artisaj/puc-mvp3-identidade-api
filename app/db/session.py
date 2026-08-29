"""Engine e sessão do banco de dados."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Session:
    """Fornece uma sessão e assegura seu fechamento após a requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
