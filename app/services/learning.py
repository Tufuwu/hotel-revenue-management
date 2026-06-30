def compute_learning_adjustment(feedback_history: list[dict]) -> float:
    """Convert recent pricing outcomes into a small adjustment factor."""
    if not feedback_history:
        return 0.0

    # Only the latest few outcomes should influence the next recommendation.
    recent_feedback = feedback_history[:5]
    signals = []
    for feedback in recent_feedback:
        occupancy = feedback["actual_occupancy"]
        executed_price = feedback["executed_price"]
        recommended_price = feedback["recommended_price"]

        if occupancy >= 75 and executed_price >= recommended_price * 0.98:
            signals.append(0.02)
        elif occupancy < 60:
            signals.append(-0.02)
        else:
            signals.append(0.0)

    # Cap learning so feedback cannot overpower the base pricing rule.
    adjustment = sum(signals) / len(signals)
    return max(-0.05, min(0.05, adjustment))


def apply_learning_adjustment(
    recommended_price: float,
    learning_adjustment_factor: float,
    min_price: float,
    max_price: float | None,
) -> float:
    """Apply the learned factor while respecting hotel-specific price bounds."""
    adjusted_price = recommended_price * (1 + learning_adjustment_factor)
    ceiling = max_price if max_price is not None else adjusted_price
    return max(min_price, min(adjusted_price, ceiling))
