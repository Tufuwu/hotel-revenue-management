from __future__ import annotations

from datetime import date, datetime
from typing import List

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_type: Mapped[str] = mapped_column(String(100), nullable=False)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    occupancy: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    competitor_hotels: Mapped[List["CompetitorHotel"]] = relationship(
        back_populates="hotel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    daily_metrics: Mapped[List["DailyMetric"]] = relationship(
        back_populates="hotel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pricing_constraint: Mapped["PricingConstraint | None"] = relationship(
        back_populates="hotel",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )
    recommendations: Mapped[List["PricingRecommendation"]] = relationship(
        back_populates="hotel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CompetitorHotel(Base):
    __tablename__ = "competitor_hotels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    room_type: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)

    hotel: Mapped[Hotel] = relationship(back_populates="competitor_hotels")
    rate_snapshots: Mapped[List["CompetitorRateSnapshot"]] = relationship(
        back_populates="competitor_hotel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CompetitorRateSnapshot(Base):
    __tablename__ = "competitor_rate_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_hotel_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_hotels.id"),
        nullable=False,
    )
    stay_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    competitor_hotel: Mapped[CompetitorHotel] = relationship(
        back_populates="rate_snapshots"
    )


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    occupancy: Mapped[float] = mapped_column(Float, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, nullable=False)
    adr: Mapped[float] = mapped_column(Float, nullable=False)
    revpar: Mapped[float] = mapped_column(Float, nullable=False)

    hotel: Mapped[Hotel] = relationship(back_populates="daily_metrics")


class PricingConstraint(Base):
    __tablename__ = "pricing_constraints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hotel_id: Mapped[int] = mapped_column(
        ForeignKey("hotels.id"),
        nullable=False,
        unique=True,
    )
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    max_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    hotel: Mapped[Hotel] = relationship(back_populates="pricing_constraint")


class PricingRecommendation(Base):
    __tablename__ = "pricing_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    recommended_price: Mapped[float] = mapped_column(Float, nullable=False)
    comp_index: Mapped[float] = mapped_column(Float, nullable=False)
    demand_score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hotel: Mapped[Hotel] = relationship(back_populates="recommendations")
    feedback: Mapped["PricingFeedback | None"] = relationship(
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )


class PricingFeedback(Base):
    __tablename__ = "pricing_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("pricing_recommendations.id"),
        nullable=False,
        unique=True,
    )
    executed_price: Mapped[float] = mapped_column(Float, nullable=False)
    actual_occupancy: Mapped[float] = mapped_column(Float, nullable=False)
    actual_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    feedback_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recommendation: Mapped[PricingRecommendation] = relationship(
        back_populates="feedback"
    )
