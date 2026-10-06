import sys
import json
import random

from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
    )
)

from backend.app.database.connection import (
    Base,
    engine,
    SessionLocal
)

from backend.app.models.models import (
    Product,
    Event
)

from backend.app.services.analytics import (
    rebuild
)

from backend.app.privacy.privacy import (
    pseudonymize
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(
    bind=engine
)

db = SessionLocal()


# =========================================================
# PRODUCTS
# =========================================================

db.query(Product).delete()

products_file = Path(
    "data/products/products.json"
)

products = json.loads(
    products_file.read_text(
        encoding="utf-8"
    )
)

for product in products:

    db.add(
        Product(
            **product
        )
    )


# =========================================================
# OLD DEMO EVENTS
# =========================================================

db.query(Event).delete()


# =========================================================
# DEMO JOURNEYS
# =========================================================

journey_flows = [

    [
        ("page_view", "Home"),
        ("search", "Search"),
        ("view_item", "Product"),
        ("product_insight_opened", "Product"),
        ("select_size", "Product"),
        ("add_to_cart", "Product"),
        ("view_cart", "Cart"),
        ("begin_checkout", "Checkout"),
        ("purchase", "Confirmation")
    ],

    [
        ("page_view", "Home"),
        ("search", "Search"),
        ("view_item", "Product"),
        ("product_insight_opened", "Product"),
        ("product_insight_section_view", "Product"),
        ("product_insight_closed", "Product"),
        ("view_item", "Product")
    ],

    [
        ("page_view", "Home"),
        ("view_item", "Product"),
        ("select_size", "Product"),
        ("add_to_cart", "Product"),
        ("view_cart", "Cart"),
        ("begin_checkout", "Checkout")
    ],

    [
        ("page_view", "Home"),
        ("search", "Search"),
        ("view_item", "Product"),
        ("product_insight_opened", "Product"),
        ("product_insight_section_viewed", "Product"),
        ("product_source_expanded", "Product"),
        ("product_insight_closed", "Product"),
        ("view_item", "Product"),
        ("add_to_cart", "Product"),
        ("view_cart", "Cart"),
        ("begin_checkout", "Checkout"),
        ("purchase", "Confirmation")
    ]
]


now = datetime.utcnow()


# =========================================================
# 30 SESSIONS
# 15 USERS
#
# Each user gets multiple sessions.
# This allows the dashboard to analyze:
#
# USER
#   ├── SESSION 1
#   ├── SESSION 2
#   └── ...
#
# =========================================================

for session_number in range(30):

    raw_user_id = (
        f"demo-user-{session_number % 15:03d}"
    )

    raw_session_id = (
        f"demo-session-{session_number:03d}"
    )

    # Pseudonymize before storing.
    stored_user_id = pseudonymize(
        raw_user_id
    )

    stored_session_id = pseudonymize(
        raw_session_id
    )

    flow = journey_flows[
        session_number
        % len(journey_flows)
    ]

    # Slightly randomize product choice.
    product_id = random.choice([
        "shoes-01",
        "clothing-01",
        "food-01",
        "electronics-01"
    ])

    session_time = (
        now
        - timedelta(
            minutes=session_number * 5
        )
    )

    for sequence_number, (
        event_name,
        page
    ) in enumerate(
        flow
    ):

        db.add(
            Event(

                event_name=event_name,

                anonymous_user_id=
                    stored_user_id,

                session_id=
                    stored_session_id,

                page=page,

                product_id=(
                    product_id
                    if page == "Product"
                    else None
                ),

                timestamp=(
                    session_time
                    + timedelta(
                        seconds=sequence_number
                    )
                ),

                sequence_number=
                    sequence_number,

                metadata_json={},

                source="synthetic"
            )
        )


# =========================================================
# SAVE
# =========================================================

db.commit()


# =========================================================
# REBUILD JOURNEYS
# =========================================================

rebuild(db)


db.close()


print(
    "Seed complete:"
)

print(
    "12 products"
)

print(
    "30 sessions"
)

print(
    "15 pseudonymous users"
)

print(
    "Multiple sessions per user"
)

print(
    "User-level journeys reconstructed"
)