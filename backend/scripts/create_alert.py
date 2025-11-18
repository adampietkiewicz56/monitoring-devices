import sys
from pathlib import Path

# dodajemy katalog backend do sys.path — teraz "app" będzie widoczne
ROOT = Path(__file__).resolve().parents[1]   # backend/
sys.path.insert(0, str(ROOT))


from app.db.session import engine, Session
from app.db.models import Alert
from datetime import datetime


HOST_ID = 1

with Session(engine) as session:
    alert = Alert(host_id=HOST_ID, severity="CRITICAL", message="Manual test alert", timestamp=datetime.utcnow())
    session.add(alert)
    session.commit()
    session.refresh(alert)
    print("Created alert id:", alert.id)