from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Every model registers onto this `Base.metadata`, which Alembic autogenerate reads from."""
