import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)
SUPABASE_STORAGE_BUCKET = os.getenv(
    "SUPABASE_STORAGE_BUCKET",
    "appliance-nameplates",
)

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL environment variable is missing."
    )

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "SUPABASE_SERVICE_ROLE_KEY environment variable is missing."
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


async def upload_nameplate(
    file: UploadFile,
    appliance_type: str,
    submission_id: str,
) -> str:
    """
    Upload a nameplate image to Supabase Storage.

    Returns the permanent Storage object path.
    """
    image_bytes = await file.read()

    if not image_bytes:
        raise ValueError("The uploaded image is empty.")

    content_type = file.content_type or "image/jpeg"

    if not content_type.startswith("image/"):
        raise ValueError("The uploaded file must be an image.")

    extension = Path(file.filename or "").suffix.lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".heic",
    }

    if extension not in allowed_extensions:
        extension = ".jpg"

    object_path = (
        f"{appliance_type}/"
        f"{submission_id}/"
        f"{uuid4()}{extension}"
    )

    supabase.storage.from_(
        SUPABASE_STORAGE_BUCKET
    ).upload(
        path=object_path,
        file=image_bytes,
        file_options={
            "content-type": content_type,
            "upsert": "false",
        },
    )

    return object_path


def download_nameplate(
    object_path: str,
) -> bytes:
    """
    Download a private image from Supabase Storage.
    """
    image_bytes = (
        supabase.storage
        .from_(SUPABASE_STORAGE_BUCKET)
        .download(object_path)
    )

    return bytes(image_bytes)


def create_nameplate_signed_url(
    object_path: str,
    expires_in: int = 3600,
) -> str:
    """
    Create a temporary URL for a private image.
    """
    response = (
        supabase.storage
        .from_(SUPABASE_STORAGE_BUCKET)
        .create_signed_url(
            path=object_path,
            expires_in=expires_in,
        )
    )

    signed_url = response.get("signedURL")

    if not isinstance(signed_url, str):
        signed_url = response.get("signedUrl")

    if not isinstance(signed_url, str):
        raise RuntimeError(
            "Supabase did not return a signed URL."
        )

    return signed_url


def delete_nameplate(
    object_path: str,
) -> None:
    """
    Delete an image from Supabase Storage.
    """
    supabase.storage.from_(
        SUPABASE_STORAGE_BUCKET
    ).remove([object_path])
```
