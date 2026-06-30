
# testing capabilities of 
# applicable files: schema.py, appliance.py, db.py

from sqlalchemy import inspect

from src.core.schema import (
    HVACAnalysis,
    HVACSubmission,
    WaterHeaterAnalysis,
    WaterHeaterSubmission,
)

from src.core.db import (
    HVACAnalysisResponse,
    HVACSubmissionResponse,
    WaterHeaterAnalysisResponse,
    WaterHeaterSubmissionResponse,
)

# -------------SCHEMA.PY--------------------------------------------------------


# checking all fields exist
def test_expected_tables_exist(db_session):
    engine = db_session.get_bind()
    inspector = inspect(engine)

    table_names = inspector.get_table_names()

    assert "hvac_submissions" in table_names
    assert "water_heater_submissions" in table_names
    assert "hvac_analysis" in table_names
    assert "water_heater_analysis" in table_names


def test_hvac_submission_columns_exist():
    columns = HVACSubmission.__table__.columns.keys()

    assert "id" in columns
    assert "address" in columns
    assert "system_number" in columns
    assert "outdoor_nameplate_photo" in columns
    assert "indoor_nameplate_photo" in columns


def test_water_heater_submission_columns_exist():
    columns = WaterHeaterSubmission.__table__.columns.keys()

    assert "id" in columns
    assert "address" in columns
    assert "system_number" in columns
    assert "nameplate_photo" in columns


def test_hvac_analysis_columns_exist():
    columns = HVACAnalysis.__table__.columns.keys()

    assert "id" in columns
    assert "submission_id" in columns
    assert "model_number" in columns
    assert "serial_number" in columns
    assert "age" in columns
    assert "replacement_recommendation" in columns


def test_water_heater_analysis_columns_exist():
    columns = WaterHeaterAnalysis.__table__.columns.keys()

    assert "id" in columns
    assert "submission_id" in columns
    assert "model_number" in columns
    assert "serial_number" in columns
    assert "age" in columns
    assert "replacement_recommendation" in columns


# allows null data for ai stuff, not the other one
def test_analysis_fields_are_nullable():
    assert HVACAnalysis.__table__.columns["model_number"].nullable is True
    assert HVACAnalysis.__table__.columns["serial_number"].nullable is True
    assert HVACAnalysis.__table__.columns["age"].nullable is True

    assert (
        HVACAnalysis.__table__
        .columns["replacement_recommendation"]
        .nullable
        is True
    )

    assert WaterHeaterAnalysis.__table__.columns["model_number"].nullable is True
    assert WaterHeaterAnalysis.__table__.columns["serial_number"].nullable is True
    assert WaterHeaterAnalysis.__table__.columns["age"].nullable is True

    assert (
        WaterHeaterAnalysis.__table__
        .columns["replacement_recommendation"]
        .nullable
        is True
    )


def test_submission_fields_are_not_nullable():
    assert HVACSubmission.__table__.columns["address"].nullable is False
    assert HVACSubmission.__table__.columns["system_number"].nullable is False
    assert (
        HVACSubmission.__table__
        .columns["outdoor_nameplate_photo"]
        .nullable
        is False
    )
    assert (
        HVACSubmission.__table__
        .columns["indoor_nameplate_photo"]
        .nullable
        is False
    )

    assert WaterHeaterSubmission.__table__.columns["address"].nullable is False
    assert (
        WaterHeaterSubmission.__table__.columns["system_number"].nullable
        is False
    )
    assert (
        WaterHeaterSubmission.__table__.columns["nameplate_photo"].nullable
        is False
    )


# testing that foreign keys exist
def test_foreign_keys_exist():
    hvac_foreign_keys = list(HVACAnalysis.__table__.foreign_keys)
    water_foreign_keys = list(WaterHeaterAnalysis.__table__.foreign_keys)

    assert len(hvac_foreign_keys) == 1
    assert len(water_foreign_keys) == 1

    assert (
        hvac_foreign_keys[0].target_fullname
        == "hvac_submissions.id"
    )

    assert (
        water_foreign_keys[0].target_fullname
        == "water_heater_submissions.id"
    )
# -------------APPLIANCE.PY-----------------------------------------------------


# routes work even if empty and just return []
def test_hvac_route_returns_empty_list(client):
    response = client.get("/appliances/hvac")

    assert response.status_code == 200
    assert response.json() == []


def test_water_heaters_route_returns_empty_list(client):
    response = client.get("/appliances/water-heaters")

    assert response.status_code == 200
    assert response.json() == []


def test_hvac_analysis_route_returns_empty_list(client):
    response = client.get("/appliances/hvac-analysis")

    assert response.status_code == 200
    assert response.json() == []


def test_water_heater_analysis_route_returns_empty_list(client):
    response = client.get("/appliances/water-heater-analysis")

    assert response.status_code == 200
    assert response.json() == []


# testing that routes actual return records
def test_hvac_route_returns_database_records(client, db_session):
    submission = HVACSubmission(
        address="123 Main St",
        system_number=1,
        outdoor_nameplate_photo="uploads/outdoor.jpg",
        indoor_nameplate_photo="uploads/indoor.jpg",
    )

    db_session.add(submission)
    db_session.commit()

    response = client.get("/appliances/hvac")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["address"] == "123 Main St"
    assert data[0]["system_number"] == 1
    assert data[0]["outdoor_nameplate_photo"] == "uploads/outdoor.jpg"
    assert data[0]["indoor_nameplate_photo"] == "uploads/indoor.jpg"


def test_water_heater_route_returns_database_records(client, db_session):
    submission = WaterHeaterSubmission(
        address="456 Oak Ave",
        system_number=1,
        nameplate_photo="uploads/water.jpg",
    )

    db_session.add(submission)
    db_session.commit()

    response = client.get("/appliances/water-heaters")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["address"] == "456 Oak Ave"
    assert data[0]["system_number"] == 1
    assert data[0]["nameplate_photo"] == "uploads/water.jpg"


def test_hvac_analysis_route_returns_database_records(client, db_session):
    submission = HVACSubmission(
        address="789 Pine Rd",
        system_number=1,
        outdoor_nameplate_photo="uploads/outdoor.jpg",
        indoor_nameplate_photo="uploads/indoor.jpg",
    )

    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    analysis = HVACAnalysis(
        submission_id=submission.id,
        model_number=None,
        serial_number=None,
        age=None,
        replacement_recommendation=None,
    )

    db_session.add(analysis)
    db_session.commit()

    response = client.get("/appliances/hvac-analysis")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["submission_id"] == str(submission.id)
    assert data[0]["model_number"] is None
    assert data[0]["serial_number"] is None
    assert data[0]["age"] is None
    assert data[0]["replacement_recommendation"] is None


def test_water_heater_analysis_route_returns_database_records(
    client,
    db_session,
):
    submission = WaterHeaterSubmission(
        address="111 River St",
        system_number=1,
        nameplate_photo="uploads/water.jpg",
    )

    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    analysis = WaterHeaterAnalysis(
        submission_id=submission.id,
        model_number=None,
        serial_number=None,
        age=None,
        replacement_recommendation=None,
    )

    db_session.add(analysis)
    db_session.commit()

    response = client.get("/appliances/water-heater-analysis")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["submission_id"] == str(submission.id)
    assert data[0]["model_number"] is None
    assert data[0]["serial_number"] is None
    assert data[0]["age"] is None
    assert data[0]["replacement_recommendation"] is None


# pydantic response models validate correctly


# testing the id numbers


# making sure it will eventually accept the ai analysis
