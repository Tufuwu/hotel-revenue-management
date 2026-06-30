def get_seed_hotels() -> list[dict]:
    return generate_seed_hotels(start_id=1, count=25)


def generate_seed_hotels(start_id: int, count: int) -> list[dict]:
    room_types = ["standard", "superior", "deluxe", "family", "suite"]
    hotels = []
    base_latitude = 31.2304
    base_longitude = 121.4737

    for offset in range(count):
        hotel_id = start_id + offset
        room_type = room_types[offset % len(room_types)]
        base_price = float(85 + (offset % 10) * 12 + (offset // 10) * 18)
        occupancy = float(50 + (offset * 7) % 42)
        min_price = round(base_price * 0.75, 2)
        max_price = round(base_price * 1.35, 2)
        latitude = round(base_latitude + (offset % 5) * 0.018, 6)
        longitude = round(base_longitude + (offset // 5) * 0.018, 6)

        hotels.append(
            {
                "hotel_id": hotel_id,
                "room_type": room_type,
                "base_price": base_price,
                "occupancy": occupancy,
                "latitude": latitude,
                "longitude": longitude,
                "min_price": min_price,
                "max_price": max_price,
                "competitor_hotels": generate_competitor_hotels(
                    hotel_id,
                    room_type,
                    base_price,
                    latitude,
                    longitude,
                ),
                "daily_metrics": generate_daily_metrics(base_price, occupancy),
            }
        )

    return hotels


def generate_daily_metrics(base_price: float, occupancy: float) -> list[dict]:
    metrics = []
    dates = ["2026-06-27", "2026-06-28", "2026-06-29"]

    for index, metric_date in enumerate(dates):
        daily_occupancy = max(30.0, min(96.0, occupancy - 4 + index * 2))
        adr = round(base_price * (0.98 + index * 0.01), 2)
        revenue = round(adr * daily_occupancy, 2)
        revpar = round(adr * daily_occupancy / 100, 2)

        metrics.append(
            {
                "metric_date": metric_date,
                "occupancy": round(daily_occupancy, 2),
                "revenue": revenue,
                "adr": adr,
                "revpar": revpar,
            }
        )

    return metrics


def generate_competitor_hotels(
    hotel_id: int,
    room_type: str,
    base_price: float,
    latitude: float,
    longitude: float,
) -> list[dict]:
    competitors = []
    offsets = [
        (0.006, 0.004, 0.82),
        (-0.009, 0.007, 1.08),
        (0.012, -0.006, 1.22),
        (-0.014, -0.011, 1.86),
    ]

    for index, (lat_delta, lon_delta, distance_km) in enumerate(offsets, start=1):
        price_anchor = base_price * (0.94 + index * 0.03)
        competitors.append(
            {
                "name": f"Competitor {hotel_id}-{index}",
                "room_type": room_type,
                "latitude": round(latitude + lat_delta, 6),
                "longitude": round(longitude + lon_delta, 6),
                "distance_km": distance_km,
                "rate_snapshots": generate_competitor_rate_snapshots(price_anchor),
            }
        )

    return competitors


def generate_competitor_rate_snapshots(price_anchor: float) -> list[dict]:
    dates = ["2026-06-27", "2026-06-28", "2026-06-29"]
    return [
        {
            "stay_date": stay_date,
            "price": round(price_anchor * (0.98 + index * 0.02), 2),
            "source": "seed",
        }
        for index, stay_date in enumerate(dates)
    ]
