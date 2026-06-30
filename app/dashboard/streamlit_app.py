from datetime import date

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


st.set_page_config(page_title="酒店动态定价 MVP", layout="wide")
init_db()

st.title("酒店动态定价 MVP")

db = SessionLocal()
hotels = list_hotels(db)
if not hotels:
    db.close()
    st.error("SQLite 中没有酒店数据。")
    st.stop()

with st.sidebar:
    st.header("数据选择")
    selected_hotel_id = st.selectbox(
        "酒店 / 房型",
        [hotel["id"] for hotel in hotels],
        format_func=lambda hotel_id: next(
            f"{hotel['id']} - {hotel['room_type']}"
            for hotel in hotels
            if hotel["id"] == hotel_id
        ),
    )

pricing_input = get_hotel_pricing_input(db, selected_hotel_id)
if pricing_input is None:
    db.close()
    st.error("SQLite 中没有找到所选酒店。")
    st.stop()

with st.sidebar:
    st.divider()
    st.header("演示操作")
    if st.button("模拟新增调价记录", use_container_width=True):
        result = simulate_pricing_cycle(db, selected_hotel_id)
        if result is None:
            st.error("模拟失败：未找到酒店。")
        else:
            st.success(
                f"已生成推荐 #{result.prediction.recommendation_id}，"
                f"并写入反馈 #{result.feedback.id}。"
            )
            st.rerun()

    st.divider()
    st.header("录入每日经营数据")
    with st.form("daily_metric_form"):
        metric_date = st.date_input("日期", value=date.today())
        occupancy_value = st.number_input(
            "入住率",
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
            "收入",
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
        submitted_metric = st.form_submit_button("保存经营数据")

    if submitted_metric:
        metric = record_hotel_daily_metric(
            db,
            selected_hotel_id,
            DailyMetricRequest(
                metric_date=metric_date,
                occupancy=occupancy_value,
                revenue=revenue_value,
                adr=adr_value,
                revpar=revpar_value,
            ),
        )
        if metric is None:
            st.error("保存失败：未找到酒店。")
        else:
            st.success("每日经营数据已保存。")
            st.rerun()

    st.divider()
    st.header("价格约束")
    with st.form("pricing_constraint_form"):
        min_price_value = st.number_input(
            "最低价格",
            min_value=0.01,
            value=float(pricing_input["min_price"]),
            step=10.0,
        )
        use_max_price = st.checkbox(
            "启用最高价格",
            value=pricing_input["max_price"] is not None,
        )
        max_price_value = st.number_input(
            "最高价格",
            min_value=0.01,
            value=float(pricing_input["max_price"] or pricing_input["base_price"] * 1.3),
            step=10.0,
            disabled=not use_max_price,
        )
        submitted_constraint = st.form_submit_button("保存价格约束")

    if submitted_constraint:
        try:
            constraint = revise_pricing_constraint(
                db,
                selected_hotel_id,
                PricingConstraintRequest(
                    min_price=min_price_value,
                    max_price=max_price_value if use_max_price else None,
                ),
            )
        except ValueError as error:
            st.error(str(error))
        else:
            if constraint is None:
                st.error("保存失败：未找到酒店。")
            else:
                st.success("价格约束已更新。")
                st.rerun()

pricing_input = get_hotel_pricing_input(db, selected_hotel_id)
base_price = pricing_input["base_price"]
occupancy = pricing_input["occupancy"]
competitor_prices = pricing_input["competitor_prices"]
competitor_hotels = list_competitor_hotels(db, selected_hotel_id) or []
min_price = pricing_input["min_price"]
max_price = pricing_input["max_price"]
feedback_history = list_pricing_feedback_for_hotel(db, selected_hotel_id)
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
metric_cols[0].metric("基础价格", f"${base_price:,.2f}")
metric_cols[1].metric("推荐价格", f"${recommended_price:,.2f}")
metric_cols[2].metric("竞品均价", f"${comp_index:,.2f}")
metric_cols[3].metric("需求评分", f"{demand_score:.2f}")
metric_cols[4].metric("最低价格", f"${min_price:,.2f}")
metric_cols[5].metric("学习调整", f"{learning_adjustment_factor:.2%}")

chart_col, input_col = st.columns([2, 1])

with chart_col:
    st.subheader("5 公里内竞品最新价格")
    st.bar_chart(
        {
            competitor["name"]: competitor["latest_price"]
            for competitor in competitor_hotels
            if competitor["latest_price"] is not None
        }
    )

with input_col:
    st.subheader("当前定价输入")
    st.json(pricing_input)

st.subheader("周边 5 公里竞品酒店")
st.dataframe(
    competitor_hotels,
    column_config={
        "id": "竞品 ID",
        "hotel_id": "本酒店 ID",
        "name": "竞品酒店",
        "room_type": "房型",
        "latitude": "纬度",
        "longitude": "经度",
        "distance_km": "距离 km",
        "latest_price": "最新价格",
        "latest_stay_date": "入住日期",
    },
    use_container_width=True,
)

st.subheader("每日经营数据")
daily_metrics = list_daily_metrics(db, selected_hotel_id)
st.dataframe(
    daily_metrics,
    column_config={
        "id": "ID",
        "hotel_id": "酒店 ID",
        "metric_date": "日期",
        "occupancy": "入住率",
        "revenue": "收入",
        "adr": "平均房价 ADR",
        "revpar": "每间可售房收入 RevPAR",
    },
    use_container_width=True,
)

st.subheader("反馈学习样本")
st.caption("点击“模拟新增调价记录”后，系统会生成推荐记录并写入模拟反馈。")
st.dataframe(
    feedback_history,
    column_config={
        "id": "反馈 ID",
        "recommendation_id": "推荐 ID",
        "executed_price": "实际执行价格",
        "actual_occupancy": "实际入住率",
        "actual_revenue": "实际收入",
        "recommended_price": "原推荐价格",
        "feedback_note": "备注",
        "created_at": "反馈时间",
    },
    use_container_width=True,
)

db.close()
