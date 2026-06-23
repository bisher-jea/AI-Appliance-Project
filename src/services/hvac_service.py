from datetime import date, datetime
import re
from re import Match
from typing import Any

from .ocr_service import NameplateFields
from .recommendation import build_recommendation, ReplacementRecommendation
from .schema import HVACAnalysis


def decode_trane(serial) -> dict[str, int] | None:
    """_summary_

    Args:
        serial (_type_): _description_

    Returns:
        dict[str, int] | None: _description_
    """
    serial: Any = serial.upper().strip()

    # New format (2010+)
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match:

        year: int = 2000 + int(match.group(1))
        week: int = int(match.group(2))

        if (
            year >= 2010 and
            year <= date.today().year and
            1 <= week <= 53
        ):

            manufacture_date: datetime = datetime.strptime(
                f"{year}-W{week}-1",
                "%Y-W%W-%w"
            )

            month = manufacture_date.month

            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "manufacture_week": week,
                "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
            }

    # Old format (2002-2010)
    match: Match[str] | None = re.match(r"^[A-Z](\d{2})", serial)

    if match:

        year: int = 2000 + int(match.group(1))

        if 2002 <= year <= 2010:

            return {
                "manufacture_year": year,
                "manufacture_month": 1,  # Unknown
                "age_years": calculate_age(manufacture_year=year, manufacture_month=1)
            }

    return None


# there are multiple serial codes for carrier, this is just the modern one
def decode_carrier(serial) -> dict[str, int | Any] | None:
    """_summary_

    Args:
        serial (_type_): _description_

    Returns:
        dict[str, int | Any] | None: _description_
    """
    # Carrier/Bryant example: 2414E12345 = 24th week of 2014
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)
    if not match:
        return None

    week: int = int(match.group(1))
    year: int = 2000 + int(match.group(2))

    # to help determine if modern serial version
    current_year: int = date.today().year
    if year > current_year:
        return None

    if week < 1 or week > 53:
        return None

    manufacture_date: datetime = datetime.strptime(
        f"{year}-W{week}-1",
        "%Y-W%W-%w"
    )

    month: int = manufacture_date.month

    return {
        "manufacture_year": year,
        "manufacture_week": week,
        "manufacture_month": month,
        "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
    }


def decode_lennox_armstrong(serial) -> dict[str, int] | None:
    """_summary_

    Args:
        serial (_type_): _description_

    Returns:
        dict[str, int] | None: _description_
    """
    # Lennox: PPYYM
    serial = serial.upper().strip()

    if len(serial) < 5:
        return None

    year_digits: Any = serial[2:4]
    month_letter: Any = serial[4]

    try:
        year = 2000 + int(year_digits)

        # Handle older units
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
        "M": 12
    }

    if month_letter not in month_codes:
        return None

    month = month_codes[month_letter]

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
    }


def decode_goodman(serial) -> dict[str, int | Any] | None:
    """_summary_

    Args:
        serial (_type_): _description_

    Returns:
        dict[str, int | Any] | None: _description_
    """
    # Goodman example: 1404123456 = April 2014
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)
    if not match:
        return None

    year: int = 2000 + int(match.group(1))
    month: int = int(match.group(2))

    if month < 1 or month > 12:
        return None

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
    }


def decode_rheem_hvac(serial) -> dict[str, int] | None:
    """_summary_

    Args:
        serial (_type_): _description_

    Returns:
        dict[str, int] | None: _description_
    """
    # Format 1: Plant code + WW + YY
    # Format 2: 7 digits + plant code + WW + YY

    serial = serial.upper().strip().replace(" ", "")

    # Format 2: 3333333*WWYY
    match: Match[str] | None = re.search(r"\*(\d{2})(\d{2})", serial)

    if match:
        week: int = int(match.group(1))
        year: int = 2000 + int(match.group(2))

    else:
        # Format 1: Plant + WWYY
        match: Match[str] | None = re.match(r"^[A-Z](\d{2})(\d{2})", serial)

        if not match:
            return None

        week: int = int(match.group(1))
        year: int = 2000 + int(match.group(2))

    if week < 1 or week > 53:
        return None

    if year > date.today().year:
        return None

    manufacture_date: datetime = datetime.strptime(
        f"{year}-W{week}-1",
        "%Y-W%W-%w"
    )

    month: int = manufacture_date.month

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "manufacture_week": week,
        "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
    }


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


def decode_hvac_age_from_brand_serial(brand: str, serial: str) -> dict[str, Any] | None:
    """_summary_

    Args:
        brand (str): _description_
        serial (str): _description_

    Returns:
        dict[str, Any] | None: _description_
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


def decode_hvac_age(ocr_result: NameplateFields) -> dict[str, Any] | None:
    """_summary_

    Args:
        ocr_result (NameplateFields): _description_

    Returns:
        dict[str, Any] | None: _description_
    """
    return decode_hvac_age_from_brand_serial(
        brand=ocr_result.brand,
        serial=ocr_result.serial_number
    )


def save_hvac_ocr_results(db, submission_id: int, ocr_result: NameplateFields, age_info: dict[str, Any] | None,
recommendation: ReplacementRecommendation) -> HVACAnalysis:
    """_summary_

    Args:
        db (_type_): _description_
        submission_id (int): _description_
        ocr_result (NameplateFields): _description_
        age_info (dict[str, Any] | None): _description_
        recommendation (ReplacementRecommendation): _description_

    Returns:
        HVACAnalysis: _description_
    """
    analysis = (
        db.query(HVACAnalysis)
        .filter(HVACAnalysis.submission_id == submission_id)
        .first()
    )

    if not analysis:
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

    return analysis


def recommend_hvac_replacement(subtype: str | None, age_info: dict[str, Any] | None) -> ReplacementRecommendation:
    """_summary_

    Args:
        subtype (str | None): _description_
        age_info (dict[str, Any] | None): _description_

    Returns:
        ReplacementRecommendation: _description_
    """
    if not age_info:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unable to calculate HVAC age."
        )

    age = age_info.get("age_years")

    if not subtype:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Missing HVAC subtype."
        )

    subtype = subtype.upper().strip()

    if subtype in ["AIR CONDITIONER", "HEAT PUMP", "AIR HANDLER"]:
        monitor_age = 12
        replace_age = 15

    elif subtype == "FURNACE":
        monitor_age = 15
        replace_age = 20

    else:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unsupported HVAC subtype."
        )

    return build_recommendation(subtype, age, monitor_age, replace_age)