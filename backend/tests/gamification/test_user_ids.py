"""Tests for User.id <-> gamification UUID conversion helpers."""

from uuid import UUID, uuid4

import pytest

from app.gamification.user_ids import user_id_to_uuid, uuid_to_user_id


class TestUserIdConversion:

    def test_user_id_string_round_trip(self):
        raw = str(uuid4())
        assert uuid_to_user_id(user_id_to_uuid(raw)) == raw

    def test_uuid_passthrough(self):
        value = uuid4()
        assert user_id_to_uuid(value) is value
        assert user_id_to_uuid(value) == value

    def test_uuid_to_user_id_from_string(self):
        raw = str(uuid4())
        assert uuid_to_user_id(raw) == raw

    def test_invalid_user_id_raises(self):
        with pytest.raises(ValueError):
            user_id_to_uuid("not-a-uuid")
