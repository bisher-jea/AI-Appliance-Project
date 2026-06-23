"""
# testing capabilities of form's submission to correctly share information to API
# applicable files: main.py, operations.py

from fastapi.testclient import TestClient
from io import BytesIO
from sqlalchemy import inspect
from main import app
from backend.schema import Base, HVACSubmission, WaterHeaterSubmission
from backend.operations import get_db, init_tables


#-------------MAIN.PY------------------------------------------------------------------------------------

# home route works
def test_home_route(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "FastAPI appliance database is running"

# POST /submit with HVAC makes 1 HVAC row
def test_submit_hvac_creates_hvac_submission(client, db_session):
    files = {
        "outdoorNameplate1": (
            "outdoor.jpg",
            BytesIO(b"fake outdoor image"),
            "image/jpeg",
        ),
        "indoorNameplate1": (
            "indoor.jpg",
            BytesIO(b"fake indoor image"),
            "image/jpeg",
        ),
    }

    data = {
        "address": "123 Main St",
        "applianceType": "HVAC",
        "systemCount": "1",
    }

    response = client.post(
        "/submit",
        data=data,
        files=files,
    )

    assert response.status_code == 200
    assert response.json()["appliance_type"] == "HVAC"
    assert response.json()["systems_saved"] == 1

    submissions = db_session.query(HVACSubmission).all()

    assert len(submissions) == 1
    assert submissions[0].address == "123 Main St"
    assert submissions[0].system_number == 1

# POST /submit with WH makes 1 HVAC row
def test_submit_water_heater_creates_water_heater_submission(
    client,
    db_session,
):
    files = {
        "waterHeaterNameplate1": (
            "water-heater.jpg",
            BytesIO(b"fake water heater image"),
            "image/jpeg",
        ),
    }

    data = {
        "address": "456 Oak Ave",
        "applianceType": "Water Heater",
        "systemCount": "1",
    }

    response = client.post(
        "/submit",
        data=data,
        files=files,
    )

    assert response.status_code == 200
    assert response.json()["appliance_type"] == "Water Heater"
    assert response.json()["systems_saved"] == 1

    submissions = db_session.query(WaterHeaterSubmission).all()

    assert len(submissions) == 1
    assert submissions[0].address == "456 Oak Ave"
    assert submissions[0].system_number == 1

# POST /submit with 2 systems makes 2 separate rows
def test_submit_hvac_two_systems_creates_two_rows(client, db_session):
    files = {
        "outdoorNameplate1": (
            "outdoor1.jpg",
            BytesIO(b"fake outdoor image 1"),
            "image/jpeg",
        ),
        "indoorNameplate1": (
            "indoor1.jpg",
            BytesIO(b"fake indoor image 1"),
            "image/jpeg",
        ),
        "outdoorNameplate2": (
            "outdoor2.jpg",
            BytesIO(b"fake outdoor image 2"),
            "image/jpeg",
        ),
        "indoorNameplate2": (
            "indoor2.jpg",
            BytesIO(b"fake indoor image 2"),
            "image/jpeg",
        ),
    }

    data = {
        "address": "789 Pine Rd",
        "applianceType": "HVAC",
        "systemCount": "2",
    }

    response = client.post(
        "/submit",
        data=data,
        files=files,
    )

    assert response.status_code == 200
    assert response.json()["systems_saved"] == 2

    submissions = db_session.query(HVACSubmission).all()

    assert len(submissions) == 2


#-------------OPERATIONS.PY------------------------------------------------------------------------------------

# init_tables runs without crash and makes expected tables
def test_init_tables_creates_expected_tables(db_session):
    engine = db_session.get_bind()

    Base.metadata.drop_all(bind=engine)
    init_tables(engine)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "hvac_submissions" in table_names
    assert "water_heater_submissions" in table_names
    assert "hvac_analysis" in table_names
    assert "water_heater_analysis" in table_names

# makes db session
def test_get_db_returns_database_session():
    db_generator = get_db()
    db = next(db_generator)

    assert db is not None
    assert hasattr(db, "query")

    try:
        next(db_generator)
    except StopIteration:
        pass
        
"""