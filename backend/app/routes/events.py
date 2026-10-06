from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.models import Event
from backend.app.schemas.schemas import EventIn
from backend.app.privacy.privacy import minimize_event
router=APIRouter(prefix="/api/events",tags=["events"])
@router.post("")
def collect(payload:EventIn,db:Session=Depends(get_db)):
    try: d=minimize_event(payload.model_dump())
    except ValueError as e: raise HTTPException(400,str(e))
    db.add(Event(event_name=d["event_name"],anonymous_user_id=d["anonymous_user_id"],session_id=d["session_id"],page=d["page"],product_id=d["product_id"],timestamp=d["timestamp"],sequence_number=d["sequence_number"],metadata_json=d["metadata"],source="live"))
    db.commit(); return {"status":"accepted"}
