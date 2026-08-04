"""
Each appliance has 2 tables: submission and analysis.
The submission table contains just information gathered during the form submission
The analysis table is the container of all the OCR extracted data. 
"""
from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, DateTime, String
from uuid import uuid4
from typing import ClassVar
from datetime import datetime, timezone


# parent base class, used to track all models
class Base(DeclarativeBase):
    pass


# tables store photo file path, not actual photo
class HVACSubmission(Base):
    __tablename__: ClassVar[str] = "hvac_submissions" # pyright: ignore[reportIncompatibleVariableOverride]

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    address: Mapped[str] = mapped_column(nullable=False)
    appliance_number: Mapped[int] = mapped_column(nullable=False)
    nameplate_photo: Mapped[str] = mapped_column(nullable=False)
    batch_id: Mapped[str | None] = mapped_column(
        nullable=False,
        index=True,
    )

    analysis: Mapped[HVACAnalysis | None] = relationship(
        back_populates="submission",
        uselist=False
    )


class WaterHeaterSubmission(Base):
    __tablename__: ClassVar[str] = "water_heater_submissions" # pyright: ignore[reportIncompatibleVariableOverride]

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    address: Mapped[str] = mapped_column(nullable=False)
    appliance_number: Mapped[int] = mapped_column(nullable=False)
    nameplate_photo: Mapped[str] = mapped_column(nullable=False)
    batch_id: Mapped[str | None] = mapped_column(
        nullable=False,
        index=True,
    )

    analysis: Mapped[WaterHeaterAnalysis | None] = relationship(
        back_populates="submission",
        uselist=False
    )


# None is used for AI fields because this data is unknown at submission time.
class HVACAnalysis(Base):
    __tablename__: ClassVar[str] = "hvac_analysis"   # pyright: ignore[reportIncompatibleVariableOverride]

    submission_id: Mapped[str] = mapped_column(
        ForeignKey("hvac_submissions.id"),
        primary_key=True,
        nullable=False,
        unique=True
    )

    submission: Mapped[HVACSubmission] = relationship(
        back_populates="analysis"
    )

    brand: Mapped[str | None] = mapped_column(nullable=True)
    model_number: Mapped[str | None] = mapped_column(nullable=True)
    serial_number: Mapped[str | None] = mapped_column(nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    replacement_recommendation: Mapped[str | None] = mapped_column(
        nullable=True)
    subtype: Mapped[str | None] = mapped_column(nullable=True)
    needs_human_review: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    review_reason: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    analysis_complete: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )


class WaterHeaterAnalysis(Base):
    __tablename__: ClassVar[str] = "water_heater_analysis" # pyright: ignore[reportIncompatibleVariableOverride]

    submission_id: Mapped[str] = mapped_column(
        ForeignKey("water_heater_submissions.id"),
        primary_key=True,
        nullable=False,
        unique=True
    )

    submission: Mapped[WaterHeaterSubmission] = relationship(
        back_populates="analysis"
    )

    brand: Mapped[str | None] = mapped_column(nullable=True)
    model_number: Mapped[str | None] = mapped_column(nullable=True)
    serial_number: Mapped[str | None] = mapped_column(nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    replacement_recommendation: Mapped[str | None] = mapped_column(
        nullable=True)
    subtype: Mapped[str | None] = mapped_column(nullable=True)
    needs_human_review: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    review_reason: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    analysis_complete: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )


class DashboardAccessLog(Base):
    __tablename__: ClassVar[str] = "dashboard_access_logs"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    email: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class DashboardActivityLog(Base):
    __tablename__ = "dashboard_activity_logs"

    id = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    email = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    action = mapped_column(
        String,
        nullable=False,
    )

    submission_id = mapped_column(
        String,
        nullable=True,
    )

    timestamp = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )