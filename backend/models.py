import enum
from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Enum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP


class ActivityCategory(str, enum.Enum):
    """Categories for mood boosting activities"""

    BREATHWORK = "breathwork"
    GROUNDING = "grounding"
    JOURNALING = "journaling"
    SENSORY_MINDFULNESS = "sensory_mindfulness"
    MOVEMENT = "movement"
    NATURE = "nature"
    CONNECTION = "connection"
    COLD_EXPOSURE = "cold_exposure"
    MEDITATION = "meditation"


class ActivityTime(int, enum.Enum):
    """Predefined time durations for activities in minutes"""

    FIVE_MINUTES = 5
    TEN_MINUTES = 10
    FIFTEEN_MINUTES = 15
    TWENTY_MINUTES = 20
    THIRTY_MINUTES = 30


class SessionOutcome(str, enum.Enum):
    """Outcomes for mood boosting sessions"""

    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXITED_EARLY = "exited_early"


class Base(DeclarativeBase):
    """Base class for all models to indicate they are database tables and to inherit common functionality."""
    pass


class User(Base):
    """A user of Oasis."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda:str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.display_name} ({self.email})>"


class Activity(Base):
    """A single mood-boosting activity."""

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda:str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[ActivityCategory] = mapped_column(Enum(ActivityCategory), nullable=False)
    duration_minutes: Mapped[ActivityTime] = mapped_column(Enum(ActivityTime), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    flow_steps: Mapped[List["FlowStep"]] = relationship("FlowStep", back_populates="activity", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Activity {self.name} ({self.category.value})>"
    

class Flow(Base):
    """A pre-built sequence of activities.
    
    One flow for now, later there will be options.
    """

    __tablename__ = "flows"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda:str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    steps: Mapped[List["FlowStep"]] = relationship("FlowStep", back_populates="flow", lazy="selectin", order_by="FlowStep.order")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="flow", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Flow {self.name}>"
    

class FlowStep(Base):
    """A single step within a flow, linking to an activity and check-in behavior."""

    __tablename__ = "flow_steps"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda:str(uuid4()))
    flow_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("flows.id", ondelete="CASCADE"), nullable=False)
    activity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    has_check_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    flow: Mapped["Flow"] = relationship("Flow", back_populates="steps")
    activity: Mapped["Activity"] = relationship("Activity", back_populates="flow_steps")
    step_logs: Mapped[List["SessionStepLog"]] = relationship("SessionStepLog", back_populates="flow_step", lazy="selectin")

    def __repr__(self) -> str:
        return f"<FlowStep flow={self.flow_id} order={self.order}>"
    

class Session(Base):
    """
    A user going through a flow.
    
    Tracks when they started, when they finished, and how it ended.
    """
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    flow_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("flows.id", ondelete="SET NULL"), nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    outcome: Mapped[SessionOutcome | None] = mapped_column(Enum(SessionOutcome), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")
    flow: Mapped["Flow | None"] = relationship("Flow", back_populates="sessions")
    step_logs: Mapped[List["SessionStepLog"]] = relationship("SessionStepLog", back_populates="session", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Session user={self.user_id} outcome={self.outcome}>"
    

class SessionStepLog(Base):
    """Tracks a user's progress through each step of a session."""

    __tablename__ = "session_step_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    flow_step_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("flow_steps.id", ondelete="SET NULL"), nullable=True)

    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped["Session"] = relationship("Session", back_populates="step_logs")
    flow_step: Mapped["FlowStep | None"] = relationship("FlowStep", back_populates="step_logs")

    def __repr__(self) -> str:
        status = "skipped" if self.skipped else "completed" if self.completed_at else "in_progress"
        return f"<SessionStepLog session={self.session_id} status={status}>"
