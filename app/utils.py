"""Purpose: small standalone helpers shared across models — currently just
ID generation. Anything here must have no dependency on the DB, config, or
any single model, or it belongs somewhere more specific instead.
"""

import uuid

from app.constants import ID_SUFFIX_LENGTH


def generate_id(prefix: str) -> str:
    """Build an id like 'task_a1b2c3d4e5f6' — a human-readable prefix plus a
    short random hex suffix. Used as the default primary key for every
    entity so ids are self-describing in logs and API responses.
    """
    return f"{prefix}_{uuid.uuid4().hex[:ID_SUFFIX_LENGTH]}"
