"""Explicit conversions between User.id (str) and gamification user_id columns."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import String, TypeDecorator


class GamificationUserIdType(TypeDecorator):
    """
    users.id is String(36) on all dialects; gamification FK columns must match.
  """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return uuid_to_user_id(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return user_id_to_uuid(value)


def user_id_to_uuid(user_id: str | UUID) -> UUID:
    """Convert a users.id string (or UUID) to a gamification UUID."""
    if isinstance(user_id, UUID):
        return user_id
    return UUID(str(user_id))


def uuid_to_user_id(value: str | UUID) -> str:
    """Convert a gamification UUID (or string) to users.id format."""
    return str(value)
