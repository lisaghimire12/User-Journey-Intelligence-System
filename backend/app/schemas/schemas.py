from datetime import datetime
from pydantic import BaseModel,Field
class EventIn(BaseModel):
    event_name:str
    anonymous_user_id:str
    session_id:str
    page:str
    product_id:str|None=None
    timestamp:datetime
    sequence_number:int
    metadata:dict=Field(default_factory=dict)
class ProductInsightRequest(BaseModel):
    product_id:str
