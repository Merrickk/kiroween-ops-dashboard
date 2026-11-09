# Tasks: 个人服务器运维仪表盘 (ops-dashboard)

## Implementation Plan

按 Kiro spec 流程执行：每项做完打勾，跑通测试再往下走。
免费档 50 credits/月，优先把 spec 与核心链路交给 Kiro，重复性修补自己动手。

- [x] 1. 建项目骨架
  - [x] 1.1 初始化仓库结构：app.py、prober.py、store.py（SQLite）、static/index.html、requirements.txt、README
  - [x] 1.2 首次启动自动建表（hosts / deploys / checks），提供 /healthz
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 2. 机器管理与探活
  - [x] 2.1 实现 hosts 的增删查 API 与页面表格
  - [x] 2.2 实现 HTTP 探活（超时 5 秒，记延迟与状态码）
  - [x] 2.3 实现证书到期检查（剩余天数，<=14 天标红，失败记 unknown）
  - [x] 2.4 连续 2 次失败才标离线
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 3. 部署记录
  - [x] 3.1 实现 deploys 的提交与历史列表 API
  - [x] 3.2 页面加部署表单（目标机器、内容、执行人、结果）
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 4. 定时检查与一键测试
  - [x] 4.1 后台线程每 15 分钟跑全量检查，结果写入 checks 表
  - [x] 4.2 实现“一键跑测试”接口与按钮，页面显示逐项通过/失败
  - [x] 4.3 检查历史列表（最近 20 条）
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 5. 测试与验收
  - [x] 5.1 pytest 单元测试：探活判定、证书天数、离线阈值
  - [x] 5.2 TestClient 接口测试：hosts/deploys/checks + /healthz
  - [x] 5.3 本地验收：登记真实域名 + 本地地址，跑通三块功能（2026-11-09 已验：example.com 探活 online、本地死地址失败留 unknown、部署记录写入，PORT 环境变量生效）
  - _Requirements: 全部_

- [ ] 6. 部署与提交材料
  - [ ] 6.1 选定免费演示托管并部署，拿到公开 URL
  - [ ] 6.2 写 README（含运行方法与 Kiro 用法说明）
  - [ ] 6.3 录 3 分钟内演示视频并公开到 YouTube
  - [ ] 6.4 Devpost 存草稿复核，12 月 4 日 Billings 15:00 前提交

- [ ] 7. Vercel serverless 适配（演示托管改走 Vercel）
  - [x] 7.1 api/index.py 转发入口 + vercel.json（includeFiles + rewrites）
  - [x] 7.2 数据库改写 /tmp（VERCEL=1 时），空库自动放演示机器
  - [x] 7.3 serverless 下不启动定时线程，探活改线程池并行
  - [x] 7.4 本地 pytest 全过 + VERCEL=1 模拟验收通过
  - [ ] 7.5 Vercel 上部署并公开访问验证
