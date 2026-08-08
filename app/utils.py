import uuid

from app.constants import ID_SUFFIX_LENGTH


def generate_id(prefix: str) -> str:
    """Builds an id like 'task_a1b2c3d4e5f6' — prefix + short random hex suffix."""
    return f"{prefix}_{uuid.uuid4().hex[:ID_SUFFIX_LENGTH]}"
