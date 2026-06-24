import os
import shutil
from typing import cast, NotRequired, TypedDict, Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, Request, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import FormData
from urllib.parse import quote

from core.operations import get_db
from core.db import HVACSubmissionResponse, HVACAnalysisResponse
from core.schema import HVACSubmission, HVACAnalysis
from services.background_tasks import process_hvac_submission_background


hvac_router = APIRouter(
    prefix="/appliances/hvac",
    tags=["HVAC"]
)

UPLOAD_FOLDER = "uploads"


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
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> RedirectResponse:
    """_summary_

    Args:
        request (Request): _description_
        db (DbSession): _description_

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        RedirectResponse: _description_
    """
    form: FormData = await request.form()

    address_value = form.get("address")
    count_value = form.get("applianceCount")

    if not isinstance(address_value, str):
        raise HTTPException(400, "Missing address")

    if not isinstance(count_value, str):
        raise HTTPException(400, "Missing applianceCount")

    address: str = address_value
    appliance_count: int = int(count_value)

    saved_count = 0
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    for i in range(1, appliance_count + 1):
        unique_id = str(uuid4())

        file = cast(UploadFile, form[f"Nameplate{i}"])

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
        db.flush()

        background_tasks.add_task(
            process_hvac_submission_background,
            submission.id,
        )
        saved_count += 1

    db.commit()

    return RedirectResponse(
        url=f"/dashboard/report?address={quote(address)}",
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
