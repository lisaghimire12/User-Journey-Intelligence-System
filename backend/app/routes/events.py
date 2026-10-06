from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.models import Event
from backend.app.schemas.schemas import EventIn
from backend.app.privacy.privacy import minimize_event

router = APIRouter(
    prefix="/api/events",
    tags=["events"]
)


@router.post("")
def collect(
    payload: EventIn,
    db: Session = Depends(get_db)
):
    """
    Store one privacy-filtered user journey event.

    Raw events are the source of truth.
    Journey records are derived from these events.
    """

    # ---------------------------------------------------------
    # 1. Privacy filtering / validation
    # ---------------------------------------------------------

    try:
        data = minimize_event(
            payload.model_dump()
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    # ---------------------------------------------------------
    # 2. Store raw event
    # ---------------------------------------------------------

    event = Event(
        event_name=data["event_name"],
        anonymous_user_id=data["anonymous_user_id"],
        session_id=data["session_id"],
        page=data["page"],
        product_id=data["product_id"],
        timestamp=data["timestamp"],
        sequence_number=data["sequence_number"],
        metadata_json=data["metadata"],
        source="live"
    )

    db.add(event)

    try:
        db.commit()
        db.refresh(event)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not save event: {str(exc)}"
        )

    # ---------------------------------------------------------
    # 3. Rebuild the derived journey
    # ---------------------------------------------------------

    # IMPORTANT:
    # The raw event has already been committed.
    # Therefore, even if journey reconstruction fails,
    # we do not lose the event.

    rebuild_error = None

    try:
        from backend.app.services.analytics import rebuild

        rebuild(db)

    except Exception as exc:
        rebuild_error = str(exc)

        # The event itself is already safely stored.
        # Roll back only the failed rebuild transaction.
        db.rollback()

    # ---------------------------------------------------------
    # 4. Return success
    # ---------------------------------------------------------

    response = {
        "status": "accepted",
        "event_id": event.id
    }

    if rebuild_error:
        response["journey_rebuild"] = "failed"
        response["rebuild_error"] = rebuild_error
    else:
        response["journey_rebuild"] = "updated"

    return response