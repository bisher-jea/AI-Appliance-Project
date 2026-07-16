from starlette.templating import _TemplateResponse
from typing import Annotated, TypedDict
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from src.core.operations import get_db
from src.core.schema import (
    HVACAnalysis,
    HVACSubmission,
    WaterHeaterAnalysis,
    WaterHeaterSubmission,
)

DbSession = Annotated[Session, Depends(get_db)]

templates = Jinja2Templates(directory="src/templates")

report_router = APIRouter(
    prefix="/report",
    tags=["Report"],
)


class ReportRow(TypedDict):
    id: str
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
            "analysis_complete": analysis is not None,
        }

        rows.append(row)

    water_heater_submissions = (
        db.query(WaterHeaterSubmission).all()
    )

    for submission in water_heater_submissions:
        analysis = submission.analysis

        row: ReportRow = {
            "id": submission.id,
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
            "analysis_complete": analysis is not None,
        }

        rows.append(row)

    return rows


@report_router.get("/")
def get_report_page(
    request: Request,
    address: str,
    db: DbSession,
):
    """_summary_

    Args:
        request (Request): _description_
        address (str): _description_
        db (DbSession): _description_

    Returns:
        _type_: _description_
    """
    all_rows = build_report_rows(db)

    normalized_address = address.strip().lower()

    report_rows = [
        row for row in all_rows
        if row["address"].strip().lower() == normalized_address
    ]

    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "address": address,
            "appliances": report_rows,
        },
    )


@report_router.get("")
def show_report(
    request: Request,
    address: str,
    batch_id: str | None = None,
    completed: bool = False,
    db: Session = Depends(get_db),
):
    hvac_query = db.query(HVACSubmission).filter(
        HVACSubmission.address == address
    )

    water_heater_query = db.query(
        WaterHeaterSubmission
    ).filter(
        WaterHeaterSubmission.address == address
    )

    if batch_id:
        hvac_query = hvac_query.filter(
            HVACSubmission.batch_id == batch_id
        )

        water_heater_query = water_heater_query.filter(
            WaterHeaterSubmission.batch_id == batch_id
        )

    hvac_submissions = hvac_query.all()
    water_heater_submissions = water_heater_query.all()

    rows: list[ReportRow] = build_report_rows(db)

    all_complete = bool(rows) and all(
        row["analysis_complete"]
        for row in rows
    )

    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "address": address,
            "batch_id": batch_id,
            "rows": rows,
            "all_complete": all_complete,
        },
    )