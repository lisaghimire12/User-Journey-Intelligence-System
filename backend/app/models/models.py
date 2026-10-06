from datetime import datetime
from sqlalchemy import String,Integer,Float,Boolean,DateTime,JSON,Text
from sqlalchemy.orm import Mapped,mapped_column
from backend.app.database.connection import Base

class Product(Base):
    __tablename__="products"
    id:Mapped[str]=mapped_column(String(80),primary_key=True)
    name:Mapped[str]=mapped_column(String(200))
    brand:Mapped[str]=mapped_column(String(120))
    category:Mapped[str]=mapped_column(String(80))
    price:Mapped[float]=mapped_column(Float)
    description:Mapped[str]=mapped_column(Text)
    images:Mapped[list]=mapped_column(JSON,default=list)
    rating:Mapped[float]=mapped_column(Float)
    stock:Mapped[int]=mapped_column(Integer)
    attributes:Mapped[dict]=mapped_column(JSON,default=dict)

class Event(Base):
    __tablename__="events"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    event_name:Mapped[str]=mapped_column(String(80))
    anonymous_user_id:Mapped[str]=mapped_column(String(128))
    session_id:Mapped[str]=mapped_column(String(128))
    page:Mapped[str]=mapped_column(String(120))
    product_id:Mapped[str|None]=mapped_column(String(80),nullable=True)
    timestamp:Mapped[datetime]=mapped_column(DateTime)
    sequence_number:Mapped[int]=mapped_column(Integer)
    metadata_json:Mapped[dict]=mapped_column(JSON,default=dict)
    source:Mapped[str]=mapped_column(String(30),default="live")

class Session(Base):
    __tablename__="sessions"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    session_id:Mapped[str]=mapped_column(String(128),unique=True)
    anonymous_user_id:Mapped[str]=mapped_column(String(128))
    start_time:Mapped[datetime]=mapped_column(DateTime)
    end_time:Mapped[datetime]=mapped_column(DateTime)
    event_count:Mapped[int]=mapped_column(Integer)
    converted:Mapped[bool]=mapped_column(Boolean)
    source:Mapped[str]=mapped_column(String(30),default="live")

class Journey(Base):
    __tablename__="journeys"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    session_id:Mapped[str]=mapped_column(String(128),unique=True)
    sequence:Mapped[list]=mapped_column(JSON)
    journey_length:Mapped[int]=mapped_column(Integer)
    duration_seconds:Mapped[float]=mapped_column(Float)
    unique_pages:Mapped[int]=mapped_column(Integer)
    repeated_pages:Mapped[int]=mapped_column(Integer)
    loop_count:Mapped[int]=mapped_column(Integer)
    entry_page:Mapped[str]=mapped_column(String(120))
    exit_page:Mapped[str]=mapped_column(String(120))
    converted:Mapped[bool]=mapped_column(Boolean)
    abandonment_stage:Mapped[str|None]=mapped_column(String(80),nullable=True)
