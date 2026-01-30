from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlmodel import select, delete, Session, col
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.db.session import get_session
from app.db.models import Host, Alert, User, UserRole
from app.utils.role_decorator import require_role

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[Host])
def read_hosts(session: Session = Depends(get_session)):
    return session.exec(select(Host)).all()


@router.get("/search", response_model=List[Host])
def search_hosts(
    name: Optional[str] = Query(None, description="Search by host name (contains)"),
    ip: Optional[str] = Query(None, description="Search by IP address (contains)"),
    status: Optional[str] = Query(None, description="Filter by status (UP/DOWN/unknown)"),
    session: Session = Depends(get_session)
):
    """
    Search hosts by name, IP, or status using LIKE/contains pattern matching.
    All parameters are optional and can be combined.
    """
    query = select(Host)
    
    if name:
        query = query.where(col(Host.name).contains(name))
    
    if ip:
        query = query.where(col(Host.ip).contains(ip))
    
    if status:
        query = query.where(Host.status == status)
    
    results = session.exec(query).all()
    return results


@router.post("/", response_model=Host, status_code=status.HTTP_201_CREATED)
def create_host(
    host: Host,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.USER))
):
    try:
        session.add(host)
        session.commit()
        session.refresh(host)
        logger.info(f"User {current_user.username} created host {host.name}")
        return host
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"DB error while creating host: {e}")
        raise HTTPException(status_code=500, detail="DB error while creating host")


@router.get("/{host_id}", response_model=Host)
def read_host(host_id: int, session: Session = Depends(get_session)):
    host = session.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@router.put("/{host_id}", response_model=Host)
def update_host(
    host_id: int,
    host_data: Host,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.USER))
):
    host = session.get(Host, host_id)
    if not host:
        logger.warning(f"User {current_user.username} attempted to update non-existent host {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")

    host.name = host_data.name
    host.ip = host_data.ip

    try:
        session.add(host)
        session.commit()
        session.refresh(host)
        logger.info(f"User {current_user.username} updated host {host.name}")
        return host
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"DB error while updating host: {e}")
        raise HTTPException(status_code=500, detail="DB error while updating host")


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_host(
    host_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    host = session.get(Host, host_id)
    if not host:
        logger.warning(f"Admin {current_user.username} attempted to delete non-existent host {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")

    try:
        # Cascade delete handled by database, but we can be explicit
        session.exec(delete(Alert).where(Alert.host_id == host_id))
        session.delete(host)
        session.commit()
        logger.info(f"Admin {current_user.username} deleted host {host.name}")
        return
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"DB error while deleting host: {e}")
        raise HTTPException(status_code=500, detail="DB error while deleting host")
