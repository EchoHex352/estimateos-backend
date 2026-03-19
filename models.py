"""
Database Models for EstimateOS Pro
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_name = Column(String(255))
    role = Column(String(50), default='estimator')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="creator")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    client_name = Column(String(255))
    project_number = Column(String(100))
    status = Column(String(50), default='processing')
    user_id = Column(UUID(as_uuid=False), ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    files = relationship("UploadedFile", back_populates="project", cascade="all, delete-orphan")
    selected_divisions = relationship("SelectedDivision", back_populates="project", cascade="all, delete-orphan")
    quantities = relationship("QuantityTakeoff", back_populates="project", cascade="all, delete-orphan")
    rfqs = relationship("RFQ", back_populates="project", cascade="all, delete-orphan")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey('projects.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_url = Column(Text, nullable=False)
    page_count = Column(Integer)
    file_size_mb = Column(Float)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="files")
    pages = relationship("PDFPage", back_populates="file", cascade="all, delete-orphan")


class SelectedDivision(Base):
    __tablename__ = "selected_divisions"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey('projects.id', ondelete='CASCADE'))
    division_id = Column(String(10), nullable=False)
    division_name = Column(String(255))
    division_color = Column(String(20))
    is_selected = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="selected_divisions")


class PDFPage(Base):
    __tablename__ = "pdf_pages"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    file_id = Column(UUID(as_uuid=False), ForeignKey('uploaded_files.id', ondelete='CASCADE'))
    page_number = Column(Integer, nullable=False)
    image_url = Column(Text)
    raw_text = Column(Text)
    sheet_type = Column(String(50))
    sheet_number = Column(String(100))
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    
    # Relationships
    file = relationship("UploadedFile", back_populates="pages")
    annotations = relationship("Annotation", back_populates="page", cascade="all, delete-orphan")
    legend_items = relationship("MaterialLegend", back_populates="page", cascade="all, delete-orphan")


class Annotation(Base):
    __tablename__ = "annotations"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    page_id = Column(UUID(as_uuid=False), ForeignKey('pdf_pages.id', ondelete='CASCADE'))
    annotation_type = Column(String(50))
    coordinates = Column(JSON, nullable=False)
    division_id = Column(String(10))
    material_type = Column(String(255))
    material_description = Column(Text)
    quantity = Column(Float)
    unit = Column(String(20))
    color = Column(String(20))
    confidence_score = Column(Float)
    detected_by = Column(String(50), default='ai')
    created_by = Column(UUID(as_uuid=False), ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    page = relationship("PDFPage", back_populates="annotations")
    creator = relationship("User", back_populates="annotations")


class MaterialLegend(Base):
    __tablename__ = "material_legend"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    page_id = Column(UUID(as_uuid=False), ForeignKey('pdf_pages.id', ondelete='CASCADE'))
    division_id = Column(String(10))
    material_type = Column(String(255))
    color = Column(String(20))
    count = Column(Integer, default=1)
    total_quantity = Column(Float)
    unit = Column(String(20))
    
    # Relationships
    page = relationship("PDFPage", back_populates="legend_items")


class QuantityTakeoff(Base):
    __tablename__ = "quantity_takeoff"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey('projects.id', ondelete='CASCADE'))
    division_id = Column(String(10))
    csi_code = Column(String(50))
    material_name = Column(String(255))
    material_description = Column(Text)
    quantity = Column(Float)
    unit = Column(String(20))
    unit_cost = Column(Float)
    material_cost = Column(Float)
    labor_hours = Column(Float)
    labor_rate = Column(Float)
    labor_cost = Column(Float)
    total_cost = Column(Float)
    waste_factor = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="quantities")


class LaborUnit(Base):
    __tablename__ = "labor_units"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    csi_code = Column(String(50), index=True)
    material_type = Column(String(255), index=True)
    description = Column(Text)
    unit = Column(String(20))
    labor_hours_per_unit = Column(Float)
    crew_size = Column(Integer)
    daily_output = Column(Float)
    source = Column(String(100))
    last_updated = Column(DateTime, default=datetime.utcnow)


class MaterialPricing(Base):
    __tablename__ = "material_pricing"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    material_name = Column(String(255), index=True)
    vendor_name = Column(String(255))
    vendor_sku = Column(String(100))
    unit = Column(String(20))
    unit_price = Column(Float)
    location = Column(String(100))
    effective_date = Column(DateTime)
    expiration_date = Column(DateTime)
    minimum_quantity = Column(Integer)
    lead_time_days = Column(Integer)
    vendor_contact = Column(JSON)


class RFQ(Base):
    __tablename__ = "rfqs"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey('projects.id', ondelete='CASCADE'))
    rfq_number = Column(String(100), unique=True)
    vendor_name = Column(String(255))
    vendor_email = Column(String(255))
    items = Column(JSON)
    status = Column(String(50), default='sent')
    sent_at = Column(DateTime)
    due_date = Column(DateTime)
    response_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="rfqs")
