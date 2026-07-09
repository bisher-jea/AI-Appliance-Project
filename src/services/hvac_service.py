from datetime import date, datetime
import re
from re import Match
from typing import TypedDict
from sqlalchemy.orm import Session

from src.services.ocr_service import NameplateFields
from src.services.recommendation import build_recommendation, ReplacementRecommendation
from src.core.schema import HVACAnalysis


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


def decode_american_hvac(serial: str) -> AgeInfo | None:
    # YWW or YYWW or XYYM
    # 1983-2001: YWW
    serial = serial.upper().strip().replace(" ", "").replace("-", "")

    if len(serial) < 3:
        return None

    month_codes = {
        "A": 1, "B": 2, "C": 3, "D": 4,
        "E": 5, "F": 6, "G": 7, "H": 8,
        "J": 9, "K": 10, "L": 11, "M": 12,
    }

    current_year = date.today().year

    # Present format: XYYM
    match = re.match(r"^[A-Z](\d{2})([A-Z])", serial)
    if match:
        year = 2000 + int(match.group(1))
        month_letter = match.group(2)

        if year <= current_year and month_letter in month_codes:
            month = month_codes[month_letter]
            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "age_years": calculate_age(year, month),
            }

    # Present / pre-2001 format: YWW
    match = re.match(r"^(\d)(\d{2})", serial)
    if match:
        year_digit = int(match.group(1))
        week = int(match.group(2))

        if 1 <= week <= 53:
            possible_years = [
                2000 + year_digit,
                2010 + year_digit,
                2020 + year_digit,
                1990 + year_digit,
            ]

            valid_years = [
                year for year in possible_years
                if year <= current_year
            ]

            if valid_years:
                year = max(valid_years)

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

    # Present format: YYW
    match = re.match(r"^(\d{2})(\d)", serial)
    if match:
        year = 2000 + int(match.group(1))
        week = int(match.group(2))

        if year <= current_year and 1 <= week <= 9:
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

    return None


def decode_carrier(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    # WWYY
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


def decode_daikin(serial: str) -> AgeInfo | None:
    serial = serial.upper().strip()

    # Skip first 4 characters, then read YYMM
    match: Match[str] | None = re.match(
        r"^.{4}(\d{2})(\d{2})",
        serial
    )

    if match is None:
        return None

    year = 2000 + int(match.group(1))
    month = int(match.group(2))

    if year > date.today().year:
        return None

    if not 1 <= month <= 12:
        return None

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_goodman(serial: str) -> AgeInfo | None:
    # Present: YYMM
    # Pre-2012: #YM
    serial = serial.upper().strip().replace(" ", "")

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

    # Present: YYMM
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match:
        year = 2000 + int(match.group(1))
        month = int(match.group(2))

        if 2012 <= year <= date.today().year and 1 <= month <= 12:
            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "age_years": calculate_age(year, month),
            }
# Pre-2012: #YM
    # First char is ignored digit, second is year letter, third is month letter
    year_codes = {
        "A": 1990,
        "B": 1991,
        "C": 1992,
        "D": 1993,
        "E": 1994,
        "F": 1995,
        "G": 1996,
        "H": 1997,
        "J": 1998,
        "K": 1999,
        "L": 2000,
        "M": 2001,
        "N": 2002,
        "P": 2003,
        "Q": 2004,
        "R": 2005,
        "S": 2006,
        "T": 2007,
        "U": 2008,
        "V": 2009,
        "W": 2010,
        "X": 2011,
        "Y": 2012,
        "Z": 2013,
    }

    match = re.match(r"^\d([A-HJ-NPR-TV-Z])([A-HJ-M])", serial)

    if match:
        year = year_codes.get(match.group(1))
        month = month_codes.get(match.group(2))

        if year is not None and month is not None:
            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "age_years": calculate_age(year, month),
            }

    return None


