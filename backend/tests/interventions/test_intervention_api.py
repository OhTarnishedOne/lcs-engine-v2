"""
Sprint 5 — training interventions.

Covers deriving a mission from the diagnosis, explicit missions, one-active-at-
a-time, anchor-based progress with auto-completion + before/after metric
capture, the no-weakness case, and history.
"""

import uuid

from app.db.models import User


def _register(client):
    email = f"iv_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"], email


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create(client, token, *, confidence=0.6, falsification=None, resolve=None):
    body = {"question": "Q", "confidence": confidence, "reasoning": "r"}
    if falsification is not None:
        body["falsification"] = falsification
    did = client.post("/api/decisions", json=body, headers=_auth(token)).json()["id"]
    if resolve is not None:
        client.post(
            f"/api/decisions/{did}/resolve",
            json={"outcome_binary": resolve},
            headers=_auth(token),
        )
    return did


# --------------------------------------------------------------------------- start

def test_start_explicit_weakness(client):
    token, _ = _register(client)
    resp = client.post(
        "/api/interventions",
        json={"weakness_slug": "weak_falsification_discipline"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created"] is True
    iv = body["intervention"]
    assert iv["weakness_slug"] == "weak_falsification_discipline"
    assert iv["intervention_type"] == "falsification"
    assert iv["status"] == "active"
    assert iv["target_count"] == 3
    assert iv["progress_count"] == 0


def test_start_derives_from_diagnosis(client):
    token, _ = _register(client)
    # 5 high-conviction misses -> diagnosis primary weakness is overconfidence.
    for _ in range(5):
        _create(client, token, confidence=0.9, resolve=False)

    resp = client.post("/api/interventions", json={}, headers=_auth(token))
    assert resp.status_code == 200, resp.text
    iv = resp.json()["intervention"]
    assert iv["weakness_slug"] == "overconfidence"
    assert iv["intervention_type"] == "premortem"
    assert iv["baseline_metric"] == 1.0  # all high-conviction calls missed


def test_start_without_weakness_conflicts(client):
    token, _ = _register(client)
    resp = client.post("/api/interventions", json={}, headers=_auth(token))
    assert resp.status_code == 409


def test_one_active_at_a_time(client):
    token, _ = _register(client)
    first = client.post(
        "/api/interventions",
        json={"weakness_slug": "reflection_avoidance"},
        headers=_auth(token),
    ).json()
    assert first["created"] is True

    second = client.post(
        "/api/interventions",
        json={"weakness_slug": "overconfidence"},  # ignored while one is active
        headers=_auth(token),
    ).json()
    assert second["created"] is False
    assert second["intervention"]["id"] == first["intervention"]["id"]
    assert second["intervention"]["weakness_slug"] == "reflection_avoidance"


# --------------------------------------------------------------------------- progress

def test_progress_and_autocomplete_with_metric_capture(client):
    token, _ = _register(client)
    client.post(
        "/api/interventions",
        json={"weakness_slug": "weak_falsification_discipline"},
        headers=_auth(token),
    )

    # Three NEW decisions that each satisfy the mission (falsification written).
    for _ in range(3):
        _create(client, token, confidence=0.6, falsification="if the base rate shifts")

    active = client.get("/api/interventions/active", headers=_auth(token))
    assert active.status_code == 200
    iv = active.json()
    assert iv["progress_count"] == 3
    assert iv["status"] == "completed"
    assert iv["post_metric"] == 0.0  # every decision now has a falsification

    # Completed -> no active mission remains.
    assert client.get("/api/interventions/active", headers=_auth(token)).status_code == 404


def test_progress_counts_only_new_actions(client):
    token, _ = _register(client)
    # Pre-existing qualifying decision BEFORE the mission starts.
    _create(client, token, confidence=0.6, falsification="pre-existing")

    client.post(
        "/api/interventions",
        json={"weakness_slug": "weak_falsification_discipline"},
        headers=_auth(token),
    )
    # Two new qualifying decisions after start.
    _create(client, token, confidence=0.6, falsification="new one")
    _create(client, token, confidence=0.6, falsification="new two")

    iv = client.get("/api/interventions/active", headers=_auth(token)).json()
    # Anchor excludes the pre-existing one -> 2 new, not yet complete.
    assert iv["progress_count"] == 2
    assert iv["status"] == "active"


def test_active_404_when_none(client):
    token, _ = _register(client)
    assert client.get("/api/interventions/active", headers=_auth(token)).status_code == 404


def test_history_lists_interventions(client):
    token, _ = _register(client)
    client.post(
        "/api/interventions",
        json={"weakness_slug": "reflection_avoidance"},
        headers=_auth(token),
    )
    resp = client.get("/api/interventions", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["interventions"][0]["weakness_slug"] == "reflection_avoidance"
