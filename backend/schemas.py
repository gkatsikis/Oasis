from pydantic import BaseModel

from models import ActivityCategory, ActivityTime


class ActivityCreate(BaseModel):
    """Request body for creating an activity."""

    name: str
    category: ActivityCategory
    duration_minutes: ActivityTime
    instructions: str


class ActivityResponse(BaseModel):
    """Response body for an activity."""

    id: str
    name: str
    category: ActivityCategory
    duration_minutes: ActivityTime
    instructions: str

    model_config = {"from_attributes": True}
    