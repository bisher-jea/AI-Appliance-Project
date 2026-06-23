from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.operations import get_db
from core.db import HVACAnalysisResponse, HVACSubmissionResponse, WaterHeaterAnalysisResponse, WaterHeaterSubmissionResponse

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@dashboard_router.get("/")
def get_dashboard(db: Session = Depends(get_db)) -> list[Any]:
    """_summary_

    Args:
        db (Session, optional): _description_. Defaults to Depends(get_db).

    Returns:
        list[Any]: _description_
    """
    hvac_submissions: List[Any] = db.query(HVACSubmissionResponse).all()
    wh_submissions: List[Any] = db.query(WaterHeaterSubmissionResponse).all()

    hvac_analysis = db.query(HVACAnalysisResponse).all()
    wh_analysis = db.query(WaterHeaterAnalysisResponse).all()

    hvac_map: dict[Any, Any] = {a.submission_id: a for a in hvac_analysis}
    wh_map: dict[Any, Any] = {a.submission_id: a for a in wh_analysis}

    dashboard: list[Any] = []

    for s in hvac_submissions:
        a: Any | None = hvac_map.get(s.id)

        dashboard.append({
            "id": s.id,
            "appliance_type": "HVAC",
            "address": s.address,
            "appliance_number": s.appliance_number,
            "nameplate_photo": s.nameplate_photo,
            "brand": a.brand if a else None,
            "model_number": a.model_number if a else None,
            "serial_number": a.serial_number if a else None,
            "age": a.age if a else None,
            "replacement_recommendation": a.replacement_recommendation if a else None,
            "subtype": a.subtype if a else None,
        })

    for s in wh_submissions:
        a: Any | None: Any | None = wh_map.get(s.id)

        dashboard.append({
            "id": s.id,
            "appliance_type": "Water Heater",
            "address": s.address,
            "appliance_number": s.appliance_number,
            "nameplate_photo": s.nameplate_photo,
            "brand": a.brand if a else None,
            "model_number": a.model_number if a else None,
            "serial_number": a.serial_number if a else None,
            "age": a.age if a else None,
            "replacement_recommendation": a.replacement_recommendation if a else None,
            "subtype": a.subtype if a else None,
        })

    return dashboard