from sqlalchemy import Column, Integer, String, Date, Float
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)

class CycleData(Base):
    __tablename__ = "cycle_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    date = Column(Date)
    cycle_length = Column(Integer)
    period_length = Column(Integer)