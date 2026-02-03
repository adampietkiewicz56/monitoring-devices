from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from app.db.session import get_session
from app.db.models import Alert, Host
from app.utils.role_decorator import get_current_user, require_role
from app.db.models import UserRole
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AlertCreate(BaseModel):
    host_id: int
    message: str
    severity: str = "INFO"


class AlertUpdate(BaseModel):
    severity: str = None
    message: str = None


@router.get("/")
def get_alerts(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    """Get all alerts ordered by timestamp (newest first)"""
    statement = select(Alert).options(selectinload(Alert.host)).order_by(Alert.timestamp.desc())
    alerts = session.exec(statement).all()
    logger.debug(f"User {current_user.username} retrieved {len(alerts)} alerts")
    
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


@router.post("/", response_model=dict, status_code=201)
def create_alert(
    alert_data: AlertCreate,
    current_user = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_session)
):
    """Create alert manually (ADMIN only)"""
    # Sprawdź czy host istnieje
    host = session.get(Host, alert_data.host_id)
    if not host:
        raise HTTPException(status_code=404, detail=f"Host {alert_data.host_id} not found")
    
    # Stwórz alert
    alert = Alert(
        host_id=alert_data.host_id,
        message=alert_data.message,
        severity=alert_data.severity,
        timestamp=datetime.utcnow()
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    
    logger.info(f"Admin {current_user.username} created alert for host {host.name}")
    
    return {
        "id": alert.id,
        "host_id": alert.host_id,
        "message": alert.message,
        "severity": alert.severity,
        "timestamp": alert.timestamp
    }


@router.put("/{alert_id}", response_model=dict)
def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    current_user = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_session)
):
    """Update alert (ADMIN only)"""
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    # Update fields if provided
    if alert_update.severity:
        alert.severity = alert_update.severity
    if alert_update.message:
        alert.message = alert_update.message
    
    session.add(alert)
    session.commit()
    session.refresh(alert)
    
    logger.info(f"Admin {current_user.username} updated alert {alert_id}")
    
    return {
        "id": alert.id,
        "host_id": alert.host_id,
        "message": alert.message,
        "severity": alert.severity,
        "timestamp": alert.timestamp
    }


@router.delete("/{alert_id}", status_code=204)
def delete_alert(
    alert_id: int,
    current_user = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_session)
):
    """Delete alert (ADMIN only)"""
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    session.delete(alert)
    session.commit()
    
    logger.warning(f"Admin {current_user.username} deleted alert {alert_id}")

