# Gamification Engine — Issues & Fixes

## Issues identified in code review

---

### 1. Process Builder uses wrong BadgeSlug (CRITICAL)

**File:** `badge_evaluator.py`  
**Problem:** `PROCESS_BUILDER` badge incorrectly reuses `BadgeSlug.WHAT_WOULD_CHANGE`.

**Fix — add to `models_gamification.py` BadgeSlug enum:**
```python
PROCESS_BUILDER = "process_builder"
```

**Fix — update `badge_evaluator.py`:**
```python
# Change this:
self._try_award_badge(
    profile.user_id, BadgeSlug.WHAT_WOULD_CHANGE,  # WRONG
    decision.id, None, 75, badges
)

# To this:
self._try_award_badge(
    profile.user_id, BadgeSlug.PROCESS_BUILDER,    # CORRECT
    decision.id, None, 75, badges
)
```

**Fix — add to Alembic migration enum:**
```python
badge_slug = postgresql.ENUM(
    ...
    'process_builder',   # ADD THIS
    ...
    name='badgeslug'
)
```

---

### 2. Badge points written even when badge not newly earned (BUG)

**File:** `badge_evaluator.py`  
**Problem:** Badge point entries are added to the `points` dict before
`_try_award_badge` is called. If the badge already exists, `_try_award_badge`
returns `False` but the points dict still has the entry, and `_commit_points`
writes them anyway.

**Fix:** Only add badge points to the dict when the badge is newly awarded.
Use the return value of `_try_award_badge` as the gate:

```python
# Instead of:
self._try_award_badge(...)
points["good_loser_badge"] = 75   # Added unconditionally

# Do this:
awarded = self._try_award_badge(...)
if awarded:
    points["good_loser_badge"] = 75   # Only added if badge was new
```

Apply this pattern to every badge point entry in:
- `on_decision_logged` (streak badges)
- `on_decision_resolved` (calibration streak)
- `on_review_submitted` (Good Loser, Humble Winner, Avoided Revenge, Revised Thesis)
- `on_insight_loop_completed` (Loop Closed, Bias Corrected, Skill Transferred)

---

### 3. Event ordering coupling in Process Score (FRAGILE)

**File:** `score_family_updater.py`  
**Problem:** `_process_score()` reads `profile.total_calls` to compute the
rolling average, assuming it was already incremented by `PointsBadgeEvaluator.
on_decision_logged()`. If call order is wrong in a test or edge case, the
rolling average is off by one.

**Fix:** Pass `call_number` explicitly instead of reading from profile state:

```python
# score_family_updater.py — change signature:
def _process_score(
    self,
    profile: UserGamificationProfile,
    decision: Decision,
    call_number: int,   # ADD THIS — pass profile.total_calls after increment
) -> float:
    ...
    if call_number <= 1:
        return float(decision_process)
    previous_total = profile.process_score * (call_number - 1)
    return (previous_total + decision_process) / call_number

# Caller in update_after_resolution:
process_score = self._process_score(profile, decision, profile.total_calls)
```

This makes the computation independent of event ordering.

---

### 4. Calibration trend bonus has no idempotency guard (BUG)

**File:** `badge_evaluator.py`, `models_gamification.py`  
**Problem:** `_calibration_trending_up()` checks if calibration improved over
30 days, but doesn't track when the bonus was last awarded. A user resolving
10 decisions in one day could earn the +40 point bonus 10 times.

**Fix — add field to UserGamificationProfile:**
```python
last_trend_bonus_at = Column(DateTime, nullable=True)
```

**Fix — add guard in `_calibration_trending_up()`:**
```python
def _calibration_trending_up(self, user_id: UUID, profile: UserGamificationProfile) -> bool:
    # Only award once per 30 days
    if profile.last_trend_bonus_at:
        days_since = (datetime.utcnow() - profile.last_trend_bonus_at).days
        if days_since < 30:
            return False
    
    # ... existing trend check logic ...
    
    if is_trending_up:
        profile.last_trend_bonus_at = datetime.utcnow()
        return True
    return False
```

Also update the Alembic migration to add the new column.

---

## Recommended pre-merge checklist

- [ ] Fix #1: Add `PROCESS_BUILDER` BadgeSlug, update migration and evaluator
- [ ] Fix #2: Gate badge points on `_try_award_badge` return value
- [ ] Fix #3: Pass `call_number` explicitly to `_process_score`
- [ ] Fix #4: Add `last_trend_bonus_at` to profile + guard in evaluator
- [ ] Run `test_brier.py` — must pass 100% before merge
- [ ] Write `test_score_family_updater.py` (mock DB, verify score transitions)
- [ ] Write `test_badge_evaluator.py` (mock DB, verify idempotency)
- [ ] Only then: wire FastAPI endpoints
