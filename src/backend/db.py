from pydantic import BaseModel, ConfigDict
from uuid import UUID


class HVACSubmissionResponse(BaseModel):
    id: UUID
    address: str
    appliance_number: int
    nameplate_photo: str

    model_config = ConfigDict(from_attributes=True)
    # converts SQLAlchemy objects into JSON responses


class WaterHeaterSubmissionResponse(BaseModel):
    id: UUID
    address: str
    appliance_number: int
    nameplate_photo: str

    model_config = ConfigDict(from_attributes=True)


class HVACAnalysisResponse(BaseModel):
    id: UUID
    submission_id: UUID
    brand: str | None = None
    model_number: str | None = None   # value can be text or empty
    serial_number: str | None = None
    age: int | None = None
    replacement_recommendation: str | None = None
    subtype: str | None = None
    model_config = ConfigDict(from_attributes=True)


class WaterHeaterAnalysisResponse(BaseModel):
    id: UUID
    submission_id: UUID
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    age: int | None = None
    replacement_recommendation: str | None = None
    subtype: str | None = None
    model_config = ConfigDict(from_attributes=True)
