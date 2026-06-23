from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.operations import get_db
from backend.db import (
    HVACSubmission,
    WaterHeaterSubmission,
    HVACAnalysis,
    WaterHeaterAnalysis
)

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@dashboard_router.get("/")
def get_dashboard(db: Session = Depends(get_db)) -> list[Any]:

    hvac_submissions = db.query(HVACSubmission).all()
    wh_submissions = db.query(WaterHeaterSubmission).all()

    hvac_analysis = db.query(HVACAnalysis).all()
    wh_analysis = db.query(WaterHeaterAnalysis).all()

    hvac_map = {a.submission_id: a for a in hvac_analysis}
    wh_map = {a.submission_id: a for a in wh_analysis}

    dashboard = []

    for s in hvac_submissions:
        a = hvac_map.get(s.id)

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
        a = wh_map.get(s.id)

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