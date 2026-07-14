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
from src.services.storage_service import upload_nameplate

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
    """Save water heater submissions and upload photos to Supabase Storage."""
    form: FormData = await request.form()

    address_value = form.get("address")
    count_value = form.get("applianceCount")

    if not isinstance(address_value, str):
        raise HTTPException(
            status_code=400,
            detail="Missing address",
        )

    if not isinstance(count_value, str):
        raise HTTPException(
            status_code=400,
            detail="Missing applianceCount",
        )

    address = address_value.strip()

    try:
        appliance_count = int(count_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="applianceCount must be a number",
        ) from exc

    if not address:
        raise HTTPException(
            status_code=400,
            detail="Address cannot be empty",
        )

    if appliance_count < 1 or appliance_count > 4:
        raise HTTPException(
            status_code=400,
            detail="applianceCount must be between 1 and 4",
        )

    submission_ids: list[str] = []

    try:
        for i in range(1, appliance_count + 1):
            form_file = form.get(f"waterHeaterNameplate{i}")

            if not isinstance(form_file, UploadFile):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Missing nameplate photo for "
                        f"water heater {i}"
                    ),
                )

            file = cast(UploadFile, form_file)
            submission_id = str(uuid4())

            storage_path = await upload_nameplate(
                file=file,
                appliance_type="water-heaters",
                submission_id=submission_id,
            )

            submission = WaterHeaterSubmission(
                id=submission_id,
                address=address,
                appliance_number=i,
                nameplate_photo=storage_path,
            )

            db.add(submission)
            submission_ids.append(submission_id)

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to save water heater submission",
        ) from exc

    for submission_id in submission_ids:
        background_tasks.add_task(
            process_water_heater_submission_background,
            submission_id,
        )

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
