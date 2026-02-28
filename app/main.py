# Context manager for app lifecycle management
from contextlib import asynccontextmanager
# FastAPI web framework imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# ASGI server
import uvicorn

# Import database engine and route modules
from app.db.session import engine
from app.api.routes import homepage, auth, profile
from app.api.routes import posts, subjects, comments, upvote
from app.api.routes import upload, leaderboard, quiz_submission
from app.db.init_db import init_db


# Manage app startup and shutdown operations
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Execute on startup: initialize the database
    print("🚀 Starting Nusa CoNEX API...")
    init_db()
    print("✅ Database initialized")
    # Entry point for shutdown operations (resume after yield)
    yield
    # Execute on shutdown: clean up database connections
    print("👋 Shutting down...")
    engine.dispose()


# Create FastAPI application instance with metadata
app = FastAPI(
    title="Nusa CoNEX API",
    description="Backend API for Nusa CoNEX platform",
    version="2.0.0",
    lifespan=lifespan,  # Register startup/shutdown handlers
)

app.add_middleware(
    CORSMiddleware,
    # Allow local development servers
    allow_origins=[
        "http://localhost:8080", 
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app", # Allow all Vercel domains (preview & prod)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Register all API route modules with their prefixes and tags
app.include_router(homepage.router,          prefix="/homepage",    tags=["Homepage"])
app.include_router(auth.router,              prefix="/auth",        tags=["Authentication"])
app.include_router(profile.router,           prefix="/profile",     tags=["Profile"])
app.include_router(posts.router,             prefix="/posts",       tags=["Posts"])
app.include_router(subjects.router,          prefix="/subjects",    tags=["Subjects"])
app.include_router(upvote.router,                                   tags=["Upvotes"])
app.include_router(comments.router,                                 tags=["Comments"])
app.include_router(upload.router,            prefix="/upload",      tags=["Upload"])
app.include_router(leaderboard.router,       prefix="/leaderboard", tags=["Leaderboard"])
app.include_router(quiz_submission.router,                          tags=["Quizzes"])


# Root endpoint - welcome message
@app.get("/")
def root():
    return {"message": "Welcome to Nusa CoNEX API", "version": "2.0.0", "docs": "/docs"}


# Health check endpoint - used by load balancers/monitoring
@app.get("/health")
def health():
    return {"status": "healthy"}


# Entry point for running the server with auto-reload on code changes
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
