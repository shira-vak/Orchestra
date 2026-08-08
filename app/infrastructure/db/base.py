"""Purpose: shared SQLAlchemy declarative base every ORM model inherits from."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Every model registers onto this `Base.metadata`, which Alembic autogenerate reads from."""
