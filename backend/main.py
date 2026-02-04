from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import Activity
from schemas import ActivityCreate, ActivityResponse


app = FastAPI(
    title=settings.app_name,
    description="Mood-boosting toolkit to help users manage stress and improve mental well-being.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.post("/activities", response_model=ActivityResponse)
async def create_activity(
    activity_data: ActivityCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new activity."""
    activity = Activity(
        name=activity_data.name,
        category=activity_data.category,
        duration_minutes=activity_data.duration_minutes,
        instructions=activity_data.instructions,
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)

    return activity


@app.get("/activities", response_model=list[ActivityResponse])
async def get_activitiesdb (db: AsyncSession = Depends(get_db)):
    """Get all activities."""

    result = await db.execute(select(Activity))
    activities = result.scalars().all()

    return activities


