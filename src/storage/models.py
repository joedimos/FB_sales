from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, JSON, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

Base = declarative_base()

class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    APPOINTMENT = "appointment"
    SHOWED = "showed"
    TEST_DRIVE = "test_drive"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

class CRMData(Base):
    __tablename__ = 'crm_data'
    id = Column(Integer, primary_key=True)
    crm_lead_id = Column(String, unique=True, nullable=False) # ID from the specific CRM
    crm_source = Column(String, nullable=False) # e.g., 'VinSolutions', 'CDK'
    raw_data = Column(JSON) # Store raw JSON from CRM ingestion
    standardized_data = Column(JSON) # Store standardized data after initial mapping
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    # Foreign keys to other tables if normalized

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    crm_data_id = Column(Integer, ForeignKey('crm_data.id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id')) # Assuming customer table
    current_status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    created_at = Column(DateTime)
    closed_at = Column(DateTime) # When status became WON or LOST
    is_converted = Column(Integer) # 1 for WON, 0 for LOST/STALE
    # Add other lead specific fields
    predicted_likelihood = Column(Float) # Store the model's prediction

    crm_data = relationship("CRMData")
    vehicle = relationship("Vehicle")
    # customer = relationship("Customer")

class Vehicle(Base):
    __tablename__ = 'vehicles'
    id = Column(Integer, primary_key=True)
    vin = Column(String, unique=True)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    price = Column(Float)
    mileage = Column(Integer)
    days_on_lot = Column(Integer)
    # Add other vehicle specific fields

# Example engine and session setup
DATABASE_URL = "postgresql://user:password@host:port/dbname" # Get from config
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine) # Creates tables if they don't exist
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
