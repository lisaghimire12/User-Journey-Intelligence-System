from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.models import Product
router=APIRouter(prefix="/api/products",tags=["products"])
@router.get("")
def products(db:Session=Depends(get_db)): return db.query(Product).all()
@router.get("/{product_id}")
def product(product_id:str,db:Session=Depends(get_db)): return db.get(Product,product_id) or {"error":"Product not found"}
