from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import hashlib
import json

from backend.app.database.connection import get_db
from backend.app.models.models import Product
from backend.app.schemas.schemas import ProductInsightRequest
from ai.interpreter.product_interpreter import interpret_product


router = APIRouter(
    prefix="/api/product-insight",
    tags=["AI"]
)


# Cache generated insights so the AI does not run again
# every time the same product is opened.
INSIGHT_CACHE = {}


def get_product_cache_key(product):
    """
    Create a key based on the actual product data.
    If the product data changes, a new insight will be generated.
    """

    product_data = {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "price": product.price,
        "description": product.description,
        "rating": product.rating,
        "stock": product.stock,
        "attributes": product.attributes,
    }

    serialized = json.dumps(
        product_data,
        sort_keys=True,
        default=str
    )

    return hashlib.md5(
        serialized.encode("utf-8")
    ).hexdigest()


@router.post("")
def insight(
    payload: ProductInsightRequest,
    db: Session = Depends(get_db)
):

    # Find product
    product = db.get(Product, payload.product_id)

    if not product:
        return {
            "error": "Product not found"
        }

    # Generate cache key from product data
    cache_key = get_product_cache_key(product)

    # --------------------------------------------------
    # FAST PATH
    # --------------------------------------------------
    # If this product has already been interpreted,
    # return the previous AI result immediately.
    # --------------------------------------------------

    if cache_key in INSIGHT_CACHE:
        return INSIGHT_CACHE[cache_key]

    # --------------------------------------------------
    # FIRST REQUEST
    # --------------------------------------------------
    # Only the first request actually runs the AI.
    # --------------------------------------------------

    try:
        result = interpret_product(product)

        # Save the generated result
        INSIGHT_CACHE[cache_key] = result

        return result

    except Exception:
        # The website should not crash if the AI service fails.
        return {
            "error": "Product insights are temporarily unavailable."
        }