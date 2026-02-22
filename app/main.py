from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.db.session import engine
from app.api.routes import homepage, auth, profile
from app.api.routes import posts, categories, comments
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Nusa CoNEX API...")
    init_db()
    print("✅ Database initialized successfully")
    yield
    print("👋 Shutting down Nusa CoNEX API...")
    engine.dispose()


app = FastAPI(
    title="Nusa CoNEX API",
    description="Backend API for Nusa CoNEX platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(homepage.router, prefix="/homepage", tags=["Homepage"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(comments.router, tags=["Comments"])  # paths defined inside router


@app.get("/")
def root():
    return {
        "message": "Welcome to Nusa CoNEX API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Nusa CoNEX API"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)