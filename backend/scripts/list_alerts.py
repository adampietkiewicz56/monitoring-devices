# backend/scripts/list_alerts.py
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import engine, Session
from app.db.models import Alert
from sqlmodel import select

with Session(engine) as session:
    alerts = session.exec(select(Alert)).all()
    for a in alerts:
        print(a.id, a.host_id, a.severity, a.message, a.timestamp)
