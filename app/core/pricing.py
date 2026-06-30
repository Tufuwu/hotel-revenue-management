from statistics import mean


def clip(value: float, min_value: float, max_value: float) -> float:
    """Keep a numeric value inside the configured business bounds."""
    return max(min_value, min(value, max_value))


def safe_mean(values: list[float]) -> float:
    """Calculate an average only when the pricing signal has source data."""
    if not values:
        raise ValueError("values must not be empty")
    return mean(values)


def compute_comp_index(prices: list[float]) -> float:
    """Use the average nearby competitor rate as the market reference price."""
    return safe_mean(prices)


def compute_demand_score(
    base_price: float,
    comp_index: float,
    occupancy: float,
) -> float:
    """Blend market gap and occupancy into a simple demand pressure score."""
    competitor_gap = (comp_index - base_price) / base_price
    occupancy_gap = (occupancy - 70) / 100
    return (0.6 * competitor_gap) + (0.4 * occupancy_gap)


def recommend_price(
    base_price: float,
    comp_index: float,
    occupancy: float,
    min_price: float | None = None,
    max_price: float | None = None,
) -> float:
    """Recommend a bounded room price from base price, market, and occupancy."""
    demand_score = compute_demand_score(base_price, comp_index, occupancy)
    recommended_price = base_price * (1 + demand_score)
    floor_price = min_price if min_price is not None else base_price * 0.7
    ceiling_price = max_price if max_price is not None else base_price * 1.3
    return clip(recommended_price, floor_price, ceiling_price)
