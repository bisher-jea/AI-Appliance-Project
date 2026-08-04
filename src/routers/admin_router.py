from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    status,
    Response,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from src.core.database import get_db
from src.core.models import (
    HVACAnalysis, WaterHeaterAnalysis, 
    HVACSubmission, WaterHeaterSubmission)
from src.core.models import DashboardAccessLog
from src.core.models import DashboardActivityLog


admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

templates = Jinja2Templates(
    directory="frontend/templates",
)


def normalize_jea_email(
    email: str,
) -> str | None:
    normalized_email = email.strip().lower()

    local_part, separator, domain = normalized_email.rpartition("@")

    if (
        separator != "@"
        or not local_part
        or domain != "jea.com"
    ):
        return None

    return normalized_email


def get_logged_in_email(
    request: Request,
) -> str | None:
    email = request.session.get("dashboard_email")

    if not isinstance(email, str):
        return None

    return normalize_jea_email(email)


def require_dashboard_email(
    request: Request,
) -> str:
    email = get_logged_in_email(request)

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dashboard login required.",
        )

    return email


def build_dashboard_rows(
    db: Session,
    search: str | None = None,
    needs_review: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    hvac_statement = (
        select(HVACSubmission)
        .options(
            selectinload(HVACSubmission.analysis),
        )
        .order_by(
            HVACSubmission.address.asc(),
            HVACSubmission.appliance_number.asc(),
        )
    )

    water_heater_statement = (
        select(WaterHeaterSubmission)
        .options(
            selectinload(WaterHeaterSubmission.analysis),
        )
        .order_by(
            WaterHeaterSubmission.address.asc(),
            WaterHeaterSubmission.appliance_number.asc(),
        )
    )

    hvac_submissions = db.scalars(
        hvac_statement,
    ).all()

    water_heater_submissions = db.scalars(
        water_heater_statement,
    ).all()

    for submission in hvac_submissions:
        analysis = submission.analysis

        row = {
            "submission_id": submission.id,
            "appliance_type": "hvac",
            "appliance_type_label": "HVAC",
            "address": submission.address,
            "appliance_number": submission.appliance_number,
            "nameplate_photo": submission.nameplate_photo,
            "brand": analysis.brand if analysis else "",
            "model_number": (
                analysis.model_number if analysis else ""
            ),
            "serial_number": (
                analysis.serial_number if analysis else ""
            ),
            "subtype": analysis.subtype if analysis else "",
            "age": analysis.age if analysis else None,
            "replacement_recommendation": (
                analysis.replacement_recommendation
                if analysis
                else ""
            ),
            "needs_human_review": (
                analysis.needs_human_review
                if analysis
                else True
            ),
            "review_reason": (
                analysis.review_reason if analysis else ""
            ),
            "analysis_complete": (
                analysis.analysis_complete
                if analysis
                else False
            ),
        }

        rows.append(row)

    for submission in water_heater_submissions:
        analysis = submission.analysis

        row = {
            "submission_id": submission.id,
            "appliance_type": "water_heater",
            "appliance_type_label": "Water Heater",
            "address": submission.address,
            "appliance_number": submission.appliance_number,
            "nameplate_photo": submission.nameplate_photo,
            "brand": analysis.brand if analysis else "",
            "model_number": (
                analysis.model_number if analysis else ""
            ),
            "serial_number": (
                analysis.serial_number if analysis else ""
            ),
            "subtype": analysis.subtype if analysis else "",
            "age": analysis.age if analysis else None,
            "replacement_recommendation": (
                analysis.replacement_recommendation
                if analysis
                else ""
            ),
            "needs_human_review": (
                analysis.needs_human_review
                if analysis
                else True
            ),
            "review_reason": (
                analysis.review_reason if analysis else ""
            ),
            "analysis_complete": (
                analysis.analysis_complete
                if analysis
                else False
            ),
        }

        rows.append(row)

    if needs_review:
        rows = [
            row
            for row in rows
            if row["needs_human_review"]
        ]

    if search:
        normalized_search = search.strip().lower()

        rows = [
            row
            for row in rows
            if normalized_search
            in " ".join(
                [
                    str(row["address"]),
                    str(row["brand"]),
                    str(row["model_number"]),
                    str(row["serial_number"]),
                    str(row["subtype"]),
                    str(row["replacement_recommendation"]),
                    str(row["appliance_type_label"]),
                ]
            ).lower()
        ]

    return rows


@admin_router.get(
    "/login",
    response_class=HTMLResponse,
)
def get_admin_login(
    request: Request,
) -> Response:
    if get_logged_in_email(request):
        return RedirectResponse(
            url="/admin/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={
            "error": None,
            "entered_email": "",
        },
    )


