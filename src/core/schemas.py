from pydantic import BaseModel, ConfigDict


class HVACSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    address: str
    appliance_number: int
    nameplate_photo: str

    # converts SQLAlchemy objects into JSON responses


class WaterHeaterSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    address: str
    appliance_number: int
    nameplate_photo: str


class HVACAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    submission_id: str
    brand: str | None = None
    model_number: str | None = None   # value can be text or empty
    serial_number: str | None = None
    age: int | None = None
    replacement_recommendation: str | None = None
    subtype: str | None = None
    review_reason: str | None = None


class WaterHeaterAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: str
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    age: int | None = None
    replacement_recommendation: str | None = None
    subtype: str | None = None
    review_reason: str | None = None

