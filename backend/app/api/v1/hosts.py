from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import select, Session, delete
from app.db.session import get_session
from app.db.models import Host, Alert
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter()


@router.get("/", response_model = List[Host])
def read_hosts(*, session: Session = Depends(get_session)):
    hosts = session.exec(select(Host)).all()
    return hosts

#might consider adding limit/offset or cursor pagination. 


@router.post("/", response_model=Host)
def create_host(*, host: Host, session: Session = Depends(get_session)):
    try:
        with session.begin():
            session.add(host)
        
        session.refresh(host)
        return host
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="DB error while creating host")

#doesnt check whether host with such ip already exists
# No rollback, doesnt work if there is an error in commit
#might be better to use separate module HostCreate (no id, alerts) as body


@router.get("/{host_id}", response_model = Host)
def read_host(host_id: int, session: Session = Depends(get_session)):
    host = session.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host
#this one is fine i guess


@router.put("/{host_id}", response_model=Host)
def update_host(host_id: int, host_data: Host, session: Session = Depends(get_session)):
    host = session.get(Host, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    host.name = host_data.name
    host.ip = host_data.ip

    try:
        with session.begin():
            session.add(host)
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
        # Usuń alerty powiązane z hostem w jednej transakcji, potem usuń hosta
        with session.begin():
            session.exec(delete(Alert).where(Alert.host_id == host_id))
            session.delete(host)
        return
    except SQLAlchemyError as e:
        # rollback wykonany przez session.begin() w przypadku wyjątku,
        # ale dodatkowo logujemy/zwrotka
        # (opcjonalnie: importuj logger i zapisz logger.exception(e))
        raise HTTPException(status_code=500, detail="DB error while deleting host")

#must remember to set ON DELETE CASCADE