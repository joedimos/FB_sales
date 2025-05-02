from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, JSON, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum
import datetime

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
    STALE = "stale" # Lead inactive

class CRMData(Base):
    """Stores raw and standardized data from CRM ingestion."""
    __tablename__ = 'crm_data'
    id = Column(Integer, primary_key=True, index=True)
    crm_lead_id = Column(String, nullable=False, index=True) # ID from the specific CRM
    crm_source = Column(String, nullable=False) # e.g., 'VinSolutions', 'CDK'
    raw_data = Column(JSON) # Store raw JSON from CRM ingestion
    standardized_data = Column(JSON) # Store standardized data after initial mapping
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationship back to the Lead if one exists
    lead = relationship("Lead", back_populates="crm_data", uselist=False)

    __table_args__ = (
        # Ensure combination of crm_lead_id and crm_source is unique
        # A single lead might update over time, but id+source identifies the lead in its CRM
        # This might need refinement if a lead ID can be reused *within* a CRM over long periods
        # For simplicity, assuming crm_lead_id is globally unique within a CRM
        # You might want to store multiple CRMData entries per Lead for history
        # For now, let's link one CRMData entry to one Lead entry based on CRM lead ID
        # A better approach might be to match Lead entries based on customer/vehicle data
        # Sticking to simpler 1:1 for this demo, assuming CRMData is the source record
        # based on crm_lead_id
        {}, # Table arguments tuple needs at least one element if not empty
    )


class Vehicle(Base):
    """Stores information about vehicles."""
    __tablename__ = 'vehicles'
    id = Column(Integer, primary_key=True, index=True)
    vin = Column(String, unique=True, nullable=True) # VIN might not always be available initially
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    price = Column(Float)
    mileage = Column(Integer)
    days_on_lot = Column(Integer) # Calculated field or fetched
    # Add other vehicle specific fields (e.g., condition, trim)

    # Relationship to Leads interested in this vehicle
    leads = relationship("Lead", back_populates="vehicle")

class Lead(Base):
    """Represents a lead and its lifecycle within the dealership."""
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True, index=True)

    # Link to the source CRM data record
    # A lead record is derived from CRMData, potentially consolidating info
    # For simplicity, let's link directly, assuming CRMData represents the *current* state
    crm_data_fk = Column(Integer, ForeignKey('crm_data.id'), unique=True, nullable=False)
    crm_data = relationship("CRMData", back_populates="lead") # 1:1 relationship

    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    vehicle = relationship("Vehicle", back_populates="leads") # Many:1 relationship

    # customer_id = Column(Integer, ForeignKey('customers.id')) # Assuming customer table - omitted for demo

    # Status derived from CRM Data updates
    current_status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    initial_message = Column(String, nullable=True) # Initial message from FBMP lead

    created_at = Column(DateTime, default=datetime.datetime.utcnow) # When lead was created (first seen)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow) # When lead record was last updated
    closed_at = Column(DateTime) # When status became WON or LOST

    # Target variable for prediction
    is_converted = Column(Integer) # 1 for WON, 0 for LOST/STALE (needs calculation based on status changes)

    # Prediction result
    predicted_likelihood = Column(Float, nullable=True)

    # Add fields for interactions (calls, emails, etc.) - could be a separate table linked here
    # interactions = relationship("Interaction", back_populates="lead") # Example

# class Interaction(Base):
#     __tablename__ = 'interactions'
#     id = Column(Integer, primary_key=True, index=True)
#     lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False)
#     lead = relationship("Lead", back_populates="interactions")
#     type = Column(String) # e.g., 'call', 'email', 'sms'
#     timestamp = Column(DateTime, default=datetime.datetime.utcnow)
#     notes = Column(String)
#     # Add fields for duration, outcome, etc.
