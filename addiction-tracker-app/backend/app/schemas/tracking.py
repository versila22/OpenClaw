from datetime import date
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password_hash: str | None = None


class SubstanceCreate(BaseModel):
    name: str
    category: str
    description: str | None = None
    risk_level: str = "moderate"


class DailyLogCreate(BaseModel):
    user_id: str
    substance_id: str
    log_date: date
    craving_level: int = Field(ge=0, le=10)
    quantity_used: int | None = None
    mood_score: int | None = Field(default=None, ge=0, le=10)
    cbt_notes: str | None = None
    trigger_notes: str | None = None


class AssessmentInput(BaseModel):
    craving_level: int = Field(ge=0, le=10)
    substance_name: str
    city: str | None = None
    postal_code: str | None = None
    cbt_notes: str | None = None
