from datetime import date, datetime
import re
from re import Match
from typing import TypedDict, NotRequired
from sqlalchemy.orm import Session

from .ocr_service import NameplateFields
from .recommendation import build_recommendation, ReplacementRecommendation
from core.schema import WaterHeaterAnalysis


class AgeInfo(TypedDict):
    manufacture_year: int
    manufacture_month: int
    age_years: int
    manufacture_week: NotRequired[int]
    plant_code: NotRequired[str]


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


def decode_ao_smith(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    serial = serial.strip().upper()

    if len(serial) < 4:
        return None

    try:
        year = 2000 + int(serial[0:2])
        week = int(serial[2:4])

        if 2008 <= year <= date.today().year and 1 <= week <= 53:
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

        month = int(serial[0])
        year = 2000 + int(serial[1:3])

        if 1 <= month <= 12 and year < 2008:
            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "age_years": calculate_age(year, month),
            }

    except ValueError:
        return None

    return None


def decode_bradford_white(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    serial = serial.upper().strip()

    if len(serial) < 2:
        return None

    year_codes: dict[str, list[int]] = {
        "A": [2004, 2024],
        "B": [2005, 2025],
        "C": [2006, 2026],
        "D": [2007], "E": [2008], "F": [2009], "G": [2010],
        "H": [2011], "J": [2012], "K": [2013], "L": [2014],
        "M": [2015], "N": [2016], "P": [2017], "S": [2018],
        "T": [2019], "W": [2020], "X": [2021], "Y": [2022],
        "Z": [2023],
    }

    month_codes: dict[str, int] = {
        "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6,
        "G": 7, "H": 8, "J": 9, "K": 10, "L": 11, "M": 12,
    }

    year_code = serial[0]
    month_code = serial[1]

    possible_years = year_codes.get(year_code)
    month = month_codes.get(month_code)

    if possible_years is None or month is None:
        return None

    current_year = date.today().year
    valid_years = [year for year in possible_years if year <= current_year]

    if not valid_years:
        return None

    year = max(valid_years)

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_rheem_water_heater(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match is None:
        return None

    month = int(match.group(1))
    year = 2000 + int(match.group(2))

    if not 1 <= month <= 12:
        return None

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_rinnai(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    serial = serial.upper().strip()

    if len(serial) < 5:
        return None

    try:
        plant_code = serial[0]
        year = 2000 + int(serial[1:3])
        week = int(serial[3:5])
    except ValueError:
        return None

    if year > date.today().year or not 1 <= week <= 53:
        return None

    manufacture_date = datetime.strptime(
        f"{year}-W{week}-1",
        "%Y-W%W-%w"
    )
    month = manufacture_date.month

    return {
        "plant_code": plant_code,
        "manufacture_year": year,
        "manufacture_month": month,
        "manufacture_week": week,
        "age_years": calculate_age(year, month),
    }


def decode_water_heater_age_from_brand_serial(
    brand: str,
    serial: str,
) -> AgeInfo | None:
    """_summary_

    Args:
        brand (str): _description_
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    brand = brand.upper().strip()
    serial = serial.upper().strip().replace(" ", "").replace("-", "")

    if not brand or not serial:
        return None

    if "AO SMITH" in brand or "A.O. SMITH" in brand:
        return decode_ao_smith(serial)

    if "BRADFORD WHITE" in brand:
        return decode_bradford_white(serial)

    if "RHEEM" in brand or "RUUD" in brand:
        return decode_rheem_water_heater(serial)

    if "RINNAI" in brand:
        return decode_rinnai(serial)

    return None


def decode_water_heater_age(
    ocr_result: NameplateFields,
) -> AgeInfo | None:
    """_summary_

    Args:
        ocr_result (NameplateFields): _description_

    Returns:
        AgeInfo | None: _description_
    """
    return decode_water_heater_age_from_brand_serial(
        brand=ocr_result.brand,
        serial=ocr_result.serial_number,
    )


def save_water_heater_ocr_results(
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
        _type_: _description_
    """
    analysis = (
        db.query(WaterHeaterAnalysis)
        .filter(WaterHeaterAnalysis.submission_id == submission_id)
        .first()
    )

    if analysis is None:
        analysis = WaterHeaterAnalysis(submission_id=submission_id)
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


def recommend_water_heater_replacement(
    subtype: str | None,
    age_info: AgeInfo | None,
) -> ReplacementRecommendation:
    if age_info is None:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unable to calculate water heater age.",
        )

    age = age_info.get("age_years")

    if age is None:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unable to determine water heater age.",
        )

    if not subtype:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Missing water heater subtype.",
        )

    subtype = subtype.upper().strip()

    if subtype == "TANK":
        return build_recommendation(subtype, age, 8, 10)

    if subtype == "TANKLESS":
        return build_recommendation(subtype, age, 15, 20)

    return ReplacementRecommendation(
        recommendation="Review",
        priority="Manual Review",
        reason="Unsupported water heater subtype.",
    )
