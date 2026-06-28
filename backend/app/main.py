from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .api.v1 import router as api_v1_router
from .shared.database import engine
from .shared.sql_models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting application...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created")

    yield

    print("Shutting down application...")

app = FastAPI(
    title="Video Analytics API",
    description="API для поиска фрагментов в видео по ключевым словам",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/")
async def root():
    return {
        "message": "Video Analytics API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}