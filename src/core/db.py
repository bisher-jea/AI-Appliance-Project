from pydantic import BaseModel


class HVACSubmissionResponse(BaseModel):
    id: str
    address: str
    appliance_number: int
    nameplate_photo: str

    class Config:
        orm_mode: bool = True
    # converts SQLAlchemy objects into JSON responses


class WaterHeaterSubmissionResponse(BaseModel):
    id: str
    address: str
    appliance_number: int
    nameplate_photo: str

    class Config:
        orm_mode: bool = True


class HVACAnalysisResponse(BaseModel):
    submission_id: str
    brand: str | None = None
    model_number: str | None = None   # value can be text or empty
    serial_number: str | None = None
    age: int | None = None
    replacement_recommendation: str | None = None
    subtype: str | None = None
    review_reason: str | None = None
    
    class Config:
        orm_mode: bool = True


class WaterHeaterAnalysisResponse(BaseModel):
    submission_id: str
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    age: int | None = None
    replacement_recommendation: str | None = None
    subtype: str | None = None
    review_reason: str | None = None
    
    class Config:
        orm_mode: bool = True
