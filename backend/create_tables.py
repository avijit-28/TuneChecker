import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app.db.session import engine, Base
import app.db.models

Base.metadata.create_all(bind=engine)
print("Created tables in:", engine.url)
