from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    email: Mapped[str] = mapped_column(String(255), default="")
    business_role: Mapped[str] = mapped_column(String(50), default="Mitarbeiter")
    age: Mapped[int] = mapped_column(Integer, default=18)

    password_hash: Mapped[str] = mapped_column(String(500), default="")
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)

    time_entries: Mapped[list[TimeEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class TimeEntry(Base):
    __tablename__ = "time_entries"
    __table_args__ = (UniqueConstraint("user_id", "work_date", name="uq_user_work_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    work_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column()
    end_time: Mapped[time] = mapped_column()

    lunch_start: Mapped[time | None] = mapped_column(nullable=True)
    lunch_end: Mapped[time | None] = mapped_column(nullable=True)

    short_break_min: Mapped[int] = mapped_column(Integer, default=0)

    net_hours: Mapped[float] = mapped_column(Float, default=0.0)
    comment: Mapped[str] = mapped_column(String(1000), default="")

    approved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="time_entries")
