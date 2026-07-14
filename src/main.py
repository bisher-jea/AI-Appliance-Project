from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles    # serve uploaded image files
from fastapi.templating import Jinja2Templates
import os
from contextlib import asynccontextmanager

from .core.operations import ENGINE, init_tables
from .routers.hvac_router import hvac_router
from .routers.water_heater_router import water_heater_router
from .routers.dashboard_router import dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    init_tables(ENGINE)
    print("Database tables ready.")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow requests from any frontend
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

templates = Jinja2Templates(directory="src/templates")

# uploaded files go to uploads and makes uploaded files viewable thru BE
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/static", StaticFiles(directory="src/static"), name="static")

app.include_router(router=hvac_router)
app.include_router(router=water_heater_router)
app.include_router(router=dashboard_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(name="index.html", request=request)
