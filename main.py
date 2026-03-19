"""
EstimateOS Pro - Backend API
Enterprise Construction Estimating Platform
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
from datetime import datetime, timedelta
import shutil
import json

# Import our modules
from database import engine, get_db, Base
from models import (
    Project, UploadedFile, PDFPage, Annotation, QuantityTakeoff,
    MaterialLegend, LaborUnit, MaterialPricing, RFQ, User
)
from schemas import (
    ProjectCreate, ProjectResponse, FileUploadResponse,
    AnnotationCreate, AnnotationResponse, QuantityResponse,
    UserCreate, UserLogin, Token
)
from auth import (
    create_access_token, get_current_user, get_password_hash,
    verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
)
from pdf_processor import PDFProcessor
from ai_analyzer import BlueprintAnalyzer

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="EstimateOS Pro API",
    description="Enterprise Construction Estimating Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://estimateos-pro.vercel.app",
        os.getenv("FRONTEND_URL", "*")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
pdf_processor = PDFProcessor()
ai_analyzer = BlueprintAnalyzer()

# Storage directories
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "EstimateOS Pro API"
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        company_name=user.company_name,
        role="estimator"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "full_name": db_user.full_name
        }
    }


@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")
    
    # Update last login
    db_user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "full_name": db_user.full_name
        }
    }


@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "role": current_user.role
    }


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.get("/api/v1/projects")
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects for current user"""
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects


