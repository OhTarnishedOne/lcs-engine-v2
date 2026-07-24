"""Explicit conversions between User.id (str) and gamification UUID columns."""

from __future__ import annotations

from uuid import UUID


def user_id_to_uuid(user_id: str | UUID) -> UUID:
    """Convert a users.id string (or UUID) to a gamification UUID."""
    if isinstance(user_id, UUID):
        return user_id
    return UUID(str(user_id))


def uuid_to_user_id(value: str | UUID) -> str:
    """Convert a gamification UUID (or string) to users.id format."""
    return str(value)
