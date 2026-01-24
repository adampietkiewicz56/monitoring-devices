from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import select, delete, Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_session
from app.db.models import Host, Alert

router = APIRouter()


@router.get("/", response_model=List[Host])
def read_hosts(session: Session = Depends(get_session)):
    return session.exec(select(Host)).all()


@router.post("/", response_model=Host, status_code=status.HTTP_201_CREATED)
def create_host(host: Host, session: Session = Depends(get_session)):
    try:
        session.add(host)
        session.commit()
        session.refresh(host)
        return host
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="DB error while creating host")


@router.get("/{host_id}", response_model=Host)
def read_host(host_id: int, session: Session = Depends(get_session)):
    host = session.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@router.put("/{host_id}", response_model=Host)
def update_host(host_id: int, host_data: Host, session: Session = Depends(get_session)):
    host = session.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    host.name = host_data.name
    host.ip = host_data.ip

    try:
        session.add(host)
        session.commit()
        session.refresh(host)
        return host
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=500, detail="DB error while updating host")


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_host(host_id: int, session: Session = Depends(get_session)):
    host = session.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    try:
        # najpierw usuń alerty powiązane z hostem
        session.exec(delete(Alert).where(Alert.host_id == host_id))

        # potem usuń hosta
        session.delete(host)

        # commit JEDEN raz na koniec
        session.commit()
        return
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=500, detail="DB error while deleting host")
