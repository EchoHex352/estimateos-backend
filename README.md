# 🚀 ESTIMATEOS PRO - BACKEND DEPLOYMENT GUIDE

## Phase 2: Backend Infrastructure

### **COMPLETE FASTAPI BACKEND WITH:**
✅ User Authentication (JWT)
✅ PDF Processing Engine
✅ Anthropic Claude AI Integration
✅ PostgreSQL Database
✅ All API Endpoints
✅ Railway Deployment Ready

---

## 📦 **PROJECT STRUCTURE**

```
estimateos-backend/
├── main.py                  # FastAPI application & all endpoints
├── models.py                # SQLAlchemy database models
├── database.py              # Database connection & session
├── schemas.py               # Pydantic request/response schemas
├── auth.py                  # JWT authentication module
├── pdf_processor.py         # PDF to image + OCR processing
├── ai_analyzer.py           # Anthropic Claude blueprint analysis
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── railway.json             # Railway deployment config
├── nixpacks.toml           # Nixpacks configuration
├── Procfile                 # Process configuration
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

## 🎯 **FEATURES IMPLEMENTED**

### **✅ Authentication System**
- User registration
- Login with JWT tokens
- Password hashing (bcrypt)
- Protected routes
- Token refresh

### **✅ Project Management**
- Create/Read/Update/Delete projects
- Associate files with projects
- Track project status
- User ownership

### **✅ File Upload & Processing**
- PDF upload (multi-page support)
- Background processing
- PDF to image conversion (300 DPI)
- OCR text extraction (Tesseract)
- Sheet type detection
- Sheet number extraction

### **✅ AI Blueprint Analysis**
- Anthropic Claude integration
- Material detection by division
- Quantity estimation
- Bounding box coordinates
- Confidence scoring
- Mock data for testing

### **✅ Annotation Management**
- Create manual annotations
- Update AI-detected annotations
- Delete annotations
- Page-by-page annotations
- Color-coded by division

### **✅ Quantity Takeoff**
- Automatic quantity aggregation
- Labor hour calculations
- Material cost estimation
- Excel export
- CSV export

### **✅ API Endpoints**
- 30+ RESTful endpoints
- Complete CRUD operations
- Background task processing
- File download responses

---

## 🚀 **DEPLOYMENT TO RAILWAY**

### **Step 1: Prepare Your Code**

```bash
# Navigate to backend directory
cd estimateos-backend

# Initialize git if not already done
git init
git add .
git commit -m "Initial backend commit"
```

### **Step 2: Create Railway Project**

1. Go to https://railway.app
2. Sign up/Login (GitHub recommended)
3. Click "New Project"
4. Select "Deploy from GitHub repo" OR "Empty Project"

### **Step 3: Add PostgreSQL Database**

1. In your Railway project, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway will provision a PostgreSQL database
4. Copy the `DATABASE_URL` from the "Connect" tab

### **Step 4: Deploy Backend**

#### **Option A: Deploy from GitHub** (Recommended)

1. Push your code to GitHub:
```bash
git remote add origin https://github.com/YOUR_USERNAME/estimateos-backend.git
git branch -M main
git push -u origin main
```

2. In Railway:
   - Click "+ New"
   - Select "GitHub Repo"
   - Choose `estimateos-backend`
   - Railway will auto-detect FastAPI and deploy

#### **Option B: Deploy with Railway CLI**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### **Step 5: Configure Environment Variables**

In Railway project settings, add these variables:

```
DATABASE_URL=<auto-filled-by-railway-postgres>
JWT_SECRET_KEY=<generate-a-long-random-string>
ANTHROPIC_API_KEY=<your-claude-api-key>
FRONTEND_URL=https://estimateos-pro.vercel.app
PORT=8000
```

**To generate a secure JWT secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### **Step 6: Verify Deployment**

1. Railway will provide a URL like: `https://estimateos-backend.railway.app`
2. Visit: `https://your-app.railway.app/health`
3. Should return: `{"status": "healthy", ...}`
4. Visit: `https://your-app.railway.app/api/docs` for Swagger docs

