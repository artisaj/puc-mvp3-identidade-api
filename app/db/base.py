"""Base declarativa compartilhada pelos modelos ORM."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base para os modelos SQLAlchemy."""
