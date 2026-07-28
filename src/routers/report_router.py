from typing import Annotated, TypedDict
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from src.core.database import get_db
from src.core.models import (
    HVACSubmission,
    WaterHeaterSubmission,
)

DbSession = Annotated[Session, Depends(get_db)]

templates = Jinja2Templates(directory="frontend/templates")

report_router = APIRouter(
    prefix="/report",
    tags=["Report"],
)


class ReportRow(TypedDict):
    id: str
    batch_id: str
    appliance_type: str
    address: str
    appliance_number: int
    nameplate_photo: str
    brand: str | None
    model_number: str | None
    serial_number: str | None
    age: int | None
    replacement_recommendation: str | None
    subtype: str | None
    needs_human_review: bool
    review_reason: str | None
    analysis_complete: bool


def build_report_rows(db: Session) -> list[ReportRow]:
    rows: list[ReportRow] = []

    hvac_submissions = db.query(HVACSubmission).all()

    for submission in hvac_submissions:
        analysis = submission.analysis

        row: ReportRow = {
            "id": submission.id,
            "batch_id": submission.batch_id,
            "appliance_type": "HVAC",
            "address": submission.address,
            "appliance_number": submission.appliance_number,
            "nameplate_photo": submission.nameplate_photo,
            "brand": analysis.brand if analysis else None,
            "model_number": analysis.model_number if analysis else None,
            "serial_number": analysis.serial_number if analysis else None,
            "age": analysis.age if analysis else None,
            "replacement_recommendation": (
                analysis.replacement_recommendation
                if analysis
                else None
            ),
            "subtype": analysis.subtype if analysis else None,
            "needs_human_review": (
                bool(analysis.needs_human_review)
                if analysis
                else False
            ),
            "review_reason": (
                analysis.review_reason
                if analysis
                else None
            ),
            "analysis_complete": (
                bool(analysis.analysis_complete)
                if analysis
                else False
            ),
        }

        rows.append(row)

    water_heater_submissions = (
        db.query(WaterHeaterSubmission).all()
    )

    for submission in water_heater_submissions:
        analysis = submission.analysis

        row: ReportRow = {
            "id": submission.id,
            "batch_id": submission.batch_id,
            "appliance_type": "Water Heater",
            "address": submission.address,
            "appliance_number": submission.appliance_number,
            "nameplate_photo": submission.nameplate_photo,
            "brand": analysis.brand if analysis else None,
            "model_number": analysis.model_number if analysis else None,
            "serial_number": analysis.serial_number if analysis else None,
            "age": analysis.age if analysis else None,
            "replacement_recommendation": (
                analysis.replacement_recommendation
                if analysis
                else None
            ),
            "subtype": analysis.subtype if analysis else None,
            "needs_human_review": (
                bool(analysis.needs_human_review)
                if analysis
                else False
            ),
            "review_reason": (
                analysis.review_reason
                if analysis
                else None
            ),
            "analysis_complete": (
                bool(analysis.analysis_complete)
                if analysis
                else False
            ),
        }

        rows.append(row)

    return rows


@report_router.get("/status")
def get_report_status(
    batch_id: str,
    db: DbSession,
):
    hvac_submissions = (
        db.query(HVACSubmission)
        .filter(
            HVACSubmission.batch_id == batch_id
        )
        .all()
    )

    water_heater_submissions = (
        db.query(WaterHeaterSubmission)
        .filter(
            WaterHeaterSubmission.batch_id == batch_id
        )
        .all()
    )

    submissions = [
        *hvac_submissions,
        *water_heater_submissions,
    ]

    if not submissions:
        return {
            "found": False,
            "complete": False,
            "completed": 0,
            "total": 0,
        }

    completed_count = 0

    for submission in submissions:
        analysis = submission.analysis

        if (
            analysis is not None
        ):
            completed_count += 1

    total_count = len(submissions)

    return {
        "found": True,
        "complete": (
            completed_count == total_count
        ),
        "completed": completed_count,
        "total": total_count,
    }


@report_router.get("/")
def get_report_page(
    request: Request,
    address: str,
    db: DbSession,
    batch_id: str | None = None,
):
    normalized_address = (
        address.strip().lower()
    )

    all_rows = build_report_rows(db)

    report_rows = [
        row
        for row in all_rows
        if (
            row["address"].strip().lower()
            == normalized_address
        )
    ]

    if batch_id:
        current_batch_rows = [
            row
            for row in report_rows
            if row["batch_id"] == batch_id
        ]
    else:
        current_batch_rows = report_rows

    all_complete = (
        bool(current_batch_rows)
        and all(
            row["analysis_complete"]
            for row in current_batch_rows
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "address": address,
            "rows": report_rows,
            "all_complete": all_complete,
            "batch_id": batch_id,
        },
    )