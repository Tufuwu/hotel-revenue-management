from app.services.learning import (
    apply_learning_adjustment,
    compute_learning_adjustment,
)
from app.services.recommendations import (
    get_pricing_decision,
)


def test_learning_adjustment_is_zero_without_feedback():
    assert compute_learning_adjustment([]) == 0.0


def test_learning_adjustment_increases_after_strong_feedback():
    feedback = [
        {
            "actual_occupancy": 82,
            "executed_price": 156,
            "recommended_price": 156,
        }
    ]
    assert compute_learning_adjustment(feedback) == 0.02


def test_learning_adjustment_decreases_after_weak_occupancy():
    feedback = [
        {
            "actual_occupancy": 55,
            "executed_price": 130,
            "recommended_price": 140,
        }
    ]
    assert compute_learning_adjustment(feedback) == -0.02


def test_apply_learning_adjustment_respects_price_bounds():
    assert apply_learning_adjustment(156, 0.02, min_price=95, max_price=156) == 156


def test_pricing_decision_labels_direction():
    assert get_pricing_decision(130, 120) == "raise_price"
    assert get_pricing_decision(110, 120) == "lower_price"
    assert get_pricing_decision(121, 120) == "keep_price"
