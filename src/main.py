from fastapi import FastAPI,
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles    # serve uploaded image files
import os
from contextlib import asynccontextmanager

from .core.operations import init_tables, ENGINE
from .routers.hvac_router import hvac_router
from .routers.water_heater_router import water_heater_router
from .routers.dashboard_router import dashboard_router


# lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tables(ENGINE)
    yield

# creates app
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow requests from any frontend
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# uploaded files go to uploads and makes uploaded files viewable thr BE
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

app.include_router(router=hvac_router)
app.include_router(router=water_heater_router)
app.include_router(router=dashboard_router)

@app.get("/")
def home() -> dict[str, str]:
    return {"message": "FastAPI appliance database is running"}


