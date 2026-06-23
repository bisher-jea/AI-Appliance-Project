from pydantic import BaseModel


class ReplacementRecommendation(BaseModel):
    recommendation: str
    priority: str
    reason: str


def build_recommendation(subtype, age, monitor_age, replace_age) -> ReplacementRecommendation:
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