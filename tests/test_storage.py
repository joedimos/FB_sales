import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.storage.models import Base, CRMData, Lead, LeadStatus, Vehicle

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_crm_data(db):
    crm_data = CRMData(crm_lead_id="test_lead_1", crm_source="TestCRM", raw_data={"key": "value"}, standardized_data={"status": "New"})
    db.add(crm_data)
    db.commit()
    db.refresh(crm_data)
    assert crm_data.id is not None
    assert crm_data.raw_data == {"key": "value"}


def test_create_vehicle(db):
    vehicle = Vehicle(vin="TESTVIN123", make="TestMake", model="TestModel", year=2022, price=35000.0, mileage=10000, days_on_lot=30)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    assert vehicle.id is not None
    assert vehicle.vin == "TESTVIN123"


def test_create_lead_with_relations(db):
    crm_data = CRMData(crm_lead_id="test_lead_2", crm_source="TestCRM", raw_data={}, standardized_data={"status": "New"})
    vehicle = Vehicle(vin="TESTVIN456", make="AnotherMake", model="AnotherModel", year=2021, price=20000.0, mileage=50000, days_on_lot=50)
    db.add_all([crm_data, vehicle])
    db.commit()
    lead = Lead(crm_data_fk=crm_data.id, vehicle_id=vehicle.id, current_status=LeadStatus.NEW, initial_message="Test message", created_at=datetime.datetime.utcnow())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    assert lead.crm_data.crm_lead_id == "test_lead_2"
    assert lead.vehicle.vin == "TESTVIN456"
    assert lead.current_status == LeadStatus.NEW
