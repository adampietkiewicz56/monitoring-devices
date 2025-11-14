from fastapi import FastAPI
from app.api.v1.hosts import router as hosts_router

app = FastAPI()

#podpinamy router od hostów

app.include_router(hosts_router, prefix="/hosts", tags=["hosts"])

@app.get("/")
def root():
    return {"message": "Monitoring backend działa!"}