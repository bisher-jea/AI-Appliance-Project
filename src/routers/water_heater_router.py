import os
import shutil
from typing import Annotated, cast
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from starlette.datastructures import FormData
from fastapi.responses import RedirectResponse
from urllib.parse import quote

from src.core.operations import get_db
from src.core.db import WaterHeaterSubmissionResponse, WaterHeaterAnalysisResponse
from src.core.schema import WaterHeaterSubmission, WaterHeaterAnalysis
from src.services.background_tasks import process_water_heater_submission_background


water_heater_router = APIRouter(
    prefix="/appliances/water-heaters",
    tags=["Water Heaters"],
)

UPLOAD_FOLDER = "uploads"
DbSession = Annotated[Session, Depends(get_db)]


@water_heater_router.post("/submit")
async def submit_water_heater(
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
        HTTPException: _description_

    Returns:
        RedirectResponse: _description_
    """
    form: FormData = await request.form()
    print("FORM KEYS:", list(form.keys()))

    address_value = form.get("address")
    count_value = form.get("applianceCount")

    if not isinstance(address_value, str):
        raise HTTPException(400, "Missing address")

    if not isinstance(count_value, str):
        raise HTTPException(400, "Missing applianceCount")

    address = address_value
    appliance_count = int(count_value)
    saved_count = 0

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    for i in range(1, appliance_count + 1):
        unique_id = str(uuid4())

        file = cast(UploadFile, form[f"waterHeaterNameplate{i}"])

        filename = f"{unique_id}_wh_{i}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        submission = WaterHeaterSubmission(
            address=address,
            appliance_number=i,
            nameplate_photo=path,
        )

        db.add(submission)
        db.flush()

        background_tasks.add_task(
            process_water_heater_submission_background,
            submission.id,
        )

        saved_count += 1

    db.commit()

    return RedirectResponse(
        url=f"/dashboard/report?address={quote(address)}",
        status_code=303,
    )


@water_heater_router.get(
    "",
    response_model=list[WaterHeaterSubmissionResponse],
)
def get_water_heater_submissions(
    db: DbSession,
    limit: int = 100,
    offset: int = 0,
) -> list[WaterHeaterSubmission]:
    """_summary_

    Args:
        db (DbSession): _description_
        limit (int, optional): _description_. Defaults to 100.
        offset (int, optional): _description_. Defaults to 0.

    Returns:
        list[WaterHeaterSubmission]: _description_
    """
    return list(
        db.query(WaterHeaterSubmission)
        .limit(limit)
        .offset(offset)
        .all()
    )


@water_heater_router.get(
    "/analysis",
    response_model=list[WaterHeaterAnalysisResponse],
)
def get_water_heater_analysis(
    db: DbSession,
    limit: int = 100,
    offset: int = 0,
) -> list[WaterHeaterAnalysis]:
    """_summary_

    Args:
        db (DbSession): _description_
        limit (int, optional): _description_. Defaults to 100.
        offset (int, optional): _description_. Defaults to 0.

    Returns:
        list[WaterHeaterAnalysis]: _description_
    """
    return list(
        db.query(WaterHeaterAnalysis)
        .limit(limit)
        .offset(offset)
        .all()
    )
