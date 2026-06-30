# 酒店收益管理动态定价 MVP

这是一个用于演示酒店收益管理闭环的 FastAPI + SQLite + Streamlit 项目。系统内置示例酒店、竞品价格、每日经营指标、价格约束、推荐记录和反馈记录，并用一套透明的规则生成动态房价建议。

核心流程：

```text
酒店基础数据 + 竞品价格 + 入住率
        -> 生成推荐价格
        -> 保存推荐记录
        -> 写入执行反馈
        -> 后续推荐加入学习调整
```

## 快速启动

安装依赖：

```bash
pip install -r requirements.txt
```

一键重置数据、启动 API 和 Streamlit，并打开浏览器：

```bash
python scripts/run_demo.py --reset-db --open
```

启动后访问：

```text
API 文档: http://127.0.0.1:8000/docs
Streamlit 看板: http://127.0.0.1:8501
```

停止服务：在运行 demo 的终端按 `Ctrl+C`。

## 手动运行

只初始化或重置 SQLite 数据库：

```bash
python scripts/init_db.py --reset
```

只启动 FastAPI：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

只启动 Streamlit：

```bash
streamlit run app/dashboard/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

运行测试：

```bash
python -m pytest
```

## 功能

- 初始化 25 个示例酒店和房型。
- 维护 5 公里范围内的竞品酒店和竞品价格快照。
- 记录每日入住率、收入、ADR、RevPAR。
- 支持最低价格和最高价格约束。
- 根据竞品均价和入住率生成推荐价格。
- 保存推荐记录和实际执行反馈。
- 根据最近反馈对后续推荐做小幅学习调整。
- 提供 FastAPI 接口和 Streamlit 演示看板。

## Streamlit 看板

Streamlit 页面用于演示业务操作：

- 选择酒店和房型。
- 查看基础价格、推荐价格、竞品均价、需求评分、最低价格、学习调整。
- 录入或更新每日经营指标。
- 修改价格上下限。
- 查看 5 公里内竞品酒店及最新价格。
- 查看推荐反馈样本。
- 点击“模拟新增调价记录”，生成一条推荐记录和一条模拟反馈记录。

推荐价格不一定每次新增记录都会变化。如果价格被最低价或最高价限制住，学习调整可能已经生效，但最终显示价格仍然不变。

## API 概览

基础接口：

```http
GET /
GET /health
```

酒店和经营数据：

```http
GET /hotels
GET /hotels/{hotel_id}/metrics
POST /hotels/{hotel_id}/metrics
PATCH /hotels/{hotel_id}/pricing-constraints
```

竞品数据：

```http
GET /hotels/{hotel_id}/competitors
POST /hotels/{hotel_id}/competitors
POST /competitors/{competitor_id}/rates
```

推荐和反馈：

```http
POST /predict-price
GET /hotels/{hotel_id}/recommendations
POST /pricing-feedback
POST /demo/simulate-pricing-cycle
```

## 常用请求示例

生成推荐价格：

```json
{
  "hotel_id": 2
}
```

新增或更新每日经营指标：

```json
{
  "metric_date": "2026-06-30",
  "occupancy": 81.0,
  "revenue": 9720.0,
  "adr": 120.0,
  "revpar": 97.2
}
```

更新价格约束：

```json
{
  "min_price": 100.0,
  "max_price": 140.0
}
```

取消最高价格限制：

```json
{
  "max_price": null
}
```

新增竞品酒店：

```json
{
  "name": "Nearby Market Hotel",
  "room_type": "deluxe",
  "latitude": 31.2364,
  "longitude": 121.4777
}
```

新增竞品价格快照：

```json
{
  "stay_date": "2026-06-30",
  "price": 188.0,
  "source": "manual"
}
```

写入推荐执行反馈：

```json
{
  "recommendation_id": 1,
  "executed_price": 150.0,
  "actual_occupancy": 78.0,
  "actual_revenue": 11700.0,
  "feedback_note": "Demo feedback"
}
```

## 定价逻辑

核心公式位于 `app/core/pricing.py`：

```python
comp_index = mean(competitor_prices)
competitor_gap = (comp_index - base_price) / base_price
occupancy_gap = (occupancy - 70) / 100
demand_score = 0.6 * competitor_gap + 0.4 * occupancy_gap
rule_price = base_price * (1 + demand_score)
final_price = clip(rule_price * (1 + learning_adjustment), min_price, max_price)
```

说明：

- `comp_index` 是 5 公里内竞品酒店最新价格的平均值。
- `competitor_gap` 表示竞品均价相对本酒店基础价格的差异。
- `occupancy_gap` 以 70% 入住率作为中性点。
- 入住率高于 70% 时，推荐价倾向上调。
- 入住率低于 70% 时，推荐价更保守。
- `learning_adjustment` 来自最近反馈，强反馈小幅上调，弱反馈小幅下调。
- 最终价格会被限制在最低价格和最高价格之间。

## 代码结构

```text
app/
  main.py                    FastAPI 应用入口
  api/
    home.py                  首页和健康检查
    hotels.py                酒店、经营指标、价格约束接口
    pricing.py               价格预测和推荐记录接口
    competitors.py           竞品酒店和竞品价格接口
    feedback.py              反馈接口
    demo.py                  演示闭环接口
    routes.py                API 路由聚合
  core/
    pricing.py               定价公式
  dashboard/
    streamlit_app.py         Streamlit 演示看板
  db/
    lifecycle.py             建表、初始化、重置和种子写入
    hotels.py                酒店读取和定价输入查询
    competitors.py           竞品酒店和竞品价格写入查询
    metrics.py               每日经营指标写入查询
    constraints.py           价格约束写入
    recommendations.py       推荐记录写入查询
    feedback.py              反馈记录写入查询
    serializers.py           ORM 对象转 dict
    database.py              兼容旧导入的数据库聚合层
    model.py                 SQLAlchemy ORM 模型
    seed.py                  示例数据生成
    session.py               SQLite 连接和会话
  schemas/
    hotels.py                酒店定价输入模型
    metrics.py               每日经营指标模型
    constraints.py           价格约束模型
    competitors.py           竞品酒店和价格快照模型
    recommendations.py       推荐价格和推荐记录模型
    feedback.py              反馈模型
    demo.py                  演示闭环模型
    pricing.py               兼容旧导入的模型聚合层
  services/
    hotels.py                酒店、经营指标和价格约束服务
    recommendations.py       定价推荐服务
    competitors.py           竞品酒店和竞品价格服务
    feedback.py              反馈记录服务
    learning.py              学习调整逻辑
    demo.py                  演示闭环服务
    pricing_service.py       兼容旧导入的服务聚合层
scripts/
  init_db.py                 初始化或重置数据库
  run_demo.py                同时启动 API 和 Streamlit
tests/
  test_api.py                API 测试
  test_learning.py           学习调整测试
  test_pricing.py            定价公式测试
```

## 数据库

默认 SQLite 文件：

```text
app/db/hotel_pricing.db
```

重置数据库：

```bash
python scripts/init_db.py --reset
```

运行 demo 时使用 `--reset-db` 也会重置数据库：

```bash
python scripts/run_demo.py --reset-db --open
```

## 说明

这是一个 MVP 演示项目，不是生产级收益管理系统。当前模型刻意保持透明和可解释，便于观察输入数据、推荐价格、反馈学习之间的关系。
