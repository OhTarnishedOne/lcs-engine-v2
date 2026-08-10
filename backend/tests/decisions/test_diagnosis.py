"""
Sprint 4 — rules-based diagnosis.

Unit tests for the deterministic detectors + API tests for the diagnosis
endpoint (building state and an active overconfidence diagnosis).
"""

import uuid
from types import SimpleNamespace

from app.db.models import User
from app.gamification.user_ids import user_id_to_uuid
from app.services.diagnostics.bias_detector import (
    detect_fifty_fifty_clustering,
    detect_overconfidence,
    detect_reflection_avoidance,
    detect_weak_falsification,
    detect_weak_process,
)


def _d(confidence, outcome=None, falsification="if X"):
    return SimpleNamespace(
        confidence=confidence, outcome_binary=outcome, falsification=falsification
    )


# --------------------------------------------------------------------------- detectors

class TestOverconfidence:
    def test_flags_high_conviction_misses(self):
        # 4 high-conviction calls, 2 wrong-direction -> 50% miss rate.
        resolved = [
            _d(0.9, True),
            _d(0.9, False),   # miss
            _d(0.85, False),  # miss
            _d(0.8, True),
        ]
        signal = detect_overconfidence(resolved)
        assert signal is not None
        assert signal.slug == "overconfidence"
        assert signal.metric["high_conviction_miss_rate"] == 0.5

    def test_low_side_miss_counts(self):
        # Confident it WON'T happen (<=0.25) but it did -> miss.
        resolved = [_d(0.1, True), _d(0.1, True), _d(0.15, True)]
        signal = detect_overconfidence(resolved)
        assert signal is not None
        assert signal.metric["high_conviction_miss_rate"] == 1.0

    def test_not_flagged_when_accurate(self):
        resolved = [_d(0.9, True), _d(0.9, True), _d(0.85, True), _d(0.8, True)]
        assert detect_overconfidence(resolved) is None

    def test_ignored_below_min_high_conviction(self):
        resolved = [_d(0.9, False), _d(0.6, True)]  # only 1 high-conviction
        assert detect_overconfidence(resolved) is None


class TestFiftyFifty:
    def test_flags_clustering(self):
        resolved = [_d(0.5, True), _d(0.55, False), _d(0.45, True), _d(0.5, True), _d(0.9, True)]
        signal = detect_fifty_fifty_clustering(resolved)
        assert signal is not None
        assert signal.slug == "underconfidence"
        assert signal.metric["fifty_fifty_rate"] == 0.8

    def test_not_flagged_when_committed(self):
        resolved = [_d(0.9, True), _d(0.1, False), _d(0.8, True), _d(0.2, False), _d(0.95, True)]
        assert detect_fifty_fifty_clustering(resolved) is None

    def test_ignored_below_min_sample(self):
        assert detect_fifty_fifty_clustering([_d(0.5, True)]) is None


class TestWeakFalsification:
    def test_flags_mostly_missing(self):
        decisions = [_d(0.6, falsification=None)] * 4 + [_d(0.6, falsification="if X")]
        signal = detect_weak_falsification(decisions)
        assert signal is not None
        assert signal.metric["falsification_missing_rate"] == 0.8

    def test_not_flagged_when_disciplined(self):
        decisions = [_d(0.6, falsification="if X")] * 5
        assert detect_weak_falsification(decisions) is None


class TestReflectionAvoidance:
    def test_flags_low_review_rate(self):
        resolved = [_d(0.6, True)] * 10
        signal = detect_reflection_avoidance(resolved, reviewed_count=1)
        assert signal is not None
        assert signal.slug == "reflection_avoidance"
        assert signal.metric["review_rate"] == 0.1

    def test_not_flagged_when_reflective(self):
        resolved = [_d(0.6, True)] * 10
        assert detect_reflection_avoidance(resolved, reviewed_count=5) is None


class TestWeakProcess:
    def test_flags_low_process_score(self):
        decisions = [_d(0.6)] * 6
        signal = detect_weak_process(decisions, process_score=30.0)
        assert signal is not None
        assert signal.slug == "weak_process_discipline"

    def test_not_flagged_above_floor(self):
        decisions = [_d(0.6)] * 6
        assert detect_weak_process(decisions, process_score=70.0) is None

    def test_ignored_when_no_score(self):
        assert detect_weak_process([_d(0.6)] * 6, process_score=None) is None


# --------------------------------------------------------------------------- API

def _register(client):
    email = f"diag_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"], email


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_and_resolve(client, token, *, confidence, outcome, falsification=None):
    body = {"question": "Q", "confidence": confidence, "reasoning": "r"}
    if falsification is not None:
        body["falsification"] = falsification
    did = client.post("/api/decisions", json=body, headers=_auth(token)).json()["id"]
    client.post(
        f"/api/decisions/{did}/resolve",
        json={"outcome_binary": outcome},
        headers=_auth(token),
    )
    return did


def test_diagnosis_building_state_below_min_sample(client):
    token, _ = _register(client)
    _create_and_resolve(client, token, confidence=0.9, outcome=True)

    resp = client.get("/api/decisions/diagnosis", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "building"
    assert body["resolved_count"] == 1
    assert body["primary_weakness"] is None
    assert body["signals"] == []


def test_diagnosis_flags_overconfidence(client):
    token, _ = _register(client)
    # 5 high-conviction calls that all resolved against the user, no
    # falsification, no reviews -> overconfidence should be the primary signal.
    for _ in range(5):
        _create_and_resolve(client, token, confidence=0.9, outcome=False)

    resp = client.get("/api/decisions/diagnosis", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "active"
    assert body["resolved_count"] == 5
    slugs = {s["slug"] for s in body["signals"]}
    assert "overconfidence" in slugs
    assert body["primary_weakness"] == "overconfidence"
    assert body["summary"]


def test_diagnosis_scoped_to_caller(client, db):
    token, email = _register(client)
    other_token, _ = _register(client)
    # Only the other user has decisions; caller has none.
    for _ in range(5):
        _create_and_resolve(client, other_token, confidence=0.9, outcome=False)

    resp = client.get("/api/decisions/diagnosis", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["state"] == "building"
    assert resp.json()["resolved_count"] == 0
