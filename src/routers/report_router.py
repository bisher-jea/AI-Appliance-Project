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


def build_report_rows(db: DbSession) -> list[ReportRow]:
    """_summary_

    Args:
        db (DbSession): _description_

    Returns:
        list[DashboardRow]: _description_
    """
    hvac_submissions = db.query(HVACSubmission).all()
    wh_submissions = db.query(WaterHeaterSubmission).all()

    hvac_analysis = db.query(HVACAnalysis).all()
    wh_analysis = db.query(WaterHeaterAnalysis).all()

    hvac_map = {analysis.submission_id: analysis for analysis in hvac_analysis}
    wh_map = {analysis.submission_id: analysis for analysis in wh_analysis}

    report: list[ReportRow] = []

    for submission in hvac_submissions:
        analysis = hvac_map.get(submission.id)

        report.append({
            "id": str(submission.id),
            "appliance_type": "HVAC",
            "address": submission.address,
            "appliance_number": submission.appliance_number,
            "nameplate_photo": submission.nameplate_photo,
            "brand": analysis.brand if analysis else None,
            "model_number": analysis.model_number if analysis else None,
            "serial_number": analysis.serial_number if analysis else None,
            "age": analysis.age if analysis else None,
            "replacement_recommendation": analysis.replacement_recommendation if analysis else None,
            "subtype": analysis.subtype if analysis else None,
            "needs_human_review": (analysis.needs_human_review if analysis else True),
            "review_reason": (analysis.review_reason if analysis else "Analysis has not completed."),
            "analysis_complete": analysis is not None,
        })

    for submission in wh_submissions:
        analysis = wh_map.get(submission.id)

        report.append({
            "id": str(submission.id),
            "appliance_type": "Water Heater",
            "address": submission.address,
            "appliance_number": submission.appliance_number,
            "nameplate_photo": submission.nameplate_photo,
            "brand": analysis.brand if analysis else None,
            "model_number": analysis.model_number if analysis else None,
            "serial_number": analysis.serial_number if analysis else None,
            "age": analysis.age if analysis else None,
            "replacement_recommendation": analysis.replacement_recommendation if analysis else None,
            "subtype": analysis.subtype if analysis else None,
            "needs_human_review": (analysis.needs_human_review if analysis else True),
            "review_reason": (analysis.review_reason if analysis else "Analysis has not completed."),
            "analysis_complete": analysis is not None,
        })

    return report


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


@report_router.get("/status")
def report_status(
    address: str,
    db: DbSession,
) -> dict[str, bool]:
    all_rows = build_report_rows(db)

    normalized_address = address.strip().lower()

    report_rows = [
        row
        for row in all_rows
        if row["address"].strip().lower() == normalized_address
    ]

    if not report_rows:
        return {"complete": False}

    complete = all(
        row.get("analysis_complete", False)
        for row in report_rows
    )

    return {"complete": complete}