@admin_router.post(
    "/login",
    response_class=HTMLResponse,
)
def submit_admin_login(
    request: Request,
    email: Annotated[str, Form()],
    db: Session = Depends(get_db),
) -> Response:
    normalized_email = normalize_jea_email(email)

    if normalized_email is None:
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "error": (
                    "Please enter a valid @jea.com email address."
                ),
                "entered_email": email,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    db.add(
        DashboardAccessLog(
            email=normalized_email,
        )
    )
    db.commit()

    request.session["dashboard_email"] = normalized_email

    return RedirectResponse(
        url="/admin/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.get(
    "/dashboard",
    response_class=HTMLResponse,
)
def get_admin_dashboard(
    request: Request,
    search: Annotated[str | None, Query()] = None,
    needs_review: Annotated[bool, Query()] = False,
    saved: Annotated[bool, Query()] = False,
    db: Session = Depends(get_db),
    deleted: Annotated[bool, Query()] = False,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    dashboard_email = get_logged_in_email(request)

    if dashboard_email is None:
        return RedirectResponse(
            url="/admin/login",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    rows = build_dashboard_rows(
        db=db,
        search=search,
        needs_review=needs_review,
    )

    total_records = len(rows)

    review_count = sum(
        1
        for row in rows
        if row["needs_human_review"]
    )

    complete_count = sum(
        1
        for row in rows
        if row["analysis_complete"]
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "dashboard_email": dashboard_email,
            "rows": rows,
            "search": search or "",
            "needs_review_filter": needs_review,
            "saved": saved,
            "total_records": total_records,
            "review_count": review_count,
            "complete_count": complete_count,
            "deleted": deleted,
            "error": error,
        },
    )


@admin_router.post("/dashboard/update")
def update_dashboard_record(
    request: Request,
    appliance_type: Annotated[str, Form()],
    submission_id: Annotated[str, Form()],
    brand: Annotated[str, Form()] = "",
    model_number: Annotated[str, Form()] = "",
    serial_number: Annotated[str, Form()] = "",
    subtype: Annotated[str, Form()] = "",
    age: Annotated[str, Form()] = "",
    replacement_recommendation: Annotated[str, Form()] = "",
    review_reason: Annotated[str, Form()] = "",
    needs_human_review: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    dashboard_email = get_logged_in_email(request)

    if dashboard_email is None:
        return RedirectResponse(
            url="/admin/login",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    normalized_type = (
        appliance_type
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


    print("UPDATE appliance_type:", repr(normalized_type))
    print("UPDATE submission_id:", repr(submission_id))
    if normalized_type == "hvac":
        analysis = db.scalar(
            select(HVACAnalysis).where(
                HVACAnalysis.submission_id == submission_id
            )
        )

    elif normalized_type == "water_heater":
        analysis = db.scalar(
            select(WaterHeaterAnalysis).where(
                WaterHeaterAnalysis.submission_id == submission_id
            )
        )

    else:
        return RedirectResponse(
            url=(
                "/admin/dashboard"
                "?error=invalid_appliance_type"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    print("FOUNDANALYSIS", analysis)

    if analysis is None:
        if normalized_type == "hvac":
            analysis = HVACAnalysis(
                    submission_id=submission_id,
            )
        else:
            analysis = WaterHeaterAnalysis(
                submission_id=submission_id,
            )
        db.add(analysis)
    cleaned_age: int | None = None

    if age.strip():
        try:
            cleaned_age = int(age.strip())

            if cleaned_age < 0:
                raise ValueError

        except ValueError:
            return RedirectResponse(
                url="/admin/dashboard?error=invalid_age",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    analysis.brand = brand.strip() or None
    analysis.model_number = model_number.strip() or None
    analysis.serial_number = serial_number.strip() or None
    analysis.subtype = subtype.strip() or None
    analysis.age = cleaned_age

    analysis.replacement_recommendation = (
        replacement_recommendation.strip() or None
    )

    analysis.review_reason = (
        review_reason.strip() or None
    )

    analysis.needs_human_review = (
        needs_human_review is not None
    )

    analysis.analysis_complete = True

    try:
        db.add(
            DashboardActivityLog(
                email=dashboard_email,
                action=f"updated {normalized_type} submission",
                submission_id=submission_id,
            )
        )

        db.commit()

    except Exception as exc:
        db.rollback()

        print(
            "Dashboard update failed:",
            repr(exc),
        )

        return RedirectResponse(
            url="/admin/dashboard?error=update_failed",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/admin/dashboard?saved=true",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post(
    "/logout",
)
def logout_admin(
    request: Request,
) -> RedirectResponse:
    request.session.clear()

    return RedirectResponse(
        url="/admin/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/dashboard/delete")
def delete_dashboard_record(
    request: Request,
    appliance_type: Annotated[str, Form()],
    submission_id: Annotated[str, Form()],
    db: Session = Depends(get_db),
) -> RedirectResponse:
    dashboard_email = get_logged_in_email(request)

    if dashboard_email is None:
        return RedirectResponse(
            url="/admin/login",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    normalized_type = (
        appliance_type
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if normalized_type == "hvac":
        submission = db.scalar(
            select(HVACSubmission)
            .options(
                selectinload(HVACSubmission.analysis)
            )
            .where(
                HVACSubmission.id == submission_id
            )
        )

    elif normalized_type == "water_heater":
        submission = db.scalar(
            select(WaterHeaterSubmission)
            .options(
                selectinload(
                    WaterHeaterSubmission.analysis
                )
            )
            .where(
                WaterHeaterSubmission.id == submission_id
            )
        )

    else:
        return RedirectResponse(
            url=(
                "/admin/dashboard"
                "?error=invalid_appliance_type"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if submission is None:
        return RedirectResponse(
            url="/admin/dashboard?error=submission_not_found",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        # Delete analysis first unless the relationship
        # already uses cascade="all, delete-orphan".
        if submission.analysis is not None:
            db.delete(submission.analysis)

        db.delete(submission)

        db.add(
            DashboardActivityLog(
                email=dashboard_email,
                action=f"deleted {normalized_type} submission",
                submission_id=submission_id,
            )
        )

        db.commit()

    except Exception as exc:
        db.rollback()

        print(
            "Dashboard deletion failed:",
            repr(exc),
        )

        return RedirectResponse(
            url="/admin/dashboard?error=delete_failed",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/admin/dashboard?deleted=true",
        status_code=status.HTTP_303_SEE_OTHER,
    )