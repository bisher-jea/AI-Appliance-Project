# ApplianceIQ
This project is an AI-powered appliance identification system designed for home inspections. Users upload photos of HVAC and water heater nameplates through a web application built with HTML, FastAPI, and SQLite. The system uses Tesseract OCR to extract key equipment information, including the manufacturer, model number, and serial number. Based on the extracted brand and serial number, a custom age-decoding engine determines the appliance's manufacture date and calculates its age using manufacturer-specific serial number formats. The results are stored in a database and can be flagged for manual review when information cannot be confidently extracted or decoded. The goal is to automate equipment identification and age estimation, reducing manual effort while improving inspection efficiency and consistency.

## Core Functionalities
- Optical character recognition
- Equipement extraction information
- Brand recognition
- Serial number decoding
- Age calculation
- Data validation
- Manual review flagigng
- Database integration

## Installation
1. Create a Python virtual environment and install the following (preferably with UV but venv works):
```
"fastapi>=0.136.3"
"pydantic>=2.13.4"
"python-dotenv>=1.2.2"
"sqlalchemy>=2.0.49"
"uvicorn>=0.47.0"
"pytesseract>=0.3.13"
```
2. Run `pip install -e .` at the main project level (`{bisher_project/`)
3. Create a file named `.env` and enter the following values into it (for a sqlite DB):
```
DB_URL="sqlite:///bisher_project/sqlite.db"
```
4. Run `main.py` in the virtual environment.
5. Go to `localhost:8000/docs` to test out the API.