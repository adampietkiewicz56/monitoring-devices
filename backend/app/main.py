import asyncio
import logging
from fastapi import FastAPI
from app.api.v1.hosts import router as hosts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.hostgroups import router as hostgroups_router
from app.db.session import create_db_and_tables
from app.services.ping_service import ping_loop
from app.services.mqtt_service import mqtt_client
from app.ws.alerts import router as ws_router
from app.utils.logging_config import logger

app = FastAPI()

#podpinamy routery

app.include_router(hosts_router, prefix="/hosts", tags=["hosts"])
app.include_router(auth_router, tags=["auth"])
app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
app.include_router(hostgroups_router, prefix="/hostgroups", tags=["hostgroups"])

#websocket
app.include_router(ws_router)


#Create database on start
@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    logger.info("Database initialized")
    # Start ping loop in background (non-blocking)
    asyncio.create_task(ping_loop())
    mqtt_client.connect()
    logger.info("MQTT client connected")


@app.on_event("shutdown")
async def on_shutdown():
    mqtt_client.disconnect()
    logger.info("MQTT client disconnected")




@app.get("/")
def root():
    return {"message": "Monitoring backend działa!"}