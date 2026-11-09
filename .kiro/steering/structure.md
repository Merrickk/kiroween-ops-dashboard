# Structure

```
app.py            FastAPI 应用：路由 + 调度器线程（每 15 分钟全量检查）
prober.py         探活器：HTTP 探活 + TLS 证书到期检查（标准库）
store.py          SQLite 存取：hosts / deploys / checks 三张表
static/index.html 仪表盘页面：机器表、部署表单与历史、检查历史
tests/            pytest：test_prober.py（探活判定）、test_api.py（接口）
.kiro/specs/ops-dashboard/   Kiro spec：requirements.md / design.md / tasks.md
.kiro/steering/   Kiro steering：product.md / tech.md / structure.md
requirements.txt  fastapi / uvicorn / httpx / pytest
```

数据文件 `ops.db` 由应用自动创建，不提交进仓库。
