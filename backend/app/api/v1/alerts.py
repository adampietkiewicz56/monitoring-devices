from fastapi import APIRouter, Depends
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from app.db.session import get_session
from app.db.models import Alert
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
def get_alerts(session: Session = Depends(get_session)):
    """Get all alerts ordered by timestamp (newest first)"""
    statement = select(Alert).options(selectinload(Alert.host)).order_by(Alert.timestamp.desc())
    alerts = session.exec(statement).all()
    logger.debug(f"Retrieved {len(alerts)} alerts")
    
    # Manually construct response with host data
    result = []
    for alert in alerts:
        result.append({
            "id": alert.id,
            "host_id": alert.host_id,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": alert.timestamp,
            "host": {
                "id": alert.host.id,
                "name": alert.host.name,
                "ip": alert.host.ip,
                "status": alert.host.status,
                "last_seen": alert.host.last_seen
            } if alert.host else None
        })
    
    return result
