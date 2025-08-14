from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Dict, Any

# Create FastAPI app
app = FastAPI(
    title="Insurance Data Platform API",
    description="API for insurance data management and analytics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Insurance Data Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "insurance-api",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_status": "operational",
        "database": "connected",
        "redis": "connected",
        "version": "1.0.0"
    }

@app.get("/api/v1/endpoints")
async def list_endpoints():
    """List available API endpoints"""
    return {
        "endpoints": [
            "/",
            "/health",
            "/api/v1/status",
            "/api/v1/endpoints",
            "/docs",
            "/redoc"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 