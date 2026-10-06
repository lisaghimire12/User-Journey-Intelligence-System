from collections import Counter

from backend.app.models.models import (
    Event,
    Session as JourneySession,
    Journey,
)


def rebuild(db):
    """
    Reconstruct journeys from raw Event records.

    Events are the source of truth.
    Each session becomes one reconstructed Journey.
    """

    events = (
        db.query(Event)
        .order_by(
            Event.session_id,
            Event.timestamp,
            Event.sequence_number
        )
        .all()
    )

    if not events:
        return 0

    # Group events by session
    grouped = {}

    for event in events:
        grouped.setdefault(event.session_id, []).append(event)

    # Rebuild derived journey records
    db.query(Journey).delete()

    session_rows = (
        db.query(JourneySession)
        .all()
    )

    session_map = {
        session.session_id: session
        for session in session_rows
    }

    for session_id, session_events in grouped.items():

        # Make sure ordering is deterministic
        session_events.sort(
            key=lambda event: (
                event.timestamp,
                event.sequence_number
            )
        )

        first_event = session_events[0]
        last_event = session_events[-1]

        anonymous_user_id = (
            first_event.anonymous_user_id
        )

        pages = [
            event.page
            for event in session_events
            if event.page
        ]

        event_names = [
            event.event_name
            for event in session_events
        ]

        # -------------------------------------------------
        # CONVERSION
        # -------------------------------------------------

        converted = (
            "purchase" in event_names
        )

        # -------------------------------------------------
        # ABANDONMENT
        # -------------------------------------------------

        if converted:
            abandonment_stage = None

        elif "begin_checkout" in event_names:
            abandonment_stage = "checkout"

        elif "add_to_cart" in event_names:
            abandonment_stage = "cart"

        elif "view_item" in event_names:
            abandonment_stage = "product"

        else:
            abandonment_stage = "discovery"

        # -------------------------------------------------
        # TIME
        # -------------------------------------------------

        start_time = first_event.timestamp
        end_time = last_event.timestamp

        try:
            duration_seconds = (
                end_time - start_time
            ).total_seconds()
        except Exception:
            duration_seconds = 0

        # -------------------------------------------------
        # PAGE METRICS
        # -------------------------------------------------

        page_counts = Counter(pages)

        unique_pages = len(
            set(pages)
        )

        repeated_pages = sum(
            1
            for count in page_counts.values()
            if count > 1
        )

        loop_count = sum(
            count - 1
            for count in page_counts.values()
            if count > 1
        )

        entry_page = (
            pages[0]
            if pages
            else ""
        )

        exit_page = (
            pages[-1]
            if pages
            else ""
        )

        # -------------------------------------------------
        # SESSION RECORD
        # -------------------------------------------------

        session = session_map.get(session_id)

        if session is None:

            session = JourneySession(
                session_id=session_id,
                anonymous_user_id=anonymous_user_id,
                start_time=start_time,
                end_time=end_time,
                event_count=len(session_events),
                converted=converted,
                source="live",
            )

            db.add(session)

        else:

            session.anonymous_user_id = (
                anonymous_user_id
            )

            session.start_time = start_time
            session.end_time = end_time
            session.event_count = len(session_events)
            session.converted = converted

        # -------------------------------------------------
        # JOURNEY RECORD
        # -------------------------------------------------

        journey = Journey(
            session_id=session_id,

            sequence=event_names,

            journey_length=len(
                event_names
            ),

            duration_seconds=duration_seconds,

            unique_pages=unique_pages,

            repeated_pages=repeated_pages,

            loop_count=loop_count,

            entry_page=entry_page,

            exit_page=exit_page,

            converted=converted,

            abandonment_stage=abandonment_stage,
        )

        db.add(journey)

    db.commit()

    return len(grouped)