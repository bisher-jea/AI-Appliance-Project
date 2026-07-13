from datetime import date, datetime
import re
from re import Match
from typing import TypedDict, NotRequired
from sqlalchemy.orm import Session

from src.services.ocr_service import NameplateFields
from src.services.recommendation import build_recommendation, ReplacementRecommendation
from src.core.schema import WaterHeaterAnalysis


class AgeInfo(TypedDict):
    manufacture_year: int
    manufacture_month: int
    age_years: int | None
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


def decode_american_water_heater(serial: str) -> AgeInfo | None:
    serial = serial.upper().strip().replace(" ", "")

    # Present: YYWW
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match is None:
        return None

    year = 2000 + int(match.group(1))
    week = int(match.group(2))

    if not (2000 <= year <= date.today().year and 1 <= week <= 53):
        return None

    manufacture_date = datetime.strptime(
        f"{year}-W{week}-1",
        "%G-W%V-%u"
    )
    month = manufacture_date.month

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "manufacture_week": week,
        "age_years": calculate_age(year, month),
    }


def decode_ao_smith(serial: str) -> AgeInfo | None:
    # 3 Options: YYWW, *YYWW, *MYY (pre 2008; month is letter)
    serial = serial.strip().upper()

    if len(serial) < 4:
        return None

    try:
        year = 2000 + int(serial[0:2])
        week = int(serial[2:4])

        if 2008 <= year <= date.today().year and 1 <= week <= 53:
            manufacture_date = datetime.strptime(
                f"{year}-W{week}-1",
                "%G-W%V-%u"
            )

            return {
                "manufacture_year": year,
                "manufacture_month": manufacture_date.month,
                "manufacture_week": week,
                "age_years": calculate_age(year, manufacture_date.month),
            }
    except ValueError:
        pass

        # Pre-2008 format: XMYY

    month_codes = {
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

    if len(serial) >= 4:
        month = month_codes.get(serial[1])

        try:
            yy = int(serial[2:4])
        except ValueError:
            return None

        if month is not None:
            year = 1900 + yy

            if year > date.today().year:
                year -= 100

            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "age_years": calculate_age(year, month),
                }

    return None


def decode_bradford_white(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    # YM (both are letters; skips i, o, q, u)
    serial = serial.upper().strip()

    if len(serial) < 2:
        return None

    year_codes: dict[str, list[int]] = {
        "A": [2004, 2024],   # overlap here sp watch for potential errors
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
    #  MMYY (different from the hvacs)
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
    # YM.**-##### (both year and month are letters; a is 2009, o&p is 2022)
    match: Match[str] | None = re.match(r"^([A-Z])([A-Z])\.?.*-?\d*", serial)

    if match is None:
        return None

    year_codes = {
        "A": 2009,
        "B": 2010,
        "C": 2011,
        "D": 2012,
        "E": 2013,
        "F": 2014,
        "G": 2015,
        "H": 2016,
        "J": 2017,
        "K": 2018,
        "L": 2019,
        "M": 2020,
        "N": 2021,
        "O": 2022,
        "P": 2022,
        "R": 2023,
        "S": 2024,
        "T": 2025,
        "W": 2026,
    }

    month_codes = {
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

    year = year_codes.get(match.group(1))
    month = month_codes.get(match.group(2))

    if year is None or month is None:
        return None

    if year > date.today().year:
        return None

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_state(serial: str) -> AgeInfo | None:
    # Present: YYWW
    # Pre-2008: **YYM
    serial = serial.upper().strip().replace(" ", "")
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match:
        year = 2000 + int(match.group(1))
        week = int(match.group(2))

        if 2008 <= year <= date.today().year and 1 <= week <= 53:
            manufacture_date = datetime.strptime(
                f"{year}-W{week}-1",
                "%G-W%V-%u"
            )
            month = manufacture_date.month

            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "manufacture_week": week,
                "age_years": calculate_age(year, month),
            }

    month_codes = {
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

    match = re.match(r"^..(\d{2})([A-HJ-M])", serial)

    if match:
        yy = int(match.group(1))
        month = month_codes.get(match.group(2))

        if month is None:
            return None

        year = 2000 + yy

        # If somehow the calculated year is after 2007,
        # assume it is from the 1900s.
        if year >= 2008:
            year -= 100

        return {
            "manufacture_year": year,
            "manufacture_month": month,
            "age_years": calculate_age(year, month),
        }

    return None


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

    if "AMERICAN STANDARD" in brand:
        return decode_american_water_heater(serial)

    if "AO SMITH" in brand or "A.O. SMITH" in brand:
        return decode_ao_smith(serial)

    if "BRADFORD WHITE" in brand:
        return decode_bradford_white(serial)

    if "RHEEM" in brand or "RUUD" in brand:
        return decode_rheem_water_heater(serial)

    if "RINNAI" in brand:
        return decode_rinnai(serial)

    if "STATE INDUSTRIES" in brand:
        return decode_state(serial)

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
    analysis.needs_human_review = recommendation.needs_human_review
    analysis.review_reason = (recommendation.reason if recommendation.needs_human_review else ocr_result.review_reason)

    db.commit()
    db.refresh(analysis)

    return None


def recommend_water_heater_replacement(
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
            reason="Unable to calculate water heater age. Please Note AO Smith and Bradford White do not follow a standardized serial number format",
        )

    age = age_info.get("age_years")

    if age is None:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unable to determine water heater age.",
            needs_human_review=True
        )

    if not subtype:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Missing water heater subtype.",
            needs_human_review=True
        )

    subtype = subtype.upper().strip()

    if subtype in ["TANK", "STORAGE TANK", "CONDENSING GAS TANK", "ELECTRIC STORAGE TANK", "ELECTRIC WATER HEATER"]:
        return build_recommendation(subtype, age, 8, 10)

    if subtype in ["TANKLESS", "SOLAR"]:
        return build_recommendation(subtype, age, 15, 20)

    return ReplacementRecommendation(
        recommendation="Review",
        priority="Manual Review",
        reason="Unsupported water heater subtype.",
        needs_human_review=True
    )
