import pytest
from fastapi.testclient import TestClient

from app.db.lifecycle import reset_db
from app.main import app


@pytest.fixture()
def client():
    reset_db()
    with TestClient(app) as test_client:
        yield test_client
    reset_db()


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_home_returns_landing_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Hotel Dynamic Pricing MVP" in response.text
    assert "/docs" in response.text


def test_get_hotels_returns_seed_data(client):
    response = client.get("/hotels")

    assert response.status_code == 200
    assert len(response.json()) == 25


def test_predict_price_creates_recommendation(client):
    response = client.post("/predict-price", json={"hotel_id": 2})
    payload = response.json()

    assert response.status_code == 200
    assert payload["hotel_id"] == 2
    assert payload["min_price"] <= payload["recommended_price"] <= payload["max_price"]
    assert payload["learning_adjustment_factor"] == 0.0
    assert payload["feedback_count"] == 0
    assert payload["recommendation_id"] > 0


def test_simulate_pricing_cycle_updates_future_learning(client):
    simulation = client.post("/demo/simulate-pricing-cycle", json={"hotel_id": 2})
    next_prediction = client.post("/predict-price", json={"hotel_id": 2})

    assert simulation.status_code == 200
    assert simulation.json()["feedback"]["actual_occupancy"] == 58.0
    assert next_prediction.status_code == 200
    assert next_prediction.json()["learning_adjustment_factor"] == -0.02
    assert next_prediction.json()["feedback_count"] == 1


def test_missing_hotel_returns_404(client):
    response = client.post("/predict-price", json={"hotel_id": 999})

    assert response.status_code == 404


def test_get_hotel_metrics_returns_seed_metrics(client):
    response = client.get("/hotels/2/metrics")
    payload = response.json()
    hotel = client.get("/hotels").json()[1]

    assert response.status_code == 200
    assert len(payload) == 3
    assert payload[0]["hotel_id"] == 2
    assert payload[0]["metric_date"] == "2026-06-27"
    assert payload[-1]["occupancy"] == hotel["occupancy"]


def test_get_missing_hotel_metrics_returns_404(client):
    response = client.get("/hotels/999/metrics")

    assert response.status_code == 404


def test_create_hotel_metric_records_daily_performance(client):
    response = client.post(
        "/hotels/2/metrics",
        json={
            "metric_date": "2026-06-30",
            "occupancy": 81.0,
            "revenue": 9720.0,
            "adr": 120.0,
            "revpar": 97.2,
        },
    )
    metrics = client.get("/hotels/2/metrics").json()
    hotels = client.get("/hotels").json()

    assert response.status_code == 200
    assert response.json()["metric_date"] == "2026-06-30"
    assert response.json()["occupancy"] == 81.0
    assert len(metrics) == 4
    assert metrics[-1]["revenue"] == 9720.0
    assert hotels[1]["occupancy"] == 81.0


def test_create_hotel_metric_updates_existing_metric_date(client):
    response = client.post(
        "/hotels/2/metrics",
        json={
            "metric_date": "2026-06-29",
            "occupancy": 77.0,
            "revenue": 9240.0,
            "adr": 120.0,
            "revpar": 92.4,
        },
    )
    metrics = client.get("/hotels/2/metrics").json()

    assert response.status_code == 200
    assert len(metrics) == 3
    assert metrics[-1]["metric_date"] == "2026-06-29"
    assert metrics[-1]["occupancy"] == 77.0
    assert metrics[-1]["revenue"] == 9240.0


def test_create_metric_for_missing_hotel_returns_404(client):
    response = client.post(
        "/hotels/999/metrics",
        json={
            "metric_date": "2026-06-30",
            "occupancy": 81.0,
            "revenue": 9720.0,
            "adr": 120.0,
            "revpar": 97.2,
        },
    )

    assert response.status_code == 404


def test_invalid_metric_payload_returns_422(client):
    response = client.post(
        "/hotels/2/metrics",
        json={
            "metric_date": "2026-06-30",
            "occupancy": 101.0,
            "revenue": -1.0,
            "adr": 120.0,
            "revpar": 97.2,
        },
    )

    assert response.status_code == 422


def test_update_pricing_constraints_changes_prediction_bounds(client):
    response = client.patch(
        "/hotels/2/pricing-constraints",
        json={"min_price": 100.0, "max_price": 140.0},
    )
    prediction = client.post("/predict-price", json={"hotel_id": 2}).json()

    assert response.status_code == 200
    assert response.json() == {
        "hotel_id": 2,
        "min_price": 100.0,
        "max_price": 140.0,
    }
    assert prediction["min_price"] == 100.0
    assert prediction["max_price"] == 140.0
    assert prediction["recommended_price"] == 100.0


def test_update_pricing_constraints_can_remove_max_price(client):
    response = client.patch(
        "/hotels/2/pricing-constraints",
        json={"max_price": None},
    )
    prediction = client.post("/predict-price", json={"hotel_id": 2}).json()

    assert response.status_code == 200
    assert response.json()["max_price"] is None
    assert prediction["max_price"] is None
    assert prediction["recommended_price"] >= prediction["min_price"]


