from typing import NotRequired, TypedDict, Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, Request, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import quote
from src.core.operations import get_db
from src.core.db import HVACSubmissionResponse, HVACAnalysisResponse
from src.core.schema import HVACSubmission, HVACAnalysis
from src.services.background_tasks import process_hvac_submission_background
from src.services.storage_service import upload_nameplate
import os

hvac_router = APIRouter(
    prefix="/appliances/hvac",
    tags=["HVAC"]
)

BACKEND_URL = os.environ["BACKEND_URL"].rstrip("/")


class AgeInfo(TypedDict):
    manufacture_year: int
    manufacture_month: int
    age_years: int
    manufacture_week: NotRequired[int]
    plant_code: NotRequired[str]


DbSession = Annotated[Session, Depends(get_db)]


@hvac_router.post("/submit")
async def submit_hvac(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    form = await request.form()

    address_value = form.get("address")
    appliance_count_value = form.get("applianceCount")

    if not isinstance(address_value, str):
        raise HTTPException(
            status_code=400,
            detail="Address is missing or invalid.",
        )

    if not isinstance(appliance_count_value, str):
        raise HTTPException(
            status_code=400,
            detail="Appliance count is missing or invalid.",
        )

    try:
        appliance_count = int(appliance_count_value)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Appliance count must be a whole number.",
        ) from error

    address = address_value.strip()
    batch_id = str(uuid4())

    for i in range(1, appliance_count + 1):
        file_value = form.get(f"Nameplate{i}")

        if not isinstance(file_value, UploadFile):
            raise HTTPException(
                status_code=400,
                detail=f"Nameplate photo {i} is missing or invalid.",
            )

        submission_id = str(uuid4())

        storage_key = await upload_nameplate(
            file=file_value,
            appliance_type="hvac",
            submission_id=submission_id,
        )

        submission = HVACSubmission(
            id=submission_id,
            address=address,
            appliance_number=i,
            nameplate_photo=storage_key,
            batch_id=batch_id,
        )

        db.add(submission)
        db.commit()

        background_tasks.add_task(
            process_hvac_submission_background,
            submission_id,
        )

    return RedirectResponse(
        url=(
            f"/report?"
            f"address={quote(address)}&"
            f"batch_id={quote(batch_id)}"
        ),
        status_code=303,
    )


@hvac_router.get("", response_model=list[HVACSubmissionResponse],)
def get_hvac_submissions(db: DbSession, limit: int = 100, offset: int = 0,) -> list[HVACSubmission]:
    """_summary_

    Args:
        db (DbSession): _description_
        limit (int, optional): _description_. Defaults to 100.
        offset (int, optional): _description_. Defaults to 0.

    Returns:
        list[HVACSubmission]: _description_
    """
    return list(db.query(HVACSubmission).limit(limit).offset(offset).all())


@hvac_router.get("/analysis", response_model=list[HVACAnalysisResponse],)
def get_hvac_analysis(db: DbSession, limit: int = 100, offset: int = 0,) -> list[HVACAnalysis]:
    """_summary_

    Args:
        db (DbSession): _description_
        limit (int, optional): _description_. Defaults to 100.
        offset (int, optional): _description_. Defaults to 0.

    Returns:
        list[HVACAnalysis]: _description_
    """
    return list(db.query(HVACAnalysis).limit(limit).offset(offset).all())
