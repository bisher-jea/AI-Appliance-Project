from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped    # orm tool
from sqlalchemy import ForeignKey
from uuid import uuid4, UUID


# parent base class, used to track all models
class Base(DeclarativeBase):
    pass


# tables store photo file path, not actual photo
class HVACSubmission(Base):
    __tablename__: any = "hvac_submissions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    address: Mapped[str] = mapped_column(nullable=False)
    appliance_number: Mapped[int] = mapped_column(nullable=False)
    nameplate_photo: Mapped[str] = mapped_column(nullable=False)


class WaterHeaterSubmission(Base):
    __tablename__: any = "water_heater_submissions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    address: Mapped[str] = mapped_column(nullable=False)
    appliance_number: Mapped[int] = mapped_column(nullable=False)
    nameplate_photo: Mapped[str] = mapped_column(nullable=False)


# None is used for AI fields because this data is unknown at submission time.
class HVACAnalysis(Base):
    __tablename__ = "hvac_analysis"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("hvac_submissions.id"),
        nullable=False,
    )

    brand: Mapped[str | None] = mapped_column(nullable=True)
    model_number: Mapped[str | None] = mapped_column(nullable=True)
    serial_number: Mapped[str | None] = mapped_column(nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    replacement_recommendation: Mapped[str | None] = mapped_column(
        nullable=True)
    subtype: Mapped[str | None]= mapped_column(nullable=True)
    

class WaterHeaterAnalysis(Base):
    __tablename__ = "water_heater_analysis"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("water_heater_submissions.id"),
        nullable=False,
    )

    brand: Mapped[str | None] = mapped_column(nullable=True)
    model_number: Mapped[str | None] = mapped_column(nullable=True)
    serial_number: Mapped[str | None] = mapped_column(nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    replacement_recommendation: Mapped[str | None] = mapped_column(
        nullable=True)
    subtype: Mapped[str | None]= mapped_column(nullable=True)
    
