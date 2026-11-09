# Design: 个人服务器运维仪表盘 (ops-dashboard)

## Overview

单体 Python 服务：FastAPI 提供 JSON API 与静态页面，SQLite 存数据，
后台用 APScheduler（或线程 + sleep 的极简调度器）每 15 分钟跑健康检查。
探活用标准库（socket + ssl + urllib），不依赖外部探活服务。
整个应用一个进程、一个 SQLite 文件、一个端口，评委一条命令能跑起来。

## Architecture

```
浏览器 ── HTTP ──► FastAPI (app.py)
                     ├─ /            仪表盘静态页 (static/index.html)
                     ├─ /api/hosts   机器 CRUD + 状态
                     ├─ /api/deploys 部署记录 CRUD
                     ├─ /api/checks  检查历史 + 一键跑测试
                     └─ /healthz     探活
                          │
                          ▼
                   SQLite (ops.db)
                          ▲
                   调度器线程：每 15 分钟
                   对每台机器做 HTTP 探活 + 证书检查，
                   结果写入 checks 表
```

### 拼合点（Frankenstein）

- Python 后端（FastAPI）+ 原生前端（HTML/JS，无构建）
- Shell 探针逻辑（socket/ssl）+ Python 调度
- SQLite 存档 + 定时任务
- 全部由 Kiro spec（requirements → design → tasks）驱动开发

## Components

### 1. hosts 表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | 自增 |
| name | TEXT | 显示名，如 tv.ztech.eu.cc |
| address | TEXT | 探活地址，如 https://tv.ztech.eu.cc |
| kind | TEXT | server / domain / node |
| status | TEXT | online / offline / unknown |
| last_latency_ms | INTEGER | 最近一次延迟 |
| last_seen_at | TEXT | 最近一次在线时间（ISO） |
| cert_expires_at | TEXT | 证书到期日（ISO），无证书为空 |
| created_at | TEXT | 登记时间 |

### 2. deploys 表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | 自增 |
| host_id | INTEGER FK | 目标机器 |
| summary | TEXT | 部署内容一句话 |
| actor | TEXT | 执行人 |
| result | TEXT | success / failed |
| created_at | TEXT | 时间 |

### 3. checks 表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | 自增 |
| host_id | INTEGER FK | 目标机器 |
| ok | INTEGER | 1 通过 / 0 失败 |
| latency_ms | INTEGER | 延迟 |
| detail | TEXT | 失败原因或证书剩余天数 |
| checked_at | TEXT | 时间 |

### 4. 探活器（prober）

- HTTP 探活：urllib 发 HEAD/GET，超时 5 秒，记状态码与延迟。
- 证书检查：ssl.get_server_certificate + 解析 notAfter，算剩余天数；失败记 unknown。
- 连续 2 次失败才标离线，避免单次抖动误报。

### 5. 前端

- 一个 static/index.html：三块——机器状态表（含证书倒计时）、部署记录（表单 + 历史）、
  检查历史（一键跑测试按钮 + 最近 20 条结果）。
- 每 30 秒自动刷新状态；不用任何前端框架。

## Testing

- 单元测试（pytest）：探活器对本地回环地址的成功/失败判定、证书天数计算、离线阈值逻辑。
- 接口测试：FastAPI TestClient 覆盖 hosts/deploys/checks 的增查与 /healthz。
- 手工验收：启动服务，登记一台真实域名与一台本地地址，跑一遍一键测试，确认页面三块都出数。
