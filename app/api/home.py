from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def api_home() -> str:
    return """
    <!doctype html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Hotel Dynamic Pricing MVP</title>
        <style>
          body {
            margin: 0;
            font-family: Arial, "Microsoft YaHei", sans-serif;
            color: #1f2937;
            background: #f8fafc;
          }
          main {
            max-width: 960px;
            margin: 0 auto;
            padding: 48px 24px;
          }
          h1 {
            margin: 0 0 12px;
            font-size: 32px;
          }
          p {
            line-height: 1.7;
            color: #4b5563;
          }
          .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-top: 28px;
          }
          .card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 18px;
            background: #ffffff;
          }
          a {
            color: #0f766e;
            font-weight: 700;
            text-decoration: none;
          }
          code {
            background: #eef2f7;
            border-radius: 4px;
            padding: 2px 6px;
          }
        </style>
      </head>
      <body>
        <main>
          <h1>Hotel Dynamic Pricing MVP</h1>
          <p>
            酒店收益管理后端已启动。系统支持 5 公里内竞品酒店价格快照、
            每日经营数据录入、价格约束更新、动态定价建议和反馈学习闭环。
          </p>
          <section class="grid">
            <div class="card">
              <h2>API 文档</h2>
              <p>查看并调试所有接口。</p>
              <a href="/docs">打开 Swagger UI</a>
            </div>
            <div class="card">
              <h2>健康检查</h2>
              <p>确认服务是否正常运行。</p>
              <a href="/health">GET /health</a>
            </div>
            <div class="card">
              <h2>酒店数据</h2>
              <p>查看初始化生成的酒店定价输入。</p>
              <a href="/hotels">GET /hotels</a>
            </div>
            <div class="card">
              <h2>演示看板</h2>
              <p>本地运行 Streamlit 后访问。</p>
              <a href="http://127.0.0.1:8501">http://127.0.0.1:8501</a>
            </div>
          </section>
          <p>
            常用流程：<code>GET /hotels</code> 选择酒店，
            <code>POST /predict-price</code> 生成推荐，
            <code>POST /pricing-feedback</code> 写入执行反馈。
          </p>
        </main>
      </body>
    </html>
    """


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
