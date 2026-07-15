import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session
from supabase import Client, create_client

from .operations import get_db
from .schema import Profile


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_ANON_KEY must be configured."
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
)

security = HTTPBearer()

DbSession = Annotated[Session, Depends(get_db)]

BearerCredentials = Annotated[
    HTTPAuthorizationCredentials,
    Depends(security),
]


def get_authenticated_user_id(
    credentials: BearerCredentials,
) -> str:
    """"Verifies supabase token and returns user id"""

    token = credentials.credentials

    try:
        response = supabase.auth.get_claims(token)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    claims = response.claims

    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to read authentication claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing a user ID.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return str(user_id)


def require_admin(
    user_id: Annotated[
        str,
        Depends(get_authenticated_user_id),
    ],
    db: DbSession,
) -> Profile:
    """ Finds user profile and checks if admin"""

    profile = (
        db.query(Profile)
        .filter(Profile.id == user_id)
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No application profile exists for this user.",
        )

    if profile.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is required.",
        )

    return profile
