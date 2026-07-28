
from sqlalchemy.orm import Session

from src.core.database import SessionLocal
from src.core.models import (
    HVACSubmission,
    WaterHeaterSubmission,
)
from src.services.hvac_service import (
    decode_hvac_age,
    recommend_hvac_replacement,
    save_hvac_ocr_results,
)
from src.services.ocr_service import process_nameplate
from src.services.storage_service import (
    download_nameplate,
)
from src.services.water_heater_service import (
    decode_water_heater_age,
    recommend_water_heater_replacement,
    save_water_heater_ocr_results,
)


def process_hvac_submission_background(
    submission_id: str,
) -> None:
    """
    Process an HVAC submission after it has been saved.

    The nameplate image is loaded from the directory configured
    by the UPLOAD_DIRECTORY environment variable.
    """
    db: Session = SessionLocal()

    try:
        submission = (
            db.query(HVACSubmission)
            .filter(
                HVACSubmission.id == submission_id
            )
            .first()
        )

        if submission is None:
            print(
                "HVAC submission not found:",
                submission_id,
            )
            return

        object_path = str(
            submission.nameplate_photo
        )

        print(
            "Loading HVAC nameplate:",
            object_path,
        )

        image_bytes = download_nameplate(
            object_path
        )

        if not image_bytes:
            raise ValueError(
                "The HVAC nameplate image is empty."
            )

        ocr_result = process_nameplate(
            image_bytes=image_bytes
        )

        age_info = decode_hvac_age(
            ocr_result
        )

        recommendation = recommend_hvac_replacement(
            subtype=ocr_result.subtype,
            age_info=age_info,
        )

        save_hvac_ocr_results(
            db=db,
            submission_id=str(
                submission.id
            ),
            ocr_result=ocr_result,
            age_info=age_info,
            recommendation=recommendation,
        )

        db.commit()

        print(
            "HVAC submission processed:",
            submission_id,
        )

    except Exception as exc:
        db.rollback()

        print(
            "HVAC background task failed:",
            submission_id,
            type(exc).__name__,
            str(exc),
        )

    finally:
        db.close()


def process_water_heater_submission_background(
    submission_id: str,
) -> None:
    """
    Process a water-heater submission after it has been saved.

    The nameplate image is loaded from the directory configured
    by the UPLOAD_DIRECTORY environment variable.
    """
    db: Session = SessionLocal()

    try:
        submission = (
            db.query(WaterHeaterSubmission)
            .filter(
                WaterHeaterSubmission.id
                == submission_id
            )
            .first()
        )

        if submission is None:
            print(
                "Water heater submission not found:",
                submission_id,
            )
            return

        object_path = str(
            submission.nameplate_photo
        )

        print(
            "Loading water-heater nameplate:",
            object_path,
        )

        image_bytes = download_nameplate(
            object_path
        )

        if not image_bytes:
            raise ValueError(
                "The water-heater nameplate image is empty."
            )

        ocr_result = process_nameplate(
            image_bytes=image_bytes
        )

        age_info = decode_water_heater_age(
            ocr_result
        )

        recommendation = (
            recommend_water_heater_replacement(
                subtype=ocr_result.subtype,
                age_info=age_info,
            )
        )

        save_water_heater_ocr_results(
            db=db,
            submission_id=str(
                submission.id
            ),
            ocr_result=ocr_result,
            age_info=age_info,
            recommendation=recommendation,
        )

        db.commit()

        print(
            "Water heater submission processed:",
            submission_id,
        )

    except Exception as exc:
        db.rollback()

        print(
            "Water heater background task failed:",
            submission_id,
            type(exc).__name__,
            str(exc),
        )

    finally:
        db.close()