def decode_icp(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    # *YYWW
    serial = serial.upper().strip().replace(" ", "")
    match = re.match(r"^[A-Z](\d{2})(\d{2})", serial)
    if match is None:
        return None
   
    year_short = int(match.group(1))
    week = int(match.group(2))

    current_year_short = date.today().year % 100
    year = (2000 + year_short) if year_short <= current_year_short else (1900 + year_short)

    # Validate calendar boundaries
    if year > date.today().year or not (1 <= week <= 53):
        return None

    # 52 weeks / 12 months = ~4.33 weeks per month
    month = max(1, min(12, int((week - 1) / 4.33) + 1))

    return {
        "manufacture_year": year,
        "manufacture_week": week,
        "manufacture_month": month,
        "age_years": calculate_age(year, month),
    }


def decode_lennox(serial: str) -> AgeInfo | None:
    """_summary_

    Args:
        serial (str): _description_

    Returns:
        AgeInfo | None: _description_
    """
    # **YYM
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


def decode_rheem_hvac(serial: str) -> AgeInfo | None:
    serial = serial.upper().strip().replace(" ", "")

    # Formats:
    # ****FWWYY
    # *WWYY
    # ####*WWYY
    match: Match[str] | None = re.search(r"(?:F|\*)(\d{2})(\d{2})", serial)

    if match is None:
        return None

    week = int(match.group(1))
    year = 2000 + int(match.group(2))

    if not 1 <= week <= 53 or year > date.today().year:
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


def decode_trane(serial: str) -> AgeInfo | None:
    # YWW or YYWW or *YYM (month is letter)
    # 1983-2001: YWW (year is letter)
    serial = serial.upper().strip().replace(" ", "")

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

    year_codes = {
        "W": 1983,
        "X": 1984,
        "Y": 1985,
        "S": 1986,
        "B": 1987,
        "C": 1988,
        "D": 1989,
        "E": 1990,
        "F": 1991,
        "G": 1992,
        "H": 1993,
        "J": 1994,
        "K": 1995,
        "L": 1996,
        "M": 1997,
        "N": 1998,
        "P": 1999,
        "R": 2000,
        "Z": 2001,
    }

    # Present: YYWW
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)

    if match:
        year = 2000 + int(match.group(1))
        week = int(match.group(2))

        if 2010 <= year <= date.today().year and 1 <= week <= 53:
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

    # Present: YWW
    match = re.match(r"^(\d)(\d{2})", serial)

    if match:
        year_digit = int(match.group(1))
        week = int(match.group(2))
        current_year = date.today().year

        possible_years = [
            2000 + year_digit,
            2010 + year_digit,
            2020 + year_digit,
        ]

        year = max(y for y in possible_years if y <= current_year)

        if 2010 <= year <= current_year and 1 <= week <= 53:
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

    # Present: *YYM, month is letter
    match = re.match(r"^[A-Z](\d{2})([A-HJ-M])", serial)

    if match:
        year = 2000 + int(match.group(1))
        month = month_codes.get(match.group(2))

        if month is not None and 2002 <= year <= date.today().year:
            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "age_years": calculate_age(year, month),
            }

    # 1983-2001: YWW, year is letter
    match = re.match(r"^([A-Z])(\d{2})", serial)

    if match:
        year = year_codes.get(match.group(1))
        week = int(match.group(2))

        if year is not None and 1 <= week <= 53:
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

    return None


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

    if brand in ["AMERICAN STANDARD", "AMERICAN"]:
        return decode_american_hvac(serial)

    if brand in ["CARRIER", "BRYANT", "PAYNE"]:
        return decode_carrier(serial)

    if brand in ["DAIKIN"]:
        return decode_daikin(serial)

    if brand in ["GOODMAN", "AMANA"]:
        return decode_goodman(serial)

    if brand in ["INTERNATIONAL COMFORT PRODUCTS", "ICP"]:
        return decode_icp(serial)

    if brand in ["LENNOX"]:
        return decode_lennox(serial)

    if brand in ["RHEEM", "RUUD"]:
        return decode_rheem_hvac(serial)
    
    if brand in ["TRANE"]:
        return decode_trane(serial)
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
