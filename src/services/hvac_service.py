from datetime import date, datetime
import re
from re import Match
from typing import TypedDict
from sqlalchemy.orm import Session

from .ocr_service import NameplateFields
from .recommendation import build_recommendation, ReplacementRecommendation
from core.schema import HVACAnalysis


class AgeInfo(TypedDict, total=False):
    manufacture_year: int
    manufacture_month: int
    manufacture_week: int
    age_years: int


def calculate_age(manufacture_year: int, manufacture_month: int = 1) -> int:
    """_summary_

    Args:
        manufacture_year (int): _description_
        manufacture_month (int, optional): _description_. Defaults to 1.

    Returns:
        int: _description_
    """
    today = date.today()
    age = today.year - manufacture_year

    if today.month < manufacture_month:
        age -= 1

    return age


def decode_trane(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    serial = serial.upper().strip()

    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match:
        year = 2000 + int(match.group(1))
        week = int(match.group(2))

        if 2010 <= year <= date.today().year and 1 <= week <= 53:
            manufacture_date = datetime.strptime(
                f"{year}-W{week}-1",
                "%Y-W%W-%w"
            )
            month = manufacture_date.month

            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "manufacture_week": week,
                "age_years": calculate_age(year, month),
            }

    match = re.match(r"^[A-Z](\d{2})", serial)

    if match:
        year = 2000 + int(match.group(1))

        if 2002 <= year <= 2010:
            return {
                "manufacture_year": year,
                "manufacture_month": 1,
                "age_years": calculate_age(year, 1),
            }

    return None


def decode_carrier(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match is None:
        return None

    week = int(match.group(1))
    year = 2000 + int(match.group(2))

    if year > date.today().year or not 1 <= week <= 53:
        return None

    manufacture_date = datetime.strptime(
        f"{year}-W{week}-1",
        "%Y-W%W-%w"
    )
    month = manufacture_date.month

    return {
        "manufacture_year": year,
        "manufacture_week": week,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_lennox_armstrong(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    serial = serial.upper().strip()

    if len(serial) < 5:
        return None

    year_digits = serial[2:4]
    month_letter = serial[4]

    try:
        year = 2000 + int(year_digits)

        if year > date.today().year:
            year = 1900 + int(year_digits)
    except ValueError:
        return None

    month_codes: dict[str, int] = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "J": 9,
        "K": 10,
        "L": 11,
        "M": 12,
    }

    month = month_codes.get(month_letter)

    if month is None:
        return None

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_goodman(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match is None:
        return None

    year = 2000 + int(match.group(1))
    month = int(match.group(2))

    if not 1 <= month <= 12:
        return None

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_rheem_hvac(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    serial = serial.upper().strip().replace(" ", "")

    match: Match[str] | None = re.search(r"\*(\d{2})(\d{2})", serial)

    if match:
        week = int(match.group(1))
        year = 2000 + int(match.group(2))
    else:
        match = re.match(r"^[A-Z](\d{2})(\d{2})", serial)

        if match is None:
            return None

        week = int(match.group(1))
        year = 2000 + int(match.group(2))

    if not 1 <= week <= 53 or year > date.today().year:
        return None

    manufacture_date = datetime.strptime(
        f"{year}-W{week}-1",
        "%Y-W%W-%w"
    )
    month = manufacture_date.month

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "manufacture_week": week,
        "age_years": calculate_age(year, month),
    }


def decode_hvac_age_from_brand_serial(
    brand: str,
    serial: str
) -> AgeInfo | None:
    """_summary_

    Args:
        brand (str): _description_
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    brand = brand.upper().strip()
    serial = serial.upper().strip()

    if not brand or not serial:
        return None

    if brand in ["TRANE", "AMERICAN STANDARD"]:
        return decode_trane(serial)

    if brand in ["CARRIER", "BRYANT", "PAYNE"]:
        return decode_carrier(serial)

    if brand in ["LENNOX", "ARMSTRONG"]:
        return decode_lennox_armstrong(serial)

    if brand in ["GOODMAN", "AMANA", "DAIKIN"]:
        return decode_goodman(serial)

    if brand in ["RHEEM", "RUUD"]:
        return decode_rheem_hvac(serial)

    return None


def decode_hvac_age(ocr_result: NameplateFields) -> AgeInfo | None:
    """_summary_

    Args:
        ocr_result (NameplateFields): _description_

    Returns:
        AgeInfo | None: _description_
    """
    return decode_hvac_age_from_brand_serial(
        brand=ocr_result.brand,
        serial=ocr_result.serial_number,
    )


def save_hvac_ocr_results(
    db: Session,
    submission_id: str,
    ocr_result: NameplateFields,
    age_info: AgeInfo | None,
    recommendation: ReplacementRecommendation,
) -> None:
    """_summary_

    Args:
        db (Session): _description_
        submission_id (str): _description_
        ocr_result (NameplateFields): _description_
        age_info (AgeInfo | None): _description_
        recommendation (ReplacementRecommendation): _description_

    Returns:
        HVACAnalysis: _description_
    """
    analysis = (
        db.query(HVACAnalysis)
        .filter(HVACAnalysis.submission_id == submission_id)
        .first()
    )

    if analysis is None:
        analysis = HVACAnalysis(submission_id=submission_id)
        db.add(analysis)

    analysis.brand = ocr_result.brand
    analysis.model_number = ocr_result.model_number
    analysis.serial_number = ocr_result.serial_number
    analysis.subtype = ocr_result.subtype
    analysis.age = age_info.get("age_years") if age_info else None
    analysis.replacement_recommendation = recommendation.recommendation

    db.commit()
    db.refresh(analysis)

    return None


def recommend_hvac_replacement(
    subtype: str | None,
    age_info: AgeInfo | None,
) -> ReplacementRecommendation:
    """_summary_

    Args:
        subtype (str | None): _description_
        age_info (AgeInfo | None): _description_

    Returns:
        ReplacementRecommendation: _description_
    """
    if age_info is None:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unable to calculate HVAC age.",
        )

    age = age_info.get("age_years")

    if age is None:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unable to determine HVAC age."
        )

    if not subtype:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Missing HVAC subtype.",
        )

    subtype = subtype.upper().strip()

    if subtype in ["AIR CONDITIONER", "HEAT PUMP", "AIR HANDLER"]:
        return build_recommendation(subtype, age, 12, 15)

    if subtype == "FURNACE":
        return build_recommendation(subtype, age, 15, 20)

    return ReplacementRecommendation(
        recommendation="Review",
        priority="Manual Review",
        reason="Unsupported HVAC subtype.",
    )
