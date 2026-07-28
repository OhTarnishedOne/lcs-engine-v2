#!/usr/bin/env python3
"""
Soak comparison: Probability Lab calibration vs gamification profile scores.

ADR-001 canonical formula: 100 * (1 - 2 * avg_brier), clamped [0, 100].

Comparisons per user with predictions resolved after --since (default: dual-write
deploy commit b799352, 2026-07-24):

  1. lab_overall_score — compute_calibration_score()["overall_score"]
     Uses 90-day recency-weighted mean Brier (Lab user-facing path). May differ
     from gamification when predictions are older than 90d or weights differ.

  2. gamification_score — UserGamificationProfile.calibration_score
     Unweighted mean Brier across all resolved Decision rows (ADR-001 formula).

  3. unweighted_adr_score — ADR formula on all resolved UserPredictions (all time)
     True formula-alignment check: should match gamification_score when dual-write
     is healthy and only Lab predictions feed the engine.

Usage:
    cd backend && ./venv/bin/python scripts/soak_calibration_diff.py
    cd backend && ./venv/bin/python scripts/soak_calibration_diff.py --since 2026-07-24
    cd backend && ./venv/bin/python scripts/soak_calibration_diff.py --since 2026-07-24T00:00:00Z --tolerance 0.5
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

# Allow `python scripts/soak_calibration_diff.py` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.db.models.gamification import UserGamificationProfile
from app.db.models.probability import PredictionMarket, UserPrediction
from app.gamification.user_ids import user_id_to_uuid
from app.probability.calibration import compute_calibration_score
from app.services.gamification.brier import (
    calculate_average_brier,
    convert_brier_to_calibration_score,
)

DEFAULT_SINCE = datetime(2026, 7, 24, tzinfo=UTC)  # b799352 dual-write deploy date
MIN_RESOLVED_FOR_SCORE = 5


def _parse_since(value: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Invalid --since '{value}'. Use YYYY-MM-DD or ISO-8601 UTC."
    )


def _users_with_post_deploy_resolutions(db: Session, since: datetime) -> list[str]:
    rows = (
        db.query(UserPrediction.user_id)
        .join(PredictionMarket, UserPrediction.market_id == PredictionMarket.id)
        .filter(
            UserPrediction.brier_score.isnot(None),
            PredictionMarket.is_resolved.is_(True),
            PredictionMarket.updated_at >= since,
        )
        .distinct()
        .all()
    )
    return [row[0] for row in rows]


def _unweighted_adr_from_predictions(
    db: Session, user_id: str
) -> tuple[Optional[float], int]:
    preds = (
        db.query(UserPrediction)
        .filter(
            UserPrediction.user_id == user_id,
            UserPrediction.brier_score.isnot(None),
        )
        .all()
    )
    if len(preds) < MIN_RESOLVED_FOR_SCORE:
        return None, len(preds)
    avg_brier = calculate_average_brier([p.brier_score for p in preds])
    return convert_brier_to_calibration_score(avg_brier), len(preds)


def _gamification_score(db: Session, user_id: str) -> Optional[float]:
    profile = (
        db.query(UserGamificationProfile)
        .filter(UserGamificationProfile.user_id == user_id_to_uuid(user_id))
        .first()
    )
    if profile is None:
        return None
    return profile.calibration_score


def _diff(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    return round(a - b, 2)


def run(since: datetime, tolerance: float) -> int:
    db = SessionLocal()
    mismatches = 0
    try:
        user_ids = _users_with_post_deploy_resolutions(db, since)
        if not user_ids:
            print(f"No users with predictions resolved since {since.isoformat()}.")
            return 0

        print(
            f"Soak calibration diff — since {since.isoformat()} — "
            f"{len(user_ids)} user(s)\n"
        )
        header = (
            f"{'user_id':<38} {'post':>4} {'all':>4} "
            f"{'lab':>6} {'gami':>6} {'uw_adr':>6} "
            f"{'uw-gami':>7} {'lab-gami':>8} status"
        )
        print(header)
        print("-" * len(header))

        for user_id in sorted(user_ids):
            post_count = (
                db.query(UserPrediction)
                .join(PredictionMarket, UserPrediction.market_id == PredictionMarket.id)
                .filter(
                    UserPrediction.user_id == user_id,
                    UserPrediction.brier_score.isnot(None),
                    PredictionMarket.is_resolved.is_(True),
                    PredictionMarket.updated_at >= since,
                )
                .count()
            )

            lab = compute_calibration_score(db, user_id)
            lab_score = lab.get("overall_score")
            gami_score = _gamification_score(db, user_id)
            uw_score, all_resolved = _unweighted_adr_from_predictions(db, user_id)

            uw_gami_diff = _diff(uw_score, gami_score)
            lab_gami_diff = _diff(
                float(lab_score) if lab_score is not None else None,
                gami_score,
            )

            if all_resolved < MIN_RESOLVED_FOR_SCORE:
                status = "INSUFFICIENT"
            elif uw_score is None or gami_score is None:
                status = "MISSING_SCORE"
                mismatches += 1
            elif uw_gami_diff is not None and abs(uw_gami_diff) > tolerance:
                status = "MISMATCH"
                mismatches += 1
            else:
                status = "OK"

            def _fmt(v: Optional[float]) -> str:
                return f"{v:6.1f}" if v is not None else "   n/a"

            def _fmt_int(v: Optional[int]) -> str:
                return f"{v:6}" if v is not None else "   n/a"

            print(
                f"{user_id:<38} {post_count:>4} {all_resolved:>4} "
                f"{_fmt_int(lab_score)} {_fmt(gami_score)} {_fmt(uw_score)} "
                f"{uw_gami_diff if uw_gami_diff is not None else '    n/a':>7} "
                f"{lab_gami_diff if lab_gami_diff is not None else '      n/a':>8} "
                f"{status}"
            )

        print()
        print(
            "Notes: lab = 90d recency-weighted; gami/uw_adr = unweighted all-time "
            f"(ADR-001). Flag MISMATCH when |uw_adr - gami| > {tolerance}."
        )
        if mismatches:
            print(f"\n{mismatches} user(s) flagged.")
        else:
            print("\nNo formula-alignment mismatches.")
        return 1 if mismatches else 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Soak: Lab vs gamification calibration")
    parser.add_argument(
        "--since",
        type=_parse_since,
        default=DEFAULT_SINCE,
        help="Only users with market resolutions on/after this UTC timestamp "
        f"(default: {DEFAULT_SINCE.date()} / b799352 deploy)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.5,
        help="Max |uw_adr - gamification| before MISMATCH (default: 0.5)",
    )
    args = parser.parse_args()
    sys.exit(run(args.since, args.tolerance))


if __name__ == "__main__":
    main()
