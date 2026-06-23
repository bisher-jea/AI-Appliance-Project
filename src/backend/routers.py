# apirouter allows routes in separate file instead of everything in main
# gives route access to sqlalchemy db session
from uuid import UUID
from typing import Any

from fastapi import APIRouter, Depends
from backend.operations import get_db
from sqlalchemy.orm import Session
from backend.schema import (
    HVACSubmission,
    WaterHeaterSubmission,
    HVACAnalysis,
    WaterHeaterAnalysis
)


# response models
from database.db import (
    HVACSubmissionResponse,
    WaterHeaterSubmissionResponse,
    HVACAnalysisResponse,
    WaterHeaterAnalysisResponse,
)

# router setup
appliance_router: APIRouter = APIRouter(
    prefix="/appliances",
    tags=["appliances"]
)


# home route/test route
@app.get("/")
def home():
    return {
        "message": "FastAPI appliance database is running"
    }


# creates the submit endpoint (HTML sends data here)
@app.post("/submit")
async def submit_form(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()    # reads submitted form

    address = form["address"]
    appliance_type = form["applianceType"]
    appliance_count = int(form["applianceCount"])

    saved_count = 0

    for i in range(1, appliance_count + 1):
        unique_id = str(uuid4())

        if appliance_type == "HVAC":
            file = form[f"Nameplate{i}"]

            # creating unique filenames
            filename = (
                f"{unique_id}_appliance_{i}{file.filename}"

            )
            path = os.path.join(UPLOAD_FOLDER, outdoor_filename)

            # putting in uploads folder
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)


            # making db row
            hvac_submission = HVACSubmission(
                address=address,
                appliance_number=i,
                nameplate_photo=path,

            )

            db.add(hvac_submission)
            ocr_result = process_nameplate(outdoor_path)

            age_info = decode_hvac_age(
                ocr_result.get("brand", ""),
                ocr_result.get("serial_number", "")
            )

            recommendation = recommend_hvac_replacement(
                ocr_result.get("subtype", ""),
                age_info
            )

            hvac_analysis = HVACAnalysis(
                submission_id=hvac_submission.id,
                brand=ocr_result.get("brand"),
                model_number=ocr_result.get("model_number"),
                serial_number=ocr_result.get("serial_number"),
                age=age_info.get("age_years") if age_info else None,
                replacement_recommendation=recommendation.recommendation,
                subtype=ocr_result.get("subtype")
            )

            db.add(hvac_analysis)
            saved_count += 1

        elif appliance_type == "Water Heater":
            water_file = form[f"waterHeaterNameplate{i}"]

            water_filename = (
                f"{unique_id}_water_heater_{i}_{water_file.filename}"
            )
            water_path = os.path.join(UPLOAD_FOLDER, water_filename)

            with open(water_path, "wb") as buffer:
                shutil.copyfileobj(water_file.file, buffer)

            water_submission = WaterHeaterSubmission(
                address=address,
                appliance_number=i,
                nameplate_photo=water_path
            )

            db.add(water_submission)
            ocr_result = process_nameplate(water_path)

            age_info = decode_water_heater_age(
                ocr_result.get("brand", ""),
                ocr_result.get("serial_number", "")
            )

            recommendation = recommend_water_heater_replacement(
                ocr_result.get("subtype", ""),
                age_info
            )

            water_analysis = WaterHeaterAnalysis(
                submission_id=water_submission.id,
                brand=ocr_result.get("brand"),
                model_number=ocr_result.get("model_number"),
                serial_number=ocr_result.get("serial_number"),
                age=age_info.get("age_years") if age_info else None,
                replacement_recommendation=recommendation.recommendation,
                subtype=ocr_result.get("subtype")
            )

            db.add(water_analysis)
            saved_count += 1

    db.commit()    # to permanently save all newly created rows to the database

    # return response
    return {
        "message": "Appliance submission saved successfully",
        "appliance_type": appliance_type,
        "systems_saved": saved_count
    }
