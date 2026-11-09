# Tech

- 语言：Python 3.11+，只用标准库做探活（urllib / socket / ssl），不依赖外部探活服务。
- 后端：FastAPI + uvicorn，SQLite 文件数据库（`ops.db`），首次启动自动建表。
- 前端：同一服务托管的静态页面（`static/index.html`），原生 HTML/JS，无构建步骤。
- 测试：pytest；接口测试用 FastAPI TestClient，探活测试用本地回环 HTTP 服务。
- 运行：`pip install -r requirements.txt && python app.py`，服务在 8000 端口，`/healthz` 探活。

## 约定

- 探活失败不抛异常：所有探活函数返回 (ok, latency, detail)，失败是正常结果。
- 离线判定：连续 2 次探活失败才标离线，避免单次抖动误报。
- 证书取不到时显示“未知”，不要让页面报错。
- 不要把真实凭据、API key 写进代码或 spec。
