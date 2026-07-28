"""
This module manages all appliance nameplate image storage for ApplianceIQ.

Rather than allowing the rest of the application to interact directly with
the filesystem, every upload, download, lookup, and deletion of nameplate
images passes through this service.

The storage location is configured using the UPLOAD_DIRECTORY environment
variable, allowing the application to switch storage providers without
changing the rest of the codebase.

Database records do not store absolute file paths. Instead, they store
relative object paths such as:

    hvac/
        <submission-id>/
            <generated-file>.jpg

or

    water_heater/
        <submission-id>/
            <generated-file>.png

When an image is needed, this module combines the relative object path with
UPLOAD_DIRECTORY to locate the file.

This module is responsible for:

• Validating uploaded image files
• Generating unique filenames
• Organizing uploads by appliance type and submission
• Reading images from storage
• Returning filesystem paths when needed
• Deleting uploaded images
• Preventing directory traversal attacks

This module intentionally contains no OCR logic or database operations.
It only manages file storage.

The rest of ApplianceIQ should continue calling these same functions without
needing to know where files are physically stored.
"""
import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


UPLOAD_DIRECTORY = Path(
    os.getenv(
        "UPLOAD_DIRECTORY",
        r"G:/Customer Relationship/Customer Analytics/Ella/uploads",
    )
).resolve()

UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


def _safe_appliance_type(
    appliance_type: str,
) -> str:
    return (
        appliance_type.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


async def upload_nameplate(
    file: UploadFile,
    appliance_type: str,
    submission_id: str,
) -> str:
    """
    Save a nameplate image inside the locally mounted
    Google Drive folder.

    Returns the relative storage key saved in the database.
    """
    image_bytes = await file.read()

    if not image_bytes:
        raise ValueError(
            "The uploaded image is empty."
        )

    content_type = (
        file.content_type
        or "image/jpeg"
    )

    if not content_type.startswith("image/"):
        raise ValueError(
            "The uploaded file must be an image."
        )

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".heic",
    }

    if extension not in allowed_extensions:
        extension = ".jpg"

    appliance_folder = _safe_appliance_type(
        appliance_type
    )

    relative_path = Path(
        appliance_folder,
        submission_id,
        f"{uuid4()}{extension}",
    )

    destination = (
        UPLOAD_DIRECTORY
        / relative_path
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_bytes(
        image_bytes
    )

    return relative_path.as_posix()


def download_nameplate(
    object_path: str,
) -> bytes:
    """
    Read a nameplate image from the locally mounted
    Google Drive folder.
    """
    full_path = (
        UPLOAD_DIRECTORY
        / Path(object_path)
    ).resolve()

    try:
        full_path.relative_to(
            UPLOAD_DIRECTORY
        )
    except ValueError as error:
        raise ValueError(
            "Invalid nameplate object path."
        ) from error

    if not full_path.is_file():
        raise FileNotFoundError(
            f"Nameplate image was not found: "
            f"{object_path}"
        )

    return full_path.read_bytes()


def get_nameplate_path(
    object_path: str,
) -> Path:
    """
    Return the complete local filesystem path.
    Useful for OCR tools that require a file path.
    """
    full_path = (
        UPLOAD_DIRECTORY
        / Path(object_path)
    ).resolve()

    try:
        full_path.relative_to(
            UPLOAD_DIRECTORY
        )
    except ValueError as error:
        raise ValueError(
            "Invalid nameplate object path."
        ) from error

    return full_path


def create_nameplate_signed_url(
    object_path: str,
    expires_in: int = 3600,
) -> str:
    """
    Local Google Drive storage does not use signed URLs.

    Returns the application's local uploads URL.
    """
    del expires_in

    normalized_path = Path(
        object_path
    ).as_posix()

    return f"/uploads/{normalized_path}"


def delete_nameplate(
    object_path: str,
) -> None:
    """
    Delete an image from the locally mounted
    Google Drive folder.
    """
    full_path = get_nameplate_path(
        object_path
    )

    if full_path.exists():
        full_path.unlink()