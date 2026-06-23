from uuid import uuid4
import os
import shutil

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.operations import get_db
from core.db import WaterHeaterSubmissionResponse, WaterHeaterAnalysisResponse
from core.schema import WaterHeaterSubmission, WaterHeaterAnalysis

from services.ocr_service import process_nameplate
from services.water_heater_service import (
    decode_water_heater_age,
    recommend_water_heater_replacement
)

water_heater_router = APIRouter(
    prefix="/appliances/water-heaters",
    tags=["Water Heaters"]
)

UPLOAD_FOLDER = "uploads"


@water_heater_router.post("/submit")
async def submit_water_heater(request: Request, db: Session = Depends(get_db)) -> dict[str, str | int]:
    """_summary_

    Args:
        request (Request): _description_
        db (Session, optional): _description_. Defaults to Depends(get_db).

    Returns:
        _type_: _description_
    """
    form = await request.form()

    address = form["address"]
    appliance_count = int(form["applianceCount"])

    saved_count = 0

    for i in range(1, appliance_count + 1):
        unique_id = str(uuid4())

        file = form[f"waterHeaterNameplate{i}"]

        filename = f"{unique_id}_wh_{i}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        submission = WaterHeaterSubmission(
            address=address,
            appliance_number=i,
            nameplate_photo=path
        )

        db.add(submission)
        db.flush()

        ocr_result = process_nameplate(path)

        age_info = decode_water_heater_age(
            ocr_result.get("brand", ""),
            ocr_result.get("serial_number", "")
        )

        recommendation = recommend_water_heater_replacement(
            ocr_result.get("subtype", ""),
            age_info
        )

        analysis = WaterHeaterAnalysis(
            submission_id=submission.id,
            brand=ocr_result.get("brand"),
            model_number=ocr_result.get("model_number"),
            serial_number=ocr_result.get("serial_number"),
            age=age_info.get("age_years") if age_info else None,
            replacement_recommendation=recommendation.recommendation,
            subtype=ocr_result.get("subtype")
        )

        db.add(analysis)
        saved_count += 1

    db.commit()

    return {
        "message": "Water heater submission saved",
        "systems_saved": saved_count
    }


# get wh submissions
@appliance_router.get(
    "/water-heaters", response_model=list[WaterHeaterSubmissionResponse])
def get_water_heater_submissions(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)) -> List[WaterHeaterSubmission]:
    """_summary_

    Args:
        limit (int, optional): _description_. Defaults to 100.
        offset (int, optional): _description_. Defaults to 0.
        db (Session, optional): _description_. Defaults to Depends(get_db).

    Returns:
        List[WaterHeaterSubmission]: _description_
    """
    return db.query(WaterHeaterSubmission).limit(limit).offset(offset).all()


# get wh ai analysis
@appliance_router.get(
    "/water-heater-analysis", response_model=list[WaterHeaterAnalysisResponse])
def get_water_heater_analysis(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)) -> List[WaterHeaterAnalysis]:
    """_summary_

    Args:
        limit (int, optional): _description_. Defaults to 100.
        offset (int, optional): _description_. Defaults to 0.
        db (Session, optional): _description_. Defaults to Depends(get_db).

    Returns:
        List[WaterHeaterAnalysis]: _description_
    """
    return db.query(WaterHeaterAnalysis).limit(limit).offset(offset).all()
