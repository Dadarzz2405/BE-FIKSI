from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routes import homepage, auth, profile
from app.db.init_db import init_db

# Create FastAPI app
app = FastAPI(
    title="Nusa CoNEX API",
    description="Backend API for Nusa CoNEX platform with authentication",
    version="1.0.0"
)

# CORS Middleware - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

# Homepage routes (public)
app.include_router(
    homepage.router,
    prefix="/homepage",
    tags=["Homepage"]
)

# Authentication routes (public)
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Profile routes (public/protected)
app.include_router(
    profile.router,
    prefix="/profile",
    tags=["Profile"]
)


# ============================================================================
# LIFECYCLE EVENTS
# ============================================================================

@app.on_event("startup")
def on_startup() -> None:
    """Initialize database on application startup."""
    print("🚀 Starting Nusa CoNEX API...")
    init_db()
    print("✅ Database initialized successfully")


@app.on_event("shutdown")
def on_shutdown() -> None:
    """Cleanup on application shutdown."""
    print("👋 Shutting down Nusa CoNEX API...")


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint - API information."""
    return {
        "message": "Welcome to Nusa CoNEX API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "homepage": "/homepage",
            "auth": "/auth",
            "profile": "/profile"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Nusa CoNEX API"
    }


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable hot reload for development
    )