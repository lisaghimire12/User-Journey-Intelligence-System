from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.models import Event,Session as S,Journey
router=APIRouter(prefix="/api/system",tags=["system"])
@router.get("/status")
def status(db:Session=Depends(get_db)):
    return {"api":"online","database":"online","event_count":db.query(Event).count(),"session_count":db.query(S).count(),"journey_count":db.query(Journey).count(),"ai_service":"local evidence-grounded interpreter"}
