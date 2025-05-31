from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path

from api import instances, compare, sync, history, test
from models.database import init_db
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Create data directory for JSON storage
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "instances").mkdir(exist_ok=True)
    
    yield
    # Shutdown
    

app = FastAPI(
    title="Magento CMS Sync API",
    description="API for synchronizing CMS content between Magento 2 instances",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(instances.router, prefix="/api/instances", tags=["instances"])
app.include_router(compare.router, prefix="/api/compare", tags=["compare"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(test.router, prefix="/api/test", tags=["test"])


@app.get("/")
async def root():
    return {"message": "Magento CMS Sync API", "version": "1.0.0"}