# backend/scripts/debug_delete_host.py
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import engine, Session
from app.db.models import Host, Alert
from sqlmodel import select, delete
import traceback

HOST_ID = 1  # ustaw id hosta do testów

with Session(engine) as session:
    print("Alerts BEFORE:")
    try:
        alerts_before = session.exec(select(Alert)).all()
        for a in alerts_before:
            print("alert:", a.id, a.host_id, a.message)
    except Exception:
        traceback.print_exc()

    # Spróbuj usunąć w transakcji i złap wyjątek
    try:
        with session.begin():
            # opcjonalnie: pokaz co usuwamy
            session.exec(delete(Alert).where(Alert.host_id == HOST_ID))
            host = session.get(Host, HOST_ID)
            if host:
                session.delete(host)
            else:
                print("Host not found")
        print("Delete transaction succeeded")
    except Exception as e:
        print("Exception during delete transaction:")
        traceback.print_exc()
        print("Exception type:", type(e), "value:", e)

    print("Alerts AFTER:")
    try:
        alerts_after = session.exec(select(Alert)).all()
        for a in alerts_after:
            print("alert:", a.id, a.host_id, a.message)
    except Exception:
        traceback.print_exc()
