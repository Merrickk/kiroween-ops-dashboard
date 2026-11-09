# Ops Dashboard — Kiroween 2026 (Frankenstein)

个人服务器运维仪表盘：机器探活状态一览、证书到期倒计时、部署记录、定时健康检查 + 一键测试。

Built with [Kiro](https://kiro.dev) using spec-driven development — see
`.kiro/specs/ops-dashboard/` (requirements → design → tasks) and `.kiro/steering/`.

## Quick start

```bash
pip install -r requirements.txt
python app.py
# open http://localhost:8000
```

SQLite 数据库（`ops.db`）首次启动自动建表，无需额外配置。
健康检查每 15 分钟自动跑一次；`/healthz` 返回 `{"status": "ok"}`。

## Tests

```bash
pytest -q
```

## How Kiro was used

- 需求、设计、任务拆解全部写成 Kiro spec（`.kiro/specs/ops-dashboard/`），
  按 requirements → design → tasks 的流程走。
- 实现对照 tasks.md 逐项完成，每项跑通测试再往下走。
- Steering 文档（`.kiro/steering/`）记录技术选型与项目结构约定。
