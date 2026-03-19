"""
Pydantic Schemas for Request/Response Validation
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    role: str
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[Dict[str, Any]] = None


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    project_number: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    client_name: Optional[str]
    project_number: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# FILE SCHEMAS
# ============================================================================

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    status: str
    message: str


class FileResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    page_count: Optional[int]
    file_size_mb: Optional[float]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# PAGE SCHEMAS
# ============================================================================

class PageResponse(BaseModel):
    id: str
    page_number: int
    sheet_type: Optional[str]
    sheet_number: Optional[str]
    processed: bool
    
    class Config:
        from_attributes = True


# ============================================================================
# ANNOTATION SCHEMAS
# ============================================================================

class AnnotationCreate(BaseModel):
    page_id: str
    annotation_type: str
    coordinates: Dict[str, Any]
    division_id: str
    material_type: str
    material_description: Optional[str] = None
    quantity: float
    unit: str


class AnnotationResponse(BaseModel):
    id: str
    page_id: str
    annotation_type: str
    coordinates: Dict[str, Any]
    division_id: str
    material_type: str
    material_description: Optional[str]
    quantity: float
    unit: str
    color: str
    confidence_score: Optional[float]
    detected_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# QUANTITY SCHEMAS
# ============================================================================

class QuantityResponse(BaseModel):
    id: str
    division_id: str
    material_name: str
    material_description: Optional[str]
    quantity: float
    unit: str
    material_cost: Optional[float]
    labor_hours: Optional[float]
    labor_cost: Optional[float]
    total_cost: Optional[float]
    
    class Config:
        from_attributes = True


# ============================================================================
# DIVISION SCHEMAS
# ============================================================================

class DivisionInfo(BaseModel):
    id: str
    name: str
    color: str
    group: str


class SelectedDivisionCreate(BaseModel):
    division_id: str
    division_name: str
    division_color: str


# ============================================================================
# LEGEND SCHEMAS
# ============================================================================

class LegendItem(BaseModel):
    division_id: str
    material_type: str
    color: str
    count: int
    total_quantity: float
    unit: str


# ============================================================================
# RFQ SCHEMAS
# ============================================================================

class RFQCreate(BaseModel):
    project_id: str
    vendor_name: str
    vendor_email: EmailStr
    items: List[Dict[str, Any]]
    due_date: Optional[datetime] = None


class RFQResponse(BaseModel):
    id: str
    rfq_number: str
    vendor_name: str
    vendor_email: str
    status: str
    sent_at: Optional[datetime]
    due_date: Optional[datetime]
    
    class Config:
        from_attributes = True
