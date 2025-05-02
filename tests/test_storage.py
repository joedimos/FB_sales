import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.storage.database import Base, get_db, SessionLocal as RealSessionLocal # Import needed components
from src.storage.models import Lead, Vehicle, CRMData, LeadStatus
import datetime

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create a test engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create a test sessionmaker
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency for tests
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Setup and Teardown ---
@pytest.fixture(scope="module")
def db():
    """Fixture to provide a test DB session."""
    Base.metadata.create_all(bind=engine) # Create tables
    yield TestingSessionLocal() # Provide session
    Base.metadata.drop_all(bind=engine) # Drop tables after tests


# --- Tests ---
def test_create_crm_data(db: TestingSessionLocal):
    crm_data = CRMData(
        crm_lead_id="test_lead_1",
        crm_source="TestCRM",
        raw_data={"key": "value"},
        standardized_data={"status": "New", "created_at": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)}
    )
    db.add(crm_data)
    db.commit()
    db.refresh(crm_data)

    assert crm_data.id is not None
    assert crm_data.crm_lead_id == "test_lead_1"
    assert crm_data.crm_source == "TestCRM"
    assert crm_data.raw_data == {"key": "value"}

def test_create_vehicle(db: TestingSessionLocal):
    vehicle = Vehicle(
        vin="TESTVIN123",
        make="TestMake",
        model="TestModel",
        year=2022,
        price=35000.0,
        mileage=10000.0,
        days_on_lot=30
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    assert vehicle.id is not None
    assert vehicle.vin == "TESTVIN123"

def test_create_lead_with_relations(db: TestingSessionLocal):
    # Create CRMData and Vehicle first
    crm_data = CRMData(
        crm_lead_id="test_lead_2",
        crm_source="TestCRM",
        raw_data={},
        standardized_data={"status": "New", "created_at": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)}
    )
    vehicle = Vehicle(
        vin="TESTVIN456",
        make="AnotherMake",
        model="AnotherModel",
        year=2021, price=20000.0, mileage=50000.0, days_on_lot=50
    )
    db.add(crm_data)
    db.add(vehicle)
    db.commit()
    db.refresh(crm_data)
    db.refresh(vehicle)

    lead = Lead(
        crm_data_fk=crm_data.id,
        vehicle_id=vehicle.id,
        current_status=LeadStatus.NEW,
        initial_message="Test message"
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    assert lead.id is not None
    assert lead.crm_data is not None
    assert lead.vehicle is not None
    assert lead.crm_data.crm_lead_id == "test_lead_2"
    assert lead.vehicle.vin == "TESTVIN456"
    assert lead.current_status == LeadStatus.NEW
