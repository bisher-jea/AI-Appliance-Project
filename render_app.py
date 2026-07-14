from fastapi import FastAPI

from src.routers.dashboard_router import dashboard_router

app = FastAPI()
app.include_router(dashboard_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "running"}