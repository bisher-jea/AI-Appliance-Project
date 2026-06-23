# parsing input of serial number to calculate dates
from datetime import date, datetime
import re
from re import Match
from typing import Any


# general age calculation (we only use years for rec)
def calculate_age(manufacture_year, manufacture_month=1) -> Any:
    today: date = date.today()
    years: Any = today.year - manufacture_year

    if today.month < manufacture_month:
        years -= 1
    return years


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
# -----------------------------------------------------------------


# THERE IS 2 VERSIONS: ONE UP TO 2008, AND ONE FOR POST 2008
def decode_ao_smith(serial) -> dict[str, int] | dict[str, int | Any] | None:
    # Pre 2008: xMYY, Post 2008: YYWW
    serial: Any = serial.strip().upper()
    if len(serial) < 4:
        return None

    try:
        # Try post-2008 format first (YYWW)
        year: int = 2000 + int(serial[0:2])
        week: int = int(serial[2:4])
        if (
            year >= 2008 and
            year <= date.today().year and
            1 <= week <= 53
        ):
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

        # Otherwise assume pre-2008 format (MYY)
        month: int = int(serial[0])
        year: int = 2000 + int(serial[1:3])

        if (
            1 <= month <= 12 and
            year < 2008
        ):
            return {
                "manufacture_year": year,
                "manufacture_month": month,
                "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
            }
    except ValueError:
        return None
    return None


def decode_bradford_white(serial) -> dict[str, int] | None:
    year_codes: dict[str, list[int]] = {
        "A": [2004, 2024], "B": [2005, 2025], "C": [2006, 2026], "D": [2007],
        "E": [2008], "F": [2009], "G": [2010], "H": [2011],
        "J": [2012], "K": [2013],
        "L": [2014], "M": [2015], "N": [2016],
        "P": [2017], "S": [2018], "T": [2019],
        "W": [2020], "X": [2021], "Y": [2022], "Z": [2023]
    }

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

    serial: Any = serial.upper().strip()
    if len(serial) < 2:
        return None

    year_code: Any = serial[0]
    month_code: Any = serial[1]

    if year_code not in year_codes:
        return None
    if month_code not in month_codes:
        return None

    possible_years: list[int] = year_codes[year_code]
    current_year = date.today().year

    valid_years: list[int] = [
        year for year in possible_years
        if year <= current_year
    ]

    if not valid_years:
        return None

    year: int = max(valid_years)
    month: int = month_codes[month_code]

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
    }


def decode_rheem_water_heater(serial) -> dict[str, int | Any] | None:
    # Common Rheem format: MMYYxxxxxx
    match: Match[str] | None = re.match(r"^(\d{2})(\d{2})", serial)
    if not match:
        return None

    month: int = int(match.group(1))
    year: int = 2000 + int(match.group(2))

    if month < 1 or month > 12:
        return None

    return {
        "manufacture_year": year,
        "manufacture_month": month,
        "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
    }


def decode_rinnai(serial) -> dict[str, Any | int] | None:
    # Rinnai format: plant code + YY + WW

    serial: Any = serial.upper().strip()

    if len(serial) < 5:
        return None

    try:
        plant_code: Any = serial[0]
        year: int = 2000 + int(serial[1:3])
        week: int = int(serial[3:5])
    except ValueError:
        return None

    if year > date.today().year:
        return None

    if week < 1 or week > 53:
        return None

    manufacture_date: datetime = datetime.strptime(
        f"{year}-W{week}-1",
        "%Y-W%W-%w"
    )

    month = manufacture_date.month

    return {
        "plant_code": plant_code,
        "manufacture_year": year,
        "manufacture_month": month,
        "manufacture_week": week,
        "age_years": calculate_age(manufacture_year=year, manufacture_month=month)
    }

# ---ROUTERS--------------------------------------------------------------


def decode_hvac_age(brand, serial):
    brand = (brand or "").upper().strip()
    serial = (serial or "").upper().replace(" ", "").replace("-", "")

    if "TRANE" in brand or "AMERICAN STANDARD" in brand:
        return decode_trane(serial)

    if "CARRIER" in brand or "BRYANT" in brand or "PAYNE" in brand:
        return decode_carrier(serial)

    if "LENNOX" in brand or "ARMSTRONG" in brand:
        return decode_lennox_armstrong(serial)

    if "GOODMAN" in brand or "AMANA" in brand or "DAIKIN" in brand:
        return decode_goodman(serial)

    if "RHEEM" in brand or "RUUD" in brand:
        return decode_rheem_hvac(serial)

    return None

# Water heaters
def decode_water_heater_age(brand, serial):
    brand = (brand or "").upper().strip()
    serial = (serial or "").upper().replace(" ", "").replace("-", "")

    if "AO SMITH" in brand or "A.O. SMITH" in brand:
        return decode_ao_smith(serial)

    if "BRADFORD WHITE" in brand:
        return decode_bradford_white(serial)

    if "RHEEM" in brand or "RUUD" in brand:
        return decode_rheem_water_heater(serial)

    if "RINNAI" in brand:
        return decode_rinnai(serial)

    return None

def decode_hvac_age_from_ocr(ocr_result):
    brand = ocr_result.get("brand", "")
    serial = ocr_result.get("serial_number", "")

    return decode_hvac_age(brand, serial)


def decode_water_heater_age_from_ocr(ocr_result):
    brand = ocr_result.get("brand", "")
    serial = ocr_result.get("serial_number", "")

    return decode_water_heater_age(brand, serial)