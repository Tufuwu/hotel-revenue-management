from app.db.model import (
    CompetitorHotel,
    CompetitorRateSnapshot,
    DailyMetric,
    PricingFeedback,
    PricingRecommendation,
)


def recommendation_to_dict(recommendation: PricingRecommendation) -> dict:
    return {
        "id": recommendation.id,
        "hotel_id": recommendation.hotel_id,
        "recommended_price": recommendation.recommended_price,
        "comp_index": recommendation.comp_index,
        "demand_score": recommendation.demand_score,
        "reason": recommendation.reason,
        "created_at": recommendation.created_at,
    }


def daily_metric_to_dict(metric: DailyMetric) -> dict:
    return {
        "id": metric.id,
        "hotel_id": metric.hotel_id,
        "metric_date": metric.metric_date,
        "occupancy": metric.occupancy,
        "revenue": metric.revenue,
        "adr": metric.adr,
        "revpar": metric.revpar,
    }


def get_latest_snapshot(
    snapshots: list[CompetitorRateSnapshot],
) -> CompetitorRateSnapshot | None:
    if not snapshots:
        return None
    return max(snapshots, key=lambda snapshot: (snapshot.stay_date, snapshot.id))


def competitor_hotel_to_dict(competitor: CompetitorHotel) -> dict:
    latest_snapshot = get_latest_snapshot(competitor.rate_snapshots)
    return {
        "id": competitor.id,
        "hotel_id": competitor.hotel_id,
        "name": competitor.name,
        "room_type": competitor.room_type,
        "latitude": competitor.latitude,
        "longitude": competitor.longitude,
        "distance_km": competitor.distance_km,
        "latest_price": latest_snapshot.price if latest_snapshot else None,
        "latest_stay_date": latest_snapshot.stay_date if latest_snapshot else None,
    }


def competitor_rate_snapshot_to_dict(snapshot: CompetitorRateSnapshot) -> dict:
    return {
        "id": snapshot.id,
        "competitor_hotel_id": snapshot.competitor_hotel_id,
        "stay_date": snapshot.stay_date,
        "price": snapshot.price,
        "source": snapshot.source,
        "collected_at": snapshot.collected_at,
    }


def feedback_to_dict(feedback: PricingFeedback) -> dict:
    return {
        "id": feedback.id,
        "recommendation_id": feedback.recommendation_id,
        "executed_price": feedback.executed_price,
        "actual_occupancy": feedback.actual_occupancy,
        "actual_revenue": feedback.actual_revenue,
        "feedback_note": feedback.feedback_note,
        "created_at": feedback.created_at,
    }
