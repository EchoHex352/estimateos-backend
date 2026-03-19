"""
EstimateOS Backend - AI-Powered Construction Estimating
Simplified for Render deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="EstimateOS Backend",
    description="AI-Powered Construction Cost Estimation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "healthy", "service": "EstimateOS Backend"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "EstimateOS"}

@app.get("/api/estimates")
async def list_estimates():
    return {"estimates": [], "total": 0}

@app.post("/api/estimates")
async def create_estimate(project_name: str, sqft: float):
    return {
        "id": 1,
        "project": project_name,
        "sqft": sqft,
        "status": "created"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
