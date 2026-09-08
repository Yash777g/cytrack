from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from database import Base

class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, index=True)
    scan_depth = Column(String)
    status = Column(String, default="running")
    created_at = Column(DateTime, default=datetime.utcnow)
    agents_selected = Column(JSON)
    results = Column(JSON, nullable=True)

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, index=True)
    agent_name = Column(String)
    severity = Column(String)
    description = Column(Text)
    payload = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)