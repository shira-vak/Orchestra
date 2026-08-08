"""Purpose: defines the shared SQLAlchemy declarative base every ORM model
inherits from."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base.

    Every ORM model inherits from this so they all register onto the same
    `Base.metadata` object — that single metadata object is what Alembic
    reads from to autogenerate migrations, and what a test fixture reads
    from to know which tables should exist.
    """
