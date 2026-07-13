from pydantic import BaseModel


class ReplacementRecommendation(BaseModel):
    recommendation: str
    priority: str
    reason: str
    needs_human_review: bool = False


def build_recommendation(subtype: str, age: int | None, monitor_age: int, replace_age: int) -> ReplacementRecommendation:
    """_summary_

    Args:
        subtype (_type_): _description_
        age (_type_): _description_
        monitor_age (_type_): _description_
        replace_age (_type_): _description_

    Returns:
        ReplacementRecommendation: _description_
    """
    if age is None:
        return ReplacementRecommendation(
            recommendation="Review",
            priority="Manual Review",
            reason="Age information is missing. Please note some brands do not use a single standard format for serial numbers (AO Smith, American Standard, Rheem, Trane)"
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
        reason=f"{subtype.title()} is approximately {age} years old and is not near typical replacement age.",
        needs_human_review=False
    )