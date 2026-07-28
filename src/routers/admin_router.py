"""
from typing import Annotated
from fastapi.security import HTTPBearer

from fastapi.security import HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import requests
from src.core.auth import require_admin
from src.core.operations import get_db
from src.core.schema import Profile


DbSession = Annotated[Session, Depends(get_db)]
AdminProfile = Annotated[Profile, Depends(require_admin)]


admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


GET    /admin/submissions
GET    /admin/submissions/{submission_id}
PATCH  /admin/hvac/{analysis_id}
PATCH  /admin/water-heaters/{analysis_id}
POST   /admin/hvac/{analysis_id}/recalculate
POST   /admin/water-heaters/{analysis_id}/recalculate
POST   /admin/submissions/{submission_id}/complete-review

@admin_router.get("/submissions")
def get_admin_submissions(
    db: DbSession,
    admin: AdminProfile,
) -> list[dict[str, object]]:
    return build_dashboard_rows(db)


@admin_router.get("/test")
def test_admin_access(
    admin: AdminProfile,
) -> dict[str, str]:
    return {
        "message": "Admin access granted.",
        "user_id": str(admin.id),
        "role": admin.role,
    }
"""