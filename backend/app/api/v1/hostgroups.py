from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
import logging

from app.db.session import get_session
from app.db.models import HostGroup, Host, User, UserRole
from app.utils.role_decorator import require_role, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class HostGroupCreate(BaseModel):
    name: str
    description: str = None


class HostGroupUpdate(BaseModel):
    name: str = None
    description: str = None


@router.post("/", response_model=dict, status_code=201)
def create_hostgroup(
    data: HostGroupCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """CREATE - Create host group"""
    existing = session.exec(select(HostGroup).where(HostGroup.name == data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Host group '{data.name}' already exists")
    
    group = HostGroup(name=data.name, description=data.description)
    session.add(group)
    session.commit()
    session.refresh(group)
    
    logger.info(f"Admin {current_user.username} created host group '{group.name}'")
    
    return {"id": group.id, "name": group.name, "description": group.description, "created_at": group.created_at}


@router.get("/", response_model=list)
def read_hostgroups(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """READ - Get all host groups"""
    groups = session.exec(select(HostGroup)).all()
    
    return [
        {
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "created_at": g.created_at,
            "host_count": len(g.hosts)
        }
        for g in groups
    ]


@router.get("/{group_id}", response_model=dict)
def read_hostgroup(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """READ - Get single host group with hosts - 0.15 pkt"""
    group = session.get(HostGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Host group {group_id} not found")
    
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "created_at": group.created_at,
        "hosts": [{"id": h.id, "name": h.name, "ip": h.ip, "status": h.status} for h in group.hosts]
    }


@router.put("/{group_id}", response_model=dict)
def update_hostgroup(
    group_id: int,
    data: HostGroupUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """UPDATE - Update host group (ADMIN only) - 0.15 pkt"""
    group = session.get(HostGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Host group {group_id} not found")
    
    if data.name and data.name != group.name:
        existing = session.exec(select(HostGroup).where(HostGroup.name == data.name)).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Host group '{data.name}' already exists")
        group.name = data.name
    
    if data.description:
        group.description = data.description
    
    session.add(group)
    session.commit()
    session.refresh(group)
    
    logger.info(f"Admin {current_user.username} updated host group '{group.name}'")
    
    return {"id": group.id, "name": group.name, "description": group.description}


@router.delete("/{group_id}", status_code=204)
def delete_hostgroup(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """DELETE - Delete host group (ADMIN only) - 0.15 pkt"""
    group = session.get(HostGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Host group {group_id} not found")
    
    group_name = group.name
    session.delete(group)
    session.commit()
    
    logger.warning(f"Admin {current_user.username} deleted host group '{group_name}'")
