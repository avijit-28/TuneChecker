import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app.db.session import engine, Base, SessionLocal
import app.db.models
from app.services.settings_service import SettingsService

Base.metadata.create_all(bind=engine)
with SessionLocal() as _db:
    SettingsService.get_latest_settings(_db)
print("Created tables & seeded default settings in:", engine.url)
