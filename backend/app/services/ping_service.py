import asyncio
from datetime import datetime
from typing import Dict
import socket
import platform
import logging

from icmplib import ping
from sqlmodel import Session, select

from app.db.session import engine
from app.db.models import Host, Alert
from app.ws.alerts import manager
from app.services.mqtt_service import mqtt_client

logger = logging.getLogger(__name__)

MAX_FAILURES = 3
PING_INTERVAL = 8
IS_WINDOWS = platform.system() == "Windows"


def is_host_alive(ip: str) -> bool:
    # Special case for localhost - always use socket check
    if ip in ('127.0.0.1', 'localhost', '::1'):
        try:
            # Try Python's own loopback
            with socket.create_connection((ip, 8000), timeout=1):
                return True
        except Exception:
            # If backend port is closed, try simple socket test
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((ip if ip != 'localhost' else '127.0.0.1', 80))
                s.close()
                return True
            except Exception:
                # Localhost always exists, even if no ports open
                return True
    
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
    logger.info("Ping loop starting...")

    while True:
        try:
            with Session(engine) as session:
                hosts = session.exec(select(Host)).all()
                logger.debug(f"Checking {len(hosts)} hosts...")

                for host in hosts:
                    try:
                        # Run ping in executor (non-blocking)
                        loop = asyncio.get_event_loop()
                        alive = await asyncio.wait_for(
                            loop.run_in_executor(None, is_host_alive, host.ip),
                            timeout=2
                        )
                    except asyncio.TimeoutError:
                        logger.debug(f"TIMEOUT {host.name} ({host.ip})")
                        alive = False
                    except Exception as ping_error:
                        logger.error(f"Ping error for {host.name}: {ping_error}")
                        alive = False

                    # ===== HOST UP =====
                    if alive:
                        failure_counts[host.id] = 0
                        previous_status = host.status

                        if previous_status == "unknown":
                            host.status = "UP"
                            host.last_seen = datetime.utcnow()
                            
                            alert = Alert(
                                host_id=host.id,
                                severity="INFO",
                                message="Host is UP"
                            )
                            session.add(alert)
                            
                            # Publish to MQTT
                            mqtt_client.publish_alert(host.id, host.name, "INFO", "Host is UP")
                            
                            logger.info(f"[UP] Host {host.name} ({host.ip}) initialized as UP")
                            try:
                                await manager.broadcast(f"ALERT: Host {host.name} is UP")
                            except Exception as ws_error:
                                logger.debug(f"WS broadcast error: {ws_error}")

                        elif previous_status == "DOWN":
                            host.status = "UP"
                            host.last_seen = datetime.utcnow()

                            alert = Alert(
                                host_id=host.id,
                                severity="INFO",
                                message="Host recovered (UP)"
                            )
                            session.add(alert)

                            # Publish to MQTT
                            mqtt_client.publish_alert(host.id, host.name, "INFO", "Host recovered (UP)")

                            logger.warning(f"[RECOVERED] ALERT: Host {host.name} recovered")
                            try:
                                await manager.broadcast(f"ALERT: Host {host.name} recovered (UP)")
                            except Exception as ws_error:
                                logger.debug(f"WS broadcast error: {ws_error}")

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

                            # Publish to MQTT
                            mqtt_client.publish_alert(host.id, host.name, "CRITICAL", "Host is DOWN")

                            logger.warning(f"[DOWN] Host {host.name} ({host.ip}) initialized as DOWN")
                            try:
                                await manager.broadcast(f"ALERT: Host {host.name} is DOWN")
                            except Exception as ws_error:
                                logger.debug(f"WS broadcast error: {ws_error}")

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

                            # Publish to MQTT
                            mqtt_client.publish_alert(host.id, host.name, "CRITICAL", "Host is DOWN")

                            logger.warning(f"[DOWN] ALERT: Host {host.name} is DOWN")
                            try:
                                await manager.broadcast(f"ALERT: Host {host.name} is DOWN")
                            except Exception as ws_error:
                                logger.debug(f"WS broadcast error: {ws_error}")

                    session.add(host)

                try:
                    session.commit()
                except Exception as commit_error:
                    # Handle case where host was deleted by another session
                    if "StaleDataError" in str(type(commit_error).__name__):
                        logger.debug(f"Host was deleted during ping check: {commit_error}")
                        session.rollback()
                    else:
                        raise

        except Exception as e:
            logger.error(f"Ping loop error: {type(e).__name__}: {e}")

        await asyncio.sleep(PING_INTERVAL)
