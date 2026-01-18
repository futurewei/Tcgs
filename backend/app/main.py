from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import api_router
from .database import engine, Base
from .config import get_settings

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TCGS API",
    description="Topic & Capacity Governance System API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "TCGS API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
