from typing import Any
from pydantic import BaseModel


class ReplacementRecommendation(BaseModel):
    recommendation: str
    priority: str
    reason: str


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


def recommend_water_heater_replacement(subtype: str | None, age_info: dict | None) -> ReplacementRecommendation:
    if not age_info:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unable to calculate water heater age."
        )

    age = age_info.get("age_years")

    if not subtype:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Missing water heater subtype."
        )

    subtype = subtype.upper().strip()

    if subtype == "TANK":
        monitor_age = 8
        replace_age = 10

    elif subtype == "TANKLESS":
        monitor_age = 15
        replace_age = 20

    else:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Unsupported water heater subtype."
        )

    return build_recommendation(subtype, age, monitor_age, replace_age)


def build_recommendation(subtype, age, monitor_age, replace_age) -> ReplacementRecommendation:

    if age is None:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Age information is missing."
        )

    if age >= replace_age:
        return ReplacementRecommendation(
            recommendation="Replace",
            priority="High",
            reason=f"{subtype.title()} is approximately {age} years old and has reached typical replacement age."
        )

    if age >= monitor_age:
        return ReplacementRecommendation(
            recommendation="Monitor",
            priority="Medium",
            reason=f"{subtype.title()} is approximately {age} years old and is approaching typical replacement age."
        )

    return ReplacementRecommendation(
        recommendation="No Replacement Needed",
        priority="Low",
        reason=f"{subtype.title()} is approximately {age} years old and is not near typical replacement age."
    )