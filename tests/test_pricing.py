import pytest

from app.core.pricing import (
    compute_comp_index,
    compute_demand_score,
    recommend_price,
    safe_mean,
)


def test_compute_comp_index_uses_average_price():
    assert compute_comp_index([110, 115, 130, 125]) == 120


def test_safe_mean_rejects_empty_values():
    with pytest.raises(ValueError):
        safe_mean([])


def test_compute_demand_score_matches_rule():
    assert compute_demand_score(
        base_price=120,
        comp_index=120,
        occupancy=75,
    ) == pytest.approx(0.02)


def test_recommend_price_respects_bounds():
    assert recommend_price(120, 120, 75, min_price=95, max_price=156) == 122.4
