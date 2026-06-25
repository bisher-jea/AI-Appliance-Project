from sqlalchemy.orm import Session

from core.operations import ENGINE
from core.schema import (
    HVACSubmission,
    WaterHeaterSubmission,
)

from services.ocr_service import process_nameplate
from services.hvac_service import (
    decode_hvac_age,
    recommend_hvac_replacement,
    save_hvac_ocr_results,
)

from services.water_heater_service import (
    decode_water_heater_age,
    recommend_water_heater_replacement,
    save_water_heater_ocr_results,
)

db = Session(bind=ENGINE)

# Implementing background tasks to help with scalability


def process_hvac_submission_background(submission_id: str) -> None:
    """_summary_

    Args:
        submission_id (str): _description_
    """
    with Session(bind=ENGINE) as db:
        submission = (
            db.query(HVACSubmission)
            .filter(HVACSubmission.id == submission_id)
            .first()
        )

        if submission is None:
            return

        ocr_result = process_nameplate(str(submission.nameplate_photo))

        age_info = decode_hvac_age(ocr_result)

        recommendation = recommend_hvac_replacement(
            subtype=ocr_result.subtype,
            age_info=age_info,
        )

        save_hvac_ocr_results(
            db=db,
            submission_id=str(submission.id),
            ocr_result=ocr_result,
            age_info=age_info,
            recommendation=recommendation,
        )


def process_water_heater_submission_background(submission_id: str) -> None:
    """

    Args:
        submission_id (str): _description_
    """
    with Session(bind=ENGINE) as db:
        submission = (
            db.query(WaterHeaterSubmission)
            .filter(WaterHeaterSubmission.id == submission_id)
            .first()
        )

        if submission is None:
            return

        ocr_result = process_nameplate(str(submission.nameplate_photo))

        age_info = decode_water_heater_age(ocr_result)

        recommendation = recommend_water_heater_replacement(
            subtype=ocr_result.subtype,
            age_info=age_info,
        )

        save_water_heater_ocr_results(
            db=db,
            submission_id=str(submission.id),
            ocr_result=ocr_result,
            age_info=age_info,
            recommendation=recommendation,
        )