def test_update_pricing_constraints_for_missing_hotel_returns_404(client):
    response = client.patch(
        "/hotels/999/pricing-constraints",
        json={"min_price": 100.0},
    )

    assert response.status_code == 404


def test_update_pricing_constraints_rejects_invalid_bounds(client):
    response = client.patch(
        "/hotels/2/pricing-constraints",
        json={"max_price": 50.0},
    )

    assert response.status_code == 400


def test_invalid_pricing_constraints_payload_returns_422(client):
    response = client.patch("/hotels/2/pricing-constraints", json={})

    assert response.status_code == 422


def test_get_hotel_competitors_returns_nearby_structured_prices(client):
    response = client.get("/hotels/2/competitors")
    payload = response.json()

    assert response.status_code == 200
    assert len(payload) == 4
    assert payload[0]["hotel_id"] == 2
    assert payload[0]["distance_km"] <= 5
    assert payload[0]["latest_price"] > 0
    assert payload[0]["latest_stay_date"] == "2026-06-29"


def test_get_competitors_for_missing_hotel_returns_404(client):
    response = client.get("/hotels/999/competitors")

    assert response.status_code == 404


def test_create_competitor_hotel_within_five_kilometers(client):
    hotel = client.get("/hotels").json()[1]
    response = client.post(
        "/hotels/2/competitors",
        json={
            "name": "Nearby Market Hotel",
            "room_type": hotel["room_type"],
            "latitude": hotel["latitude"] + 0.005,
            "longitude": hotel["longitude"] + 0.005,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["name"] == "Nearby Market Hotel"
    assert payload["hotel_id"] == 2
    assert payload["distance_km"] <= 5
    assert payload["latest_price"] is None


def test_create_competitor_hotel_rejects_far_distance(client):
    hotel = client.get("/hotels").json()[1]
    response = client.post(
        "/hotels/2/competitors",
        json={
            "name": "Far Away Hotel",
            "room_type": hotel["room_type"],
            "latitude": hotel["latitude"] + 1.0,
            "longitude": hotel["longitude"] + 1.0,
        },
    )

    assert response.status_code == 400


def test_competitor_rate_snapshot_updates_prediction_market_reference(client):
    competitor = client.get("/hotels/2/competitors").json()[0]
    before_prediction = client.post("/predict-price", json={"hotel_id": 2}).json()
    response = client.post(
        f"/competitors/{competitor['id']}/rates",
        json={
            "stay_date": "2026-06-30",
            "price": 999.0,
            "source": "manual-test",
        },
    )
    after_prediction = client.post("/predict-price", json={"hotel_id": 2}).json()

    assert response.status_code == 200
    assert response.json()["price"] == 999.0
    assert 999.0 in after_prediction["competitor_prices"]
    assert after_prediction["comp_index"] > before_prediction["comp_index"]


def test_create_rate_for_missing_competitor_returns_404(client):
    response = client.post(
        "/competitors/999/rates",
        json={
            "stay_date": "2026-06-30",
            "price": 199.0,
            "source": "manual-test",
        },
    )

    assert response.status_code == 404


def test_get_recommendations_returns_created_predictions(client):
    prediction = client.post("/predict-price", json={"hotel_id": 2}).json()
    response = client.get("/hotels/2/recommendations")
    payload = response.json()

    assert response.status_code == 200
    assert len(payload) == 1
    assert payload[0]["id"] == prediction["recommendation_id"]
    assert payload[0]["hotel_id"] == 2
    assert payload[0]["recommended_price"] == prediction["recommended_price"]


def test_get_missing_hotel_recommendations_returns_404(client):
    response = client.get("/hotels/999/recommendations")

    assert response.status_code == 404


def test_create_pricing_feedback_for_recommendation(client):
    prediction = client.post("/predict-price", json={"hotel_id": 2}).json()
    response = client.post(
        "/pricing-feedback",
        json={
            "recommendation_id": prediction["recommendation_id"],
            "executed_price": prediction["recommended_price"],
            "actual_occupancy": 80.0,
            "actual_revenue": round(prediction["recommended_price"] * 80.0, 2),
            "feedback_note": "accepted by revenue manager",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["recommendation_id"] == prediction["recommendation_id"]
    assert payload["executed_price"] == prediction["recommended_price"]
    assert payload["actual_occupancy"] == 80.0
    assert payload["feedback_note"] == "accepted by revenue manager"


def test_create_feedback_for_missing_recommendation_returns_404(client):
    response = client.post(
        "/pricing-feedback",
        json={
            "recommendation_id": 999,
            "executed_price": 156.0,
            "actual_occupancy": 80.0,
            "actual_revenue": 12480.0,
        },
    )

    assert response.status_code == 404


def test_invalid_predict_price_payload_returns_422(client):
    response = client.post("/predict-price", json={"hotel_id": 0})

    assert response.status_code == 422


def test_invalid_feedback_payload_returns_422(client):
    response = client.post(
        "/pricing-feedback",
        json={
            "recommendation_id": 1,
            "executed_price": -1.0,
            "actual_occupancy": 101.0,
            "actual_revenue": 0.0,
        },
    )

    assert response.status_code == 422
