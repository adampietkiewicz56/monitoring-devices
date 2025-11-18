from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from sqlalchemy import Column, ForeignKey





class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ip: str
    status: Optional[str] = Field(default="unknown")
    last_seen: Optional[datetime] = Field(default_factory=datetime.utcnow)


    #added on CASCADE
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