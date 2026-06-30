import asyncio
from datetime import date
from typing import Awaitable, TypeVar

import streamlit as st

from app.core.pricing import compute_comp_index, compute_demand_score, recommend_price
from app.db.competitors import list_competitor_hotels
from app.db.feedback import list_pricing_feedback_for_hotel
from app.db.hotels import get_hotel_pricing_input, list_hotels
from app.db.lifecycle import init_db
from app.db.metrics import list_daily_metrics
from app.db.session import SessionLocal
from app.schemas import DailyMetricRequest, PricingConstraintRequest
from app.services.demo import simulate_pricing_cycle
from app.services.hotels import record_hotel_daily_metric, revise_pricing_constraint
from app.services.learning import apply_learning_adjustment, compute_learning_adjustment


T = TypeVar("T")


def run_async(awaitable: Awaitable[T]) -> T:
    return asyncio.run(awaitable)


async def load_hotels() -> list[dict]:
    await init_db()
    async with SessionLocal() as db:
        return await list_hotels(db)


async def load_dashboard_data(hotel_id: int) -> dict | None:
    async with SessionLocal() as db:
        pricing_input = await get_hotel_pricing_input(db, hotel_id)
        if pricing_input is None:
            return None
        return {
            "pricing_input": pricing_input,
            "competitors": await list_competitor_hotels(db, hotel_id) or [],
            "feedback": await list_pricing_feedback_for_hotel(db, hotel_id),
            "metrics": await list_daily_metrics(db, hotel_id),
        }


async def run_simulation(hotel_id: int):
    async with SessionLocal() as db:
        return await simulate_pricing_cycle(db, hotel_id)


async def save_daily_metric(hotel_id: int, payload: DailyMetricRequest):
    async with SessionLocal() as db:
        return await record_hotel_daily_metric(db, hotel_id, payload)


async def save_pricing_constraint(hotel_id: int, payload: PricingConstraintRequest):
    async with SessionLocal() as db:
        return await revise_pricing_constraint(db, hotel_id, payload)


st.set_page_config(page_title="Hotel Dynamic Pricing MVP", layout="wide")
st.title("Hotel Dynamic Pricing MVP")

hotels = run_async(load_hotels())
if not hotels:
    st.error("No hotel data found in SQLite.")
    st.stop()

with st.sidebar:
    st.header("Data")
    selected_hotel_id = st.selectbox(
        "Hotel / room type",
        [hotel["id"] for hotel in hotels],
        format_func=lambda hotel_id: next(
            f"{hotel['id']} - {hotel['room_type']}"
            for hotel in hotels
            if hotel["id"] == hotel_id
        ),
    )

dashboard_data = run_async(load_dashboard_data(selected_hotel_id))
if dashboard_data is None:
    st.error("Selected hotel was not found.")
    st.stop()

pricing_input = dashboard_data["pricing_input"]

with st.sidebar:
    st.divider()
    st.header("Demo")
    if st.button("Simulate pricing cycle", use_container_width=True):
        result = run_async(run_simulation(selected_hotel_id))
        if result is None:
            st.error("Simulation failed: hotel not found.")
        else:
            st.success(
                f"Created recommendation #{result.prediction.recommendation_id} "
                f"and feedback #{result.feedback.id}."
            )
            st.rerun()

    st.divider()
    st.header("Daily metric")
    with st.form("daily_metric_form"):
        metric_date = st.date_input("Date", value=date.today())
        occupancy_value = st.number_input(
            "Occupancy",
            min_value=0.0,
            max_value=100.0,
            value=float(pricing_input["occupancy"]),
            step=1.0,
        )
        adr_value = st.number_input(
            "ADR",
            min_value=0.0,
            value=float(pricing_input["base_price"]),
            step=10.0,
        )
        revenue_value = st.number_input(
            "Revenue",
            min_value=0.0,
            value=round(adr_value * occupancy_value, 2),
            step=100.0,
        )
        revpar_value = st.number_input(
            "RevPAR",
            min_value=0.0,
            value=round(adr_value * occupancy_value / 100, 2),
            step=10.0,
        )
        submitted_metric = st.form_submit_button("Save metric")

    if submitted_metric:
        metric = run_async(
            save_daily_metric(
                selected_hotel_id,
                DailyMetricRequest(
                    metric_date=metric_date,
                    occupancy=occupancy_value,
                    revenue=revenue_value,
                    adr=adr_value,
                    revpar=revpar_value,
                ),
            )
        )
        if metric is None:
            st.error("Save failed: hotel not found.")
        else:
            st.success("Daily metric saved.")
            st.rerun()

    st.divider()
    st.header("Price bounds")
    with st.form("pricing_constraint_form"):
        min_price_value = st.number_input(
            "Minimum price",
            min_value=0.01,
            value=float(pricing_input["min_price"]),
            step=10.0,
        )
        use_max_price = st.checkbox(
            "Enable maximum price",
            value=pricing_input["max_price"] is not None,
        )
        max_price_value = st.number_input(
            "Maximum price",
            min_value=0.01,
            value=float(pricing_input["max_price"] or pricing_input["base_price"] * 1.3),
            step=10.0,
            disabled=not use_max_price,
        )
        submitted_constraint = st.form_submit_button("Save bounds")

    if submitted_constraint:
        try:
            constraint = run_async(
                save_pricing_constraint(
                    selected_hotel_id,
                    PricingConstraintRequest(
                        min_price=min_price_value,
                        max_price=max_price_value if use_max_price else None,
                    ),
                )
            )
        except ValueError as error:
            st.error(str(error))
        else:
            if constraint is None:
                st.error("Save failed: hotel not found.")
            else:
                st.success("Price bounds saved.")
                st.rerun()

base_price = pricing_input["base_price"]
occupancy = pricing_input["occupancy"]
competitor_prices = pricing_input["competitor_prices"]
competitor_hotels = dashboard_data["competitors"]
min_price = pricing_input["min_price"]
max_price = pricing_input["max_price"]
feedback_history = dashboard_data["feedback"]
learning_adjustment_factor = compute_learning_adjustment(feedback_history)

comp_index = compute_comp_index(competitor_prices)
demand_score = compute_demand_score(base_price, comp_index, occupancy)
rule_price = recommend_price(
    base_price,
    comp_index,
    occupancy,
    min_price=min_price,
    max_price=max_price,
)
recommended_price = apply_learning_adjustment(
    rule_price,
    learning_adjustment_factor,
    min_price,
    max_price,
)

metric_cols = st.columns(6)
metric_cols[0].metric("Base price", f"${base_price:,.2f}")
metric_cols[1].metric("Recommended", f"${recommended_price:,.2f}")
metric_cols[2].metric("Market index", f"${comp_index:,.2f}")
metric_cols[3].metric("Demand score", f"{demand_score:.2f}")
metric_cols[4].metric("Minimum", f"${min_price:,.2f}")
metric_cols[5].metric("Learning", f"{learning_adjustment_factor:.2%}")

chart_col, input_col = st.columns([2, 1])

with chart_col:
    st.subheader("Nearby competitor prices")
    st.bar_chart(
        {
            competitor["name"]: competitor["latest_price"]
            for competitor in competitor_hotels
            if competitor["latest_price"] is not None
        }
    )

with input_col:
    st.subheader("Current pricing input")
    st.json(pricing_input)

st.subheader("Competitor hotels within 5 km")
st.dataframe(competitor_hotels, use_container_width=True)

st.subheader("Daily operating metrics")
st.dataframe(dashboard_data["metrics"], use_container_width=True)

st.subheader("Feedback samples")
st.dataframe(feedback_history, use_container_width=True)
