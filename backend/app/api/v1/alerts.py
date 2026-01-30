from fastapi import APIRouter, Depends
from typing import List
from sqlmodel import select, Session
from app.db.session import get_session
from app.db.models import Alert
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[Alert])
def get_alerts(session: Session = Depends(get_session)):
    """Get all alerts ordered by timestamp (newest first)"""
    statement = select(Alert).order_by(Alert.timestamp.desc())
    alerts = session.exec(statement).all()
    logger.debug(f"Retrieved {len(alerts)} alerts")
    return alerts