@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    db_project = Project(
        name=project.name,
        description=project.description,
        client_name=project.client_name,
        project_number=project.project_number,
        user_id=current_user.id,
        status="created"
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@app.delete("/api/v1/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


# ============================================================================
# FILE UPLOAD & PROCESSING ENDPOINTS
# ============================================================================

@app.post("/api/v1/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload PDF file"""
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create project if not provided
    if not project_id:
        project = Project(
            name=f"Project from {file.filename}",
            user_id=current_user.id,
            status="processing"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = str(project.id)
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{project_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    # Create database record
    db_file = UploadedFile(
        project_id=project_id,
        filename=file.filename,
        file_type="blueprint",
        file_url=file_path,
        file_size_mb=file_size_mb
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Process PDF in background
    background_tasks.add_task(
        process_pdf_background,
        file_id=str(db_file.id),
        file_path=file_path,
        db=db
    )
    
    return {
        "file_id": str(db_file.id),
        "filename": file.filename,
        "status": "processing",
        "message": "File uploaded successfully. Processing in background."
    }


async def process_pdf_background(file_id: str, file_path: str, db: Session):
    """Background task to process PDF"""
    try:
        # Process PDF to images
        pages = pdf_processor.process_pdf(file_path, PROCESSED_DIR, file_id)
        
        # Update file record
        db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if db_file:
            db_file.page_count = len(pages)
            db.commit()
        
        # Create page records
        for page_info in pages:
            db_page = PDFPage(
                file_id=file_id,
                page_number=page_info['page_number'],
                image_url=page_info['image_path'],
                raw_text=page_info['text'],
                processed=False
            )
            db.add(db_page)
        
        db.commit()
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")


@app.get("/api/v1/files/{file_id}")
async def get_file_details(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get file details"""
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check project ownership
    project = db.query(Project).filter(
        Project.id == db_file.project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return db_file


@app.post("/api/v1/process/{file_id}")
async def trigger_ai_processing(
    file_id: str,
    selected_divisions: List[str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger AI analysis on all pages"""
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get all pages
    pages = db.query(PDFPage).filter(PDFPage.file_id == file_id).all()
    
    # Process each page in background
    for page in pages:
        background_tasks.add_task(
            analyze_page_background,
            page_id=str(page.id),
            selected_divisions=selected_divisions,
            db=db
        )
    
    return {
        "message": f"Processing {len(pages)} pages with AI",
        "total_pages": len(pages)
    }


async def analyze_page_background(page_id: str, selected_divisions: List[str], db: Session):
    """Background task to analyze page with AI"""
    try:
        page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
        if not page:
            return
        
        # Analyze with Claude
        results = await ai_analyzer.analyze_blueprint(
            image_path=page.image_url,
            ocr_text=page.raw_text,
            selected_divisions=selected_divisions
        )
        
        # Create annotations
        for material in results.get('materials', []):
            annotation = Annotation(
                page_id=page_id,
                annotation_type='rectangle',
                coordinates=material['bbox'],
                division_id=material['division'],
                material_type=material['material_type'],
                material_description=material['description'],
                quantity=material['quantity'],
                unit=material['unit'],
                color=get_division_color(material['division']),
                confidence_score=material.get('confidence', 0.8),
                detected_by='ai'
            )
            db.add(annotation)
        
        # Mark page as processed
        page.processed = True
        page.processed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        print(f"Error analyzing page: {str(e)}")


# ============================================================================
# PAGE ENDPOINTS
# ============================================================================

@app.get("/api/v1/files/{file_id}/pages")
async def get_file_pages(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pages for a file"""
    pages = db.query(PDFPage).filter(PDFPage.file_id == file_id).all()
    return pages


@app.get("/api/v1/pages/{page_id}")
async def get_page_details(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get page details"""
    page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return page


@app.get("/api/v1/pages/{page_id}/image")
async def get_page_image(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get page image"""
    page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
    
    if not page or not page.image_url:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if not os.path.exists(page.image_url):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    return FileResponse(page.image_url)


# ============================================================================
# ANNOTATION ENDPOINTS
# ============================================================================

@app.get("/api/v1/pages/{page_id}/annotations")
async def get_page_annotations(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all annotations for a page"""
    annotations = db.query(Annotation).filter(Annotation.page_id == page_id).all()
    return annotations


@app.post("/api/v1/annotations", response_model=AnnotationResponse)
async def create_annotation(
    annotation: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a manual annotation"""
    db_annotation = Annotation(
        **annotation.dict(),
        detected_by='manual',
        created_by=current_user.id,
        color=get_division_color(annotation.division_id)
    )
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)
    return db_annotation


@app.put("/api/v1/annotations/{annotation_id}")
async def update_annotation(
    annotation_id: str,
    annotation_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an annotation"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Update fields
    for key, value in annotation_data.items():
        if hasattr(annotation, key):
            setattr(annotation, key, value)
    
    annotation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(annotation)
    
    return annotation


@app.delete("/api/v1/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an annotation"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    db.delete(annotation)
    db.commit()
    
    return {"message": "Annotation deleted successfully"}


# ============================================================================
# QUANTITY TAKEOFF ENDPOINTS
# ============================================================================

@app.get("/api/v1/projects/{project_id}/quantities")
async def get_project_quantities(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quantity takeoff data for project"""
    quantities = db.query(QuantityTakeoff).filter(
        QuantityTakeoff.project_id == project_id
    ).all()
    
    return quantities


@app.post("/api/v1/quantities/calculate")
async def calculate_quantities(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate quantities from annotations"""
    # Get all annotations for project
    annotations = db.query(Annotation).join(PDFPage).join(UploadedFile).filter(
        UploadedFile.project_id == project_id
    ).all()
    
    # Group by material type
    material_totals = {}
    for ann in annotations:
        key = f"{ann.division_id}_{ann.material_type}"
        if key not in material_totals:
            material_totals[key] = {
                'division_id': ann.division_id,
                'material_type': ann.material_type,
                'material_description': ann.material_description,
                'quantity': 0,
                'unit': ann.unit
            }
        material_totals[key]['quantity'] += ann.quantity
    
    # Create/update quantity takeoff records
    for material in material_totals.values():
        # Look up labor units
        labor_info = get_labor_hours(
            material['division_id'],
            material['material_type'],
            material['quantity'],
            material['unit'],
            db
        )
        
        # Calculate costs (mock for now)
        unit_cost = 10.0  # Mock
        labor_rate = 75.0  # Mock
        
        material_cost = material['quantity'] * unit_cost
        labor_cost = labor_info['labor_hours'] * labor_rate if labor_info else 0
        total_cost = material_cost + labor_cost
        
        # Check if exists
        existing = db.query(QuantityTakeoff).filter(
            QuantityTakeoff.project_id == project_id,
            QuantityTakeoff.division_id == material['division_id'],
            QuantityTakeoff.material_name == material['material_type']
        ).first()
        
        if existing:
            existing.quantity = material['quantity']
            existing.material_cost = material_cost
            existing.labor_hours = labor_info['labor_hours'] if labor_info else 0
            existing.labor_cost = labor_cost
            existing.total_cost = total_cost
            existing.updated_at = datetime.utcnow()
        else:
            quantity_record = QuantityTakeoff(
                project_id=project_id,
                division_id=material['division_id'],
                material_name=material['material_type'],
                material_description=material['material_description'],
                quantity=material['quantity'],
                unit=material['unit'],
                unit_cost=unit_cost,
                material_cost=material_cost,
                labor_hours=labor_info['labor_hours'] if labor_info else 0,
                labor_rate=labor_rate,
                labor_cost=labor_cost,
                total_cost=total_cost
            )
            db.add(quantity_record)
    
    db.commit()
    
    return {"message": "Quantities calculated successfully"}


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@app.get("/api/v1/export/excel/{project_id}")
async def export_to_excel(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export quantity takeoff to Excel"""
    import pandas as pd
    
    quantities = db.query(QuantityTakeoff).filter(
        QuantityTakeoff.project_id == project_id
    ).all()
    
    # Convert to DataFrame
    data = [{
        'Division': q.division_id,
        'Material': q.material_name,
        'Description': q.material_description,
        'Quantity': q.quantity,
        'Unit': q.unit,
        'Material Cost': q.material_cost,
        'Labor Hours': q.labor_hours,
        'Labor Cost': q.labor_cost,
        'Total Cost': q.total_cost
    } for q in quantities]
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    output_file = f"{PROCESSED_DIR}/quantity_takeoff_{project_id}.xlsx"
    df.to_excel(output_file, index=False)
    
    return FileResponse(
        output_file,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=f'quantity_takeoff_{project_id}.xlsx'
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_division_color(division_id: str) -> str:
    """Get color for division"""
    colors = {
        '00': '#FF6B6B', '01': '#FF8E53', '02': '#4ECDC4', '03': '#95E1D3',
        '04': '#F38181', '05': '#AA96DA', '06': '#FCBAD3', '07': '#A8D8EA',
        '08': '#FFD93D', '09': '#6BCB77', '10': '#4D96FF', '11': '#FFB6B9',
        '12': '#FEC8D8', '13': '#957DAD', '14': '#D4A5A5', '20': '#FF9A8B',
        '21': '#FF6A88', '22': '#4A90E2', '23': '#F6A192', '25': '#9B59B6',
        '26': '#F1C40F', '27': '#3498DB', '28': '#E74C3C', '31': '#8B4513',
        '32': '#A9A9A9', '33': '#2C3E50', '34': '#34495E', '35': '#1ABC9C'
    }
    return colors.get(division_id, '#888888')


def get_labor_hours(division_id: str, material_type: str, quantity: float, unit: str, db: Session):
    """Look up labor hours from database"""
    labor_unit = db.query(LaborUnit).filter(
        LaborUnit.csi_code.like(f"{division_id}%"),
        LaborUnit.material_type.ilike(f"%{material_type}%")
    ).first()
    
    if labor_unit:
        total_hours = quantity * labor_unit.labor_hours_per_unit
        return {
            'labor_hours': total_hours,
            'crew_size': labor_unit.crew_size,
            'daily_output': labor_unit.daily_output
        }
    
    return None


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
