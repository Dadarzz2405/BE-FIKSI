from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.routes import homepage, login
from db.init_db import init_db

app = FastAPI(
    title="My FastAPI Application",
    description="This is a sample FastAPI application with CORS middleware.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(homepage.router, prefix="/homepage", tags=["Homepage"])
app.include_router(login.router, prefix="/auth", tags=["Auth"])

@app.on_event("startup")
def on_startup() -> None:
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
