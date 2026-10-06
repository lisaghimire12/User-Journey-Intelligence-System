from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.models import (
    Event,
    Session as JourneySession,
    Journey,
)

from backend.app.services.analytics import rebuild


router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
)


# ============================================================
# JOURNEYS
# ============================================================

@router.get("/journeys")
def journeys(db: Session = Depends(get_db)):
    """
    Rebuild journeys from the raw event table and return them.
    """

    rebuild(db)

    rows = (
        db.query(Journey)
        .order_by(Journey.id.desc())
        .all()
    )

    return rows


# ============================================================
# EVENT COUNT
# ============================================================

@router.get("/events/count")
def event_count(db: Session = Depends(get_db)):
    """
    Return the actual number of raw events stored.
    """

    count = db.query(Event).count()

    return {
        "count": count
    }


# ============================================================
# RECENT EVENTS
# ============================================================

@router.get("/events/recent")
def recent_events(db: Session = Depends(get_db)):
    """
    Return the most recent raw events.
    """

    rows = (
        db.query(Event)
        .order_by(Event.id.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "id": event.id,
            "event_name": event.event_name,
            "anonymous_user_id": event.anonymous_user_id,
            "session_id": event.session_id,
            "page": event.page,
            "product_id": event.product_id,
            "timestamp": event.timestamp,
            "sequence_number": event.sequence_number,
            "metadata": event.metadata_json,
        }
        for event in rows
    ]


# ============================================================
# USERS
# ============================================================

@router.get("/users")
def users(db: Session = Depends(get_db)):
    """
    Return pseudonymous users derived from raw events.
    """

    rows = (
        db.query(Event.anonymous_user_id)
        .distinct()
        .all()
    )

    return [
        {
            "user_id": row[0]
        }
        for row in rows
        if row[0]
    ]


# ============================================================
# USER JOURNEY
# ============================================================

@router.get("/users/{user_id}")
def user_detail(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Return all sessions and journeys belonging to one
    pseudonymous user.
    """

    rebuild(db)

    sessions = (
        db.query(JourneySession)
        .filter(
            JourneySession.anonymous_user_id == user_id
        )
        .order_by(JourneySession.start_time.desc())
        .all()
    )

    result = []

    for session in sessions:

        journey = (
            db.query(Journey)
            .filter(
                Journey.session_id == session.session_id
            )
            .first()
        )

        result.append(
            {
                "session_id": session.session_id,
                "anonymous_user_id": session.anonymous_user_id,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "event_count": session.event_count,
                "converted": session.converted,
                "source": session.source,
                "journey": (
                    journey.sequence
                    if journey
                    else []
                ),
                "journey_length": (
                    journey.journey_length
                    if journey
                    else 0
                ),
                "duration_seconds": (
                    journey.duration_seconds
                    if journey
                    else 0
                ),
                "abandonment_stage": (
                    journey.abandonment_stage
                    if journey
                    else None
                ),
            }
        )

    total_events = (
        db.query(Event)
        .filter(
            Event.anonymous_user_id == user_id
        )
        .count()
    )

    converted_sessions = sum(
        1
        for session in sessions
        if session.converted
    )

    return {
        "user_id": user_id,
        "session_count": len(sessions),
        "total_events": total_events,
        "converted_sessions": converted_sessions,
        "sessions": result,
    }


# ============================================================
# OVERVIEW
# ============================================================

@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    """
    Return dashboard metrics based on the current raw events.

    IMPORTANT:
    Rebuild is called BEFORE calculating metrics so that
    the dashboard always reflects the latest storefront
    activity.
    """

    # --------------------------------------------------------
    # THIS IS THE IMPORTANT FIX
    # --------------------------------------------------------

    rebuild(db)

    # --------------------------------------------------------
    # Raw event count
    # --------------------------------------------------------

    total_events = db.query(Event).count()

    # --------------------------------------------------------
    # Reconstructed sessions
    # --------------------------------------------------------

    sessions = db.query(JourneySession).all()

    total_sessions = len(sessions)

    # --------------------------------------------------------
    # Converted sessions
    # --------------------------------------------------------

    converted_sessions = sum(
        1
        for session in sessions
        if session.converted
    )

    # --------------------------------------------------------
    # Conversion rate
    # --------------------------------------------------------

    conversion_rate = (
        converted_sessions / total_sessions
        if total_sessions > 0
        else 0
    )

    # --------------------------------------------------------
    # Journey statistics
    # --------------------------------------------------------

    journeys = db.query(Journey).all()

    if journeys:

        average_journey_length = (
            sum(
                journey.journey_length
                for journey in journeys
            )
            / len(journeys)
        )

        average_duration = (
            sum(
                journey.duration_seconds
                for journey in journeys
            )
            / len(journeys)
        )

    else:

        average_journey_length = 0
        average_duration = 0

    # --------------------------------------------------------
    # Abandonment
    # --------------------------------------------------------

    abandoned_sessions = sum(
        1
        for journey in journeys
        if not journey.converted
    )

    abandonment_rate = (
        abandoned_sessions / total_sessions
        if total_sessions > 0
        else 0
    )

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "sessions": total_sessions,

        "conversion_rate": conversion_rate,

        "converted_sessions": converted_sessions,

        "average_journey_length": (
            round(
                average_journey_length,
                2,
            )
        ),

        "average_journey_duration": (
            round(
                average_duration,
                2,
            )
        ),

        "abandonment_rate": abandonment_rate,

        "events": total_events,
    }


# ============================================================
# RECOMPUTE
# ============================================================

@router.post("/recompute")
def recompute(db: Session = Depends(get_db)):
    """
    Manually rebuild journeys from raw events.
    """

    count = rebuild(db)

    return {
        "status": "recomputed",
        "sessions_rebuilt": count,
    }