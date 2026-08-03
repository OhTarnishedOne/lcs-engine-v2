"""Tests for expired guest account cleanup."""

import asyncio
from datetime import datetime, timedelta, UTC

import pytest

from app.auth.demo import cleanup_expired_guests
from app.auth.utils import hash_password
from app.db.models import Strategy, User


def _create_expired_guest(db, *, with_strategy: bool = False):
    now = datetime.now(UTC)
    guest = User(
        email="guest-cleanup@test.com",
        password_hash=hash_password("guest-no-login"),
        tier="pro",
        is_guest=True,
        guest_created_at=now - timedelta(days=60),
        guest_expires_at=now - timedelta(days=35),
    )
    db.add(guest)
    db.flush()

    if with_strategy:
        db.add(
            Strategy(
                user_id=guest.id,
                name="Guest Strategy",
                description="Test",
                strategy_type="balanced",
                risk_level=3,
                time_horizon="medium",
                assets=[{"ticker": "SPY", "allocation_pct": 100}],
                rationale="Test",
                risks="Test",
            )
        )

    db.commit()
    return guest


@pytest.mark.asyncio
async def test_cleanup_deletes_expired_guest_without_strategy(db):
    guest = _create_expired_guest(db, with_strategy=False)

    deleted = await cleanup_expired_guests(db)

    assert deleted == 1
    assert db.query(User).filter(User.id == guest.id).first() is None


@pytest.mark.asyncio
async def test_cleanup_deletes_expired_guest_with_strategy(db):
    """Regression: ORM delete used to null strategies.user_id (NOT NULL)."""
    guest = _create_expired_guest(db, with_strategy=True)
    guest_id = guest.id

    deleted = await cleanup_expired_guests(db)

    assert deleted == 1
    assert db.query(User).filter(User.id == guest_id).first() is None
    assert db.query(Strategy).filter(Strategy.user_id == guest_id).first() is None


@pytest.mark.asyncio
async def test_cleanup_skips_active_guests(db):
    now = datetime.now(UTC)
    active = User(
        email="guest-active@test.com",
        password_hash=hash_password("guest-no-login"),
        tier="pro",
        is_guest=True,
        guest_created_at=now - timedelta(days=2),
        guest_expires_at=now + timedelta(days=3),
    )
    db.add(active)
    db.commit()

    deleted = await cleanup_expired_guests(db)

    assert deleted == 0
    assert db.query(User).filter(User.id == active.id).first() is not None
