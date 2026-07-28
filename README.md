# Project Overview
ApplianceIQ is a full-stack application that allows users to submit appliance nameplate photographs and receive an automated appliance analysis report.
The application currently supports:
HVAC systems
Water heaters

For each submitted appliance, the system attempts to:
- Save the uploaded nameplate image.
- Extract appliance information from the image.
- Identify the brand, model number, and serial number.
- Estimate the appliance manufacturing date and age.
- Generate a replacement recommendation.
- Flag uncertain results for future human review.
- Display the completed analysis on a report page.

The database file and uploaded appliance images are stored in directories that point to the G drive.

# Current System State
ApplianceIQ is currently a locally hosted development application.

The major components are:
Plain HTML, CSS, and JavaScript frontend
FastAPI backend
Local analysis worker
SQLAlchemy database
G-drive database storage
G-drive image storage
OCR and appliance-analysis services
Report page

The system is not currently deployed to a public cloud environment.

A simplified architecture is:
User Browser
     |
     | HTTP request
     v
Local FastAPI Application
     |
     |---- Save uploaded image -------> G Drive
     |
     |---- Save submission -----------> Database on G Drive
     |
     |---- Open AI Performs analysis -> Extracts text data
     |
     v
Report Page
     |
     | Poll analysis status
     v
FastAPI Report Endpoints

Meanwhile:
Local Worker
     |
     |---- Reads raw text and extracts brand and serial number
     |---- Decode appliance age
     |---- Generate recommendation
     |---- Save results to database
     v

# Technology Stack
## Frontend:
HTML
CSS
JavaScript

There is no frontend framework.

The browser handles:

Dynamic appliance input generation
Form submission
Redirecting to the report page
Polling for analysis completion
Displaying the report

## Backend:
Python 3.13
FastAPI
Uvicorn
SQLAlchemy 2
Pydantic 2
OpenAI Python SDK
python-dotenv
G-drive file storage
Data Storage


# Application Startup
The application is started locally with Uvicorn.
A typical command is:
python -m uvicorn src.main:app --reload

Uvicorn imports the FastAPI application from src/main.py

The main application module is responsible for:
Creating the FastAPI app
Registering routers
Mounting static files
Configuring templates
Initializing the database
Running startup and shutdown logic

A simplified version looks like:
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.core.operations import ENGINE
from src.core.schema import Base
from src.routers.hvac_router import hvac_router
from src.routers.water_heater_router import water_heater_router
from src.routers.report_router import report_router

app = FastAPI()

Base.metadata.create_all(bind=ENGINE)

app.include_router(hvac_router)
app.include_router(water_heater_router)
app.include_router(report_router)

app.mount(
    "/static",
    StaticFiles(directory="src/static"),
    name="static",
)

Database table creation may instead occur inside a FastAPI lifespan function.