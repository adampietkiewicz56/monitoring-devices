import asyncio
from datetime import datetime
from typing import Dict

from icmplib import ping
from sqlmodel import Session, select

from app.db.session import engine
from app.db.models import Host, Alert


MAX_FAILURES = 3

PING_INTERVAL = 15

async def ping_loop():
    # Główna pętla monitorująca hosty
    #Działa w tle przez cały czas życia aplikacji

    failure_counts: Dict[int, int] = {}

    while True:
        try:
            with Session(engine) as session:
                hosts = session.exec(select(Host)).all()

                for host in hosts:
                    result = ping(host.ip, count=1, timeout=1)

                    if result.is_alive:
                        failure_counts[host.id] = 0

                        if host.status != "UP":
                            host.status = "UP"
                            session.add(
                                Alert(
                                    host_id=host.id,
                                    severity="INFO",
                                    message="Host recovered (UP)"
                                )
                            )
                        host.last_seen = datetime.utcnow()
                    else:
                        #zwiększamy licznik błędów
                        failure_counts[host.id] = failure_counts.get(host.id, 0) + 1


                        if (
                            failure_counts[host.id] >- MAX_FAILURES
                            and host.status != "DOWN"
                        ):
                            host.status = "DOWN"
                            session.add(
                                Alert(
                                    host_id = host.id,
                                    severity="CRITICAL",
                                    message="Host is DOWN"
                                )
                            )
                    session.add(host)

                session.commit()

        except Exception as e:
            print(f"Ping service error:", e)


        await asyncio.sleep(PING_INTERVAL)