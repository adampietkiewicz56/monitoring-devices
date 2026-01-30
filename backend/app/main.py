import asyncio
from fastapi import FastAPI
from app.api.v1.hosts import router as hosts_router
from app.db.session import create_db_and_tables
from app.services.ping_service import ping_loop
from app.ws.alerts import router as ws_router

app = FastAPI()

#podpinamy router od hostów

app.include_router(hosts_router, prefix="/hosts", tags=["hosts"])

#websocket
app.include_router(ws_router)


#Create database on start
@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    # Start ping loop in background (non-blocking)
    asyncio.create_task(ping_loop())




@app.get("/")
def root():
    return {"message": "Monitoring backend działa!"}