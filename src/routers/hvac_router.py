from typing import NotRequired, TypedDict, Annotated, cast
from uuid import uuid4
from fastapi import APIRouter, Depends, Request, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import FormData
from urllib.parse import quote
from starlette.datastructures import UploadFile as StarletteUploadFile
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
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> RedirectResponse:
    """Save HVAC submissions and upload nameplate photos to Supabase Storage."""
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
    uploaded_paths: list[str] = []

    try:
        for i in range(1, appliance_count + 1):
            form_file = form.get(f"Nameplate{i}")

            if form_file is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing nameplate photo for appliance {i}",
                )

            if not isinstance(form_file, StarletteUploadFile):
                raise HTTPException(
                    status_code=400,
                    detail=f"Nameplate{i} is not a valid uploaded file",
                )

            file = cast(UploadFile, form_file)
            submission_id: str = str(uuid4())

            storage_path = await upload_nameplate(
                file=file,
                appliance_type="hvac",
                submission_id=submission_id,
            )

            uploaded_paths.append(storage_path)

            submission = HVACSubmission(
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
            detail="Unable to save HVAC submission",
        ) from exc

    for submission_id in submission_ids:
        background_tasks.add_task(
            process_hvac_submission_background,
            submission_id,
        )

    return RedirectResponse(
        url=(
            f"{BACKEND_URL}/dashboard/report"
            f"?address={quote(address)}"
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
