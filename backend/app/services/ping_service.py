import asyncio
from datetime import datetime
from typing import Dict
import socket
import platform

from icmplib import ping
from sqlmodel import Session, select

from app.db.session import engine
from app.db.models import Host, Alert
from app.ws.alerts import manager


MAX_FAILURES = 3
PING_INTERVAL = 8
IS_WINDOWS = platform.system() == "Windows"


def is_host_alive(ip: str) -> bool:
    # Na Windows ICMP wymaga admin - używamy tylko TCP
    if IS_WINDOWS:
        try:
            with socket.create_connection((ip, 80), timeout=2):
                return True
        except Exception:
            try:
                # Fallback: spróbuj port 443
                with socket.create_connection((ip, 443), timeout=2):
                    return True
            except Exception:
                return False
    
    # Na Linux/Mac: ICMP + TCP fallback
    try:
        result = ping(ip, count=1, timeout=2, privileged=False)
        if result.is_alive:
            return True
    except Exception as icmp_error:
        print(f"  [ICMP error for {ip}]")

    # TCP fallback
    try:
        with socket.create_connection((ip, 80), timeout=2):
            return True
    except Exception:
        pass
    
    return False


async def ping_loop():
    failure_counts: Dict[int, int] = {}
    print("[PING_LOOP] Starting...")

    while True:
        try:
            with Session(engine) as session:
                hosts = session.exec(select(Host)).all()
                print(f"[PING_LOOP] Checking {len(hosts)} hosts...")

                for host in hosts:
                    try:
                        # Run ping in executor (non-blocking)
                        loop = asyncio.get_event_loop()
                        alive = await asyncio.wait_for(
                            loop.run_in_executor(None, is_host_alive, host.ip),
                            timeout=2  # Reduce from 5s to 2s per host
                        )
                    except asyncio.TimeoutError:
                        print(f"  [TIMEOUT] {host.name} ({host.ip})")
                        alive = False
                    except Exception as ping_error:
                        print(f"  [ERROR] {host.name}: {ping_error}")
                        alive = False

                    # ===== HOST UP =====
                    if alive:
                        failure_counts[host.id] = 0
                        previous_status = host.status

                        if previous_status == "unknown":
                            host.status = "UP"
                            print(f"✓ Host {host.name} ({host.ip}) initialized as UP")

                        elif previous_status == "DOWN":
                            host.status = "UP"

                            alert = Alert(
                                host_id=host.id,
                                severity="INFO",
                                message="Host recovered (UP)"
                            )
                            session.add(alert)

                            print(f"✓ ALERT: Host {host.name} recovered")
                            try:
                                await manager.broadcast(f"ALERT: Host {host.name} recovered (UP)")
                            except Exception as ws_error:
                                print(f"  [WS error]: {ws_error}")

                        host.last_seen = datetime.utcnow()

                    # ===== HOST DOWN =====
                    else:
                        failure_counts[host.id] = failure_counts.get(host.id, 0) + 1
                        previous_status = host.status

                        # Immediately mark unknown host as DOWN
                        if previous_status == "unknown":
                            host.status = "DOWN"

                            alert = Alert(
                                host_id=host.id,
                                severity="CRITICAL",
                                message="Host is DOWN"
                            )
                            session.add(alert)

                            print(f"✗ Host {host.name} ({host.ip}) initialized as DOWN")
                            try:
                                await manager.broadcast(f"ALERT: Host {host.name} is DOWN")
                            except Exception as ws_error:
                                print(f"  [WS error]: {ws_error}")

                        elif (
                            failure_counts[host.id] >= MAX_FAILURES
                            and previous_status != "DOWN"
                        ):
                            host.status = "DOWN"

                            alert = Alert(
                                host_id=host.id,
                                severity="CRITICAL",
                                message="Host is DOWN"
                            )
                            session.add(alert)

                            print(f"✗ ALERT: Host {host.name} is DOWN")
                            try:
                                await manager.broadcast(f"ALERT: Host {host.name} is DOWN")
                            except Exception as ws_error:
                                print(f"  [WS error]: {ws_error}")

                    session.add(host)

                session.commit()

        except Exception as e:
            print(f"[PING_LOOP ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        await asyncio.sleep(PING_INTERVAL)
