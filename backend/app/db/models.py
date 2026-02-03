from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from sqlalchemy import Column, ForeignKey
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    role: UserRole = Field(default=UserRole.USER)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HostGroup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    hosts: List["Host"] = Relationship(back_populates="group")


class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ip: str
    status: Optional[str] = Field(default="unknown")
    last_seen: Optional[datetime] = Field(default_factory=datetime.utcnow)
    group_id: Optional[int] = Field(default=None, sa_column=Column(ForeignKey("hostgroup.id", ondelete="SET NULL")))

    group: Optional[HostGroup] = Relationship(back_populates="hosts")
    alerts: List["Alert"] = Relationship(back_populates="host", sa_relationship_kwargs={"cascade": "all, delete-orphan"})





class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    host_id: int = Field(sa_column=Column(ForeignKey("host.id", ondelete="CASCADE")))
    severity: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    host: Optional[Host] = Relationship(back_populates="alerts")



#Do poprawek: CASCADE przy usuwaniu hostów, bez tego alerty zostaną "sierotami"
# last_seen moze miec automatyczny timestamp
# severity na enum, ale to nie moja sugestia