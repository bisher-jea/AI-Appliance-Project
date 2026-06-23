# parsing input of serial number to calculate dates
from datetime import date, datetime
import re
from re import Match
from typing import Any
from .recommendation import build_recommendation, ReplacementRecommendation


def decode_trane(serial) -> dict[str, int] | None:
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
    # Goodman example: 1404123456 = April 2014
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)    # get2 dig  for mth &yr
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


def save_hvac_ocr_results(
    db,
    submission_id,
    ocr_result: dict[str, Any],
    age_info: dict[str, Any] | None,
    recommendation: Any
) -> HVACAnalysis:
    analysis = (
        db.query(HVACAnalysis)
        .filter(HVACAnalysis.submission_id == submission_id)
        .first()
    )

    if not analysis:
        analysis = HVACAnalysis(submission_id=submission_id)
        db.add(analysis)

    analysis.brand = ocr_result.get("brand")
    analysis.model_number = ocr_result.get("model_number")
    analysis.serial_number = ocr_result.get("serial_number")
    analysis.subtype = ocr_result.get("subtype")
    analysis.age = age_info.get("age_years") if age_info else None
    analysis.replacement_recommendation = recommendation.recommendation

    db.commit()
    db.refresh(analysis)

    return analysis


def decode_hvac_age_from_ocr(ocr_result):
    brand = ocr_result.get("brand", "")
    serial = ocr_result.get("serial_number", "")

    return decode_hvac_age(brand, serial)


def recommend_hvac_replacement(subtype: str | None, age_info: dict | None) -> ReplacementRecommendation:
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