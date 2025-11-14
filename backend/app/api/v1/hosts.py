from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()


#tymczasowa baza w pamięci
HOSTS=[]


class Host(BaseModel):
    id: int
    name: str
    ip: str

@router.get("/", response_model=List[Host])
def get_hosts():
    return HOSTS

@router.post("/", response_model=Host)
def add_host(host: Host):
    HOSTS.append(host)
    return host