---

## 🔌 **CONNECT FRONTEND TO BACKEND**

### **Update Frontend Environment Variables**

In your Vercel project (frontend):

1. Go to Project Settings → Environment Variables
2. Add:
```
VITE_API_URL=https://your-backend.railway.app
```

3. Redeploy frontend:
```bash
vercel --prod
```

### **Update Frontend API Calls**

The frontend should now make requests to:
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Example API call
const response = await fetch(`${API_URL}/api/v1/projects`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

---

## 🧪 **LOCAL DEVELOPMENT**

### **Prerequisites**

- Python 3.10+
- PostgreSQL
- Tesseract OCR
- Poppler (for PDF processing)

**Install System Dependencies:**

```bash
# macOS
brew install tesseract poppler

# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# Windows
# Download and install from official websites
```

### **Setup**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your values

# Create database
createdb estimateos

# Run server
python main.py
```

Visit: http://localhost:8000/api/docs

---

## 📊 **DATABASE SCHEMA**

### **11 Tables Created:**

1. **users** - User accounts and authentication
2. **projects** - Construction projects
3. **uploaded_files** - PDF files and metadata
4. **selected_divisions** - User-selected CSI divisions
5. **pdf_pages** - Individual PDF pages and images
6. **annotations** - Material annotations on pages
7. **material_legend** - Page-by-page material legend
8. **quantity_takeoff** - Aggregated quantities and costs
9. **labor_units** - Labor productivity database
10. **material_pricing** - Material pricing database
11. **rfqs** - Request for quotes

### **Initialize Database**

The database tables are created automatically on first run.

**To add seed data:**

```python
# Create a seed script: seed_data.py
from database import SessionLocal
from models import LaborUnit

db = SessionLocal()

# Add labor units
labor_units = [
    LaborUnit(
        csi_code="03 31 00",
        material_type="Concrete Slab",
        unit="SF",
        labor_hours_per_unit=0.02,
        crew_size=4,
        daily_output=2000,
        source="RSMeans"
    ),
    # Add more...
]

db.add_all(labor_units)
db.commit()
```

---

## 🤖 **AI PROCESSING WORKFLOW**

### **How It Works:**

1. **User Uploads PDF** → `/api/v1/upload`
2. **Background Processing Starts:**
   - Convert PDF pages to images (300 DPI)
   - Extract text with OCR
   - Detect sheet type
   - Store in database
3. **User Triggers AI Analysis** → `/api/v1/process/{file_id}`
4. **For Each Page:**
   - Send image + OCR text to Claude API
   - Claude analyzes blueprint
   - Returns materials with bounding boxes
   - Store annotations in database
5. **Calculate Quantities** → `/api/v1/quantities/calculate`
   - Aggregate annotations by material type
   - Look up labor hours
   - Calculate costs
6. **User Reviews & Edits** via frontend
7. **Export** → Excel, CSV, RFQ

### **Claude API Prompt Structure:**

```
SYSTEM: You are an expert construction estimator...

USER:
- Image: [blueprint page]
- Selected Divisions: [03, 04, 08, etc.]
- OCR Text: [extracted text]
- Task: Identify materials with quantities

RESPONSE: JSON with materials array
```

---

## 🔐 **SECURITY**

### **Implemented:**
✅ JWT token authentication
✅ Password hashing (bcrypt)
✅ CORS protection
✅ SQL injection prevention (ORM)
✅ Environment variable secrets
✅ User ownership validation

### **Best Practices:**
- Never commit `.env` file
- Use strong JWT secret (32+ characters)
- HTTPS only in production (Railway provides)
- Validate all inputs
- Rate limit API calls (add if needed)

---

## 📈 **MONITORING**

### **Health Check:**
```bash
curl https://your-app.railway.app/health
```

### **Railway Logs:**
- View in Railway dashboard
- Real-time log streaming
- Error tracking

### **Database Queries:**
```bash
# Connect to Railway PostgreSQL
railway connect postgres
```

---

## 🐛 **TROUBLESHOOTING**

### **Common Issues:**

**1. PDF Processing Fails**
```
Error: poppler not found
Solution: Install poppler (see prerequisites)
```

**2. OCR Not Working**
```
Error: tesseract not found
Solution: Install tesseract-ocr and set path
```

**3. Database Connection**
```
Error: could not connect to server
Solution: Check DATABASE_URL format (postgresql:// not postgres://)
```

**4. CORS Errors**
```
Error: CORS policy blocked
Solution: Add your frontend URL to CORS origins in main.py
```

**5. AI Analysis Returns Mock Data**
```
Note: Using mock data
Solution: Set ANTHROPIC_API_KEY in environment variables
```

---

## 📝 **API DOCUMENTATION**

### **Interactive Docs:**
- Swagger UI: `https://your-app.railway.app/api/docs`
- ReDoc: `https://your-app.railway.app/api/redoc`

### **Key Endpoints:**

**Authentication:**
```
POST /api/v1/auth/register    - Create account
POST /api/v1/auth/login       - Login (returns JWT)
GET  /api/v1/auth/me          - Get current user
```

**Projects:**
```
GET    /api/v1/projects           - List projects
POST   /api/v1/projects           - Create project
GET    /api/v1/projects/{id}      - Get project
DELETE /api/v1/projects/{id}      - Delete project
```

**Files:**
```
POST /api/v1/upload                    - Upload PDF
GET  /api/v1/files/{file_id}/pages     - Get pages
GET  /api/v1/pages/{page_id}/image     - Get page image
```

**Analysis:**
```
POST /api/v1/process/{file_id}         - Trigger AI analysis
GET  /api/v1/pages/{page_id}/annotations - Get annotations
POST /api/v1/annotations               - Create annotation
PUT  /api/v1/annotations/{id}          - Update annotation
```

**Export:**
```
GET /api/v1/export/excel/{project_id}  - Download Excel
```

---

## 🎯 **NEXT STEPS**

### **Phase 3: Integration** (Coming Next)

1. **Connect Frontend & Backend**
   - Update API calls in React
   - Handle authentication flow
   - Display real data

2. **Enhanced AI Features**
   - Multi-page context
   - Schedule recognition
   - Symbol detection

3. **Labor & Pricing Databases**
   - Integrate RSMeans data
   - Connect vendor APIs
   - Historical pricing

4. **Advanced Features**
   - Real-time collaboration
   - Change order tracking
   - Project analytics
   - Mobile app

---

## 🏆 **PROJECT STATUS**

### **✅ PHASE 2: COMPLETE**
- FastAPI backend ✅
- PostgreSQL database ✅
- PDF processing ✅
- AI integration ✅
- Authentication ✅
- All API endpoints ✅
- Railway deployment ready ✅

### **🚀 READY TO:**
- Deploy to Railway
- Connect to frontend
- Process real blueprints
- Generate estimates

---

## 💡 **TESTING THE API**

### **Using cURL:**

```bash
# Register user
curl -X POST https://your-app.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Login
curl -X POST https://your-app.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Create project (use token from login)
curl -X POST https://your-app.railway.app/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name":"Test Project","client_name":"ABC Construction"}'

# Upload PDF
curl -X POST https://your-app.railway.app/api/v1/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@blueprint.pdf"
```

---

## 📞 **SUPPORT**

### **Documentation:**
- FastAPI Docs: `/api/docs`
- Database Schema: See models.py
- API Examples: See main.py

### **Resources:**
- Railway Docs: https://docs.railway.app
- Anthropic Docs: https://docs.anthropic.com
- FastAPI Docs: https://fastapi.tiangolo.com

---

**Built with ❤️ for the Construction Industry**

*EstimateOS Pro - Making Construction Estimating Intelligent*

**PHASE 2: BACKEND COMPLETE ✅**
**READY FOR DEPLOYMENT 🚀**
