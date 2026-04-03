import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "substance_id", "log_date", name="uq_daily_log_user_substance_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    substance_id: Mapped[str] = mapped_column(String(36), ForeignKey("substances.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    craving_level: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cbt_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="daily_logs")
    substance = relationship("Substance", back_populates="daily_logs")
