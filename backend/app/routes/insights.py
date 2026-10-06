from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.models import Product
from backend.app.schemas.schemas import ProductInsightRequest
from ai.interpreter.product_interpreter import interpret_product
router=APIRouter(prefix="/api/product-insight",tags=["AI"])
@router.post("")
def insight(payload:ProductInsightRequest,db:Session=Depends(get_db)):
    p=db.get(Product,payload.product_id)
    if not p: return {"error":"Product not found"}
    return interpret_product(p)
