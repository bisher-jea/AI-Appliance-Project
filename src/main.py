from fastapi import FastAPI, Request, Depends, File,
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles    # serve uploaded image files
from sqlalchemy.orm import Session
import os
import shutil
from contextlib import asynccontextmanager

from backend.ocr import process_nameplate
from backend.operations import get_db, init_tables, ENGINE
from backend.schema import (HVACSubmission, WaterHeaterSubmission, HVACAnalysis, WaterHeaterAnalysis)
from backend.parsing import decode_hvac_age, decode_water_heater_age
from backend.recommendation import recommend_hvac_replacement, recommend_water_heater_replacement
from routers.hvac_router import hvac_router
from routers.water_heater_router import water_heater_router
from routers.dashboard_router import dashboard_router


# lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tables(ENGINE)
    yield


# creates app
app = FastAPI(lifespan=lifespan)
app.include_router(router=hvac_router)
app.include_router(router=water_heater_router)
app.include_router(router=dashboard_router)

@app.get("/")
def home() -> dict[str, str]:
    return {"message": "FastAPI appliance database is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow requersts from any frontend
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# uploaded files go to uploads and makes uploaded files viewable thr BE
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# creates database based on schemas.py
init_tables(ENGINE)

