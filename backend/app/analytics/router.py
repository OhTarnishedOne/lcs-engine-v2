from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..deps import get_db
from ..auth.utils import verify_token
from ..db.models import User
from ..db.models.analytics import AnalyticsEvent
from .schemas import AnalyticsEventBatch, AnalyticsEventResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

ALLOWED_EVENTS: frozenset[str] = frozenset({
    "signup_completed",
    "login_completed",
    "session_started",
    "onboarding_started",
    "onboarding_step_completed",
    "onboarding_completed",
    "chat_message_sent",
    "strategy_generated",
    "strategy_viewed",
    "paper_trade_placed",
    "prediction_submitted",
})

SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password", "token", "secret", "api_key", "email",
})


def _sanitize_properties(props: dict | None) -> dict | None:
    if not props:
        return props
    return {k: v for k, v in props.items() if k not in SENSITIVE_KEYS}


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Parse Authorization header manually. Returns None if missing/invalid — never raises."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = verify_token(token, token_type="access")
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.post("/events", response_model=AnalyticsEventResponse)
def ingest_events(
    batch: AnalyticsEventBatch,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    accepted = 0
    rejected = 0

    for event in batch.events:
        if event.event_name not in ALLOWED_EVENTS:
            rejected += 1
            continue

        db.add(AnalyticsEvent(
            user_id=user.id if user else None,
            session_id=batch.session_id,
            event_name=event.event_name,
            event_properties=_sanitize_properties(event.event_properties),
            path=event.path,
            duration_ms=event.duration_ms,
        ))
        accepted += 1

    if accepted > 0:
        db.commit()

    return AnalyticsEventResponse(accepted=accepted, rejected=rejected)
