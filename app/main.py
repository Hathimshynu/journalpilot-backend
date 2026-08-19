from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.auth import router as auth_router
from app.core.database import Base, engine
from app.core.config import settings
from app.api.manuscripts import (router as manuscripts_router)

# Import models so SQLAlchemy knows about them
from app.models.user import User


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="JournalPilot AI API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(manuscripts_router)


@app.get("/")
def root():
    return {
        "message": "JournalPilot AI API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }
    
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)