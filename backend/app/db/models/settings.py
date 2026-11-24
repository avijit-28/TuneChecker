from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.session import Base

class SettingsVersion(Base):
    __tablename__ = "settings_versions"

    version = Column(Integer, primary_key=True, autoincrement=True)
    sensitivity = Column(String, nullable=False)  # 'low', 'medium', 'high'
    config = Column(JSON, nullable=False)
    source = Column(String, nullable=False)  # 'default', 'user', 'reset'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
