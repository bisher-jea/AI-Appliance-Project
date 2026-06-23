from uuid import uuid4
import os
import shutil

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.operations import get_db
from core.db import HVACSubmissionResponse, HVACAnalysisResponse
from core.schema import HVACSubmission, HVACAnalysis

# your existing services/utilities
from services.ocr_service import process_nameplate
from services.hvac_service import decode_hvac_age, recommend_hvac_replacement


hvac_router = APIRouter(
    prefix="/appliances/hvac",
    tags=["HVAC"]
)

UPLOAD_FOLDER = "uploads"


@hvac_router.post("/submit")
async def submit_hvac(request: Request, db: Session = Depends(get_db)) -> dict[str, str | int]:
    form = await request.form()

    address = form["address"]
    appliance_count = int(form["applianceCount"])

    saved_count = 0

    for i in range(1, appliance_count + 1):
        unique_id = str(uuid4())

        file = form[f"Nameplate{i}"]

        filename = f"{unique_id}_hvac_{i}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        submission = HVACSubmission(
            address=address,
            appliance_number=i,
            nameplate_photo=path,
        )

        db.add(submission)
        db.flush()  # ensures ID is available for analysis

        ocr_result = process_nameplate(path)

        age_info = decode_hvac_age(
            ocr_result.get("brand", ""),
            ocr_result.get("serial_number", "")
        )

        recommendation = recommend_hvac_replacement(
            ocr_result.get("subtype", ""),
            age_info
        )

        analysis = HVACAnalysis(
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
        "message": "HVAC submission saved",
        "systems_saved": saved_count
    }


@appliance_router.get(
    "/hvac", response_model=list[HVACSubmissionResponse])
def get_hvac_submissions(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)) -> List[HVACSubmission]:
    return db.query(HVACSubmission).limit(limit).offset(offset).all()


# get hvac ai analysis
@appliance_router.get(
    "/hvac-analysis", response_model=list[HVACAnalysisResponse])
def get_hvac_analysis(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)) -> List[HVACAnalysis]:
    return db.query(HVACAnalysis).limit(limit).offset(offset).all()

