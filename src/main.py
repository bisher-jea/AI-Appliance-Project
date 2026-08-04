import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles    # serve uploaded image files
from fastapi.templating import Jinja2Templates
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .core.database import engine, init_tables
from .routers.hvac_router import hvac_router
from .routers.water_heater_router import water_heater_router
from .routers.report_router import report_router
from .routers.admin_router import admin_router


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    init_tables(engine)
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

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SESSION_SECRET_KEY",
        "development-secret-change-this",
    ),
    session_cookie="applianceiq_dashboard_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=False,
)

templates = Jinja2Templates(directory="frontend/templates")

UPLOAD_DIRECTORY = Path(
    os.getenv(
        "UPLOAD_DIRECTORY",
        r"C:\Users\bishes\Downloads\applianceIQ\uploads",
    )
).resolve()

# uploaded files go to uploads and makes uploaded files viewable thru BE
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIRECTORY)),
    name="uploads",
)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(router=hvac_router)
app.include_router(router=water_heater_router)
app.include_router(router=report_router)
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(name="index.html", request=request)
