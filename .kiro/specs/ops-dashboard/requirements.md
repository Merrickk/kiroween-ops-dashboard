# Requirements: 个人服务器运维仪表盘 (ops-dashboard)

## Introduction

为 Kiroween 2026（Frankenstein 分类）新建的作品：把“仪表盘 + 服务器部署管理 + 自动化测试”拼成一个应用。
用户有多台服务器/节点（Cloady、GCP、ASCS、Instabox 等），需要一个自己用得上的运维一览工具：
一眼看到每台机器在不在线、证书几天到期、最近一次部署是什么时候、定时健康检查有没有报警。

本 spec 是 Kiro spec-driven 开发的需求文档。实现语言：Python 3.11+（标准库 + FastAPI + SQLite），
前端为同一服务托管的静态页面（HTML + 少量 JS，无构建步骤），部署时一条命令跑起来。

## Requirements

### Requirement 1: 机器状态一览

**User Story:** As a 用户，I want 在一个页面看到所有机器的在线状态，so that 不用逐台去登录检查。

#### Acceptance Criteria

1. WHEN 打开仪表盘首页，THE System SHALL 列出全部已登记机器，每台显示名称、主机地址、最后一次探活时间与在线/离线状态。
2. WHEN 一台机器连续 2 次探活失败，THE System SHALL 把它标为离线并记录一次离线事件。
3. WHEN 探活成功，THE System SHALL 更新该机器的最后在线时间与延迟毫秒数。

### Requirement 2: 证书到期倒计时

**User Story:** As a 用户，I want 看到每个域名证书还剩几天过期，so that 不会像 tv.ztech.eu.cc 那样到跟前才想起来。

#### Acceptance Criteria

1. WHEN 仪表盘加载，THE System SHALL 对每个已登记域名显示证书到期日期与剩余天数。
2. WHEN 某证书剩余天数 <= 14 天，THE System SHALL 用醒目样式标出。
3. WHEN 证书无法获取（域名不通或无证书），THE System SHALL 显示“未知”而不是报错崩掉页面。

### Requirement 3: 部署记录

**User Story:** As a 用户，I want 每次部署都留一条记录，so that 出问题能回头查是谁、什么时候、部署了什么。

#### Acceptance Criteria

1. WHEN 用户提交一次部署，THE System SHALL 记录目标机器、部署内容、执行人、时间与结果（成功/失败）。
2. WHEN 查看部署历史，THE System SHALL 按时间倒序列出全部记录。
3. THE System SHALL 只记录部署动作本身，不在演示里执行任何代理节点部署。

### Requirement 4: 定时健康检查与测试结果存档

**User Story:** As a 用户，I want 定时健康检查自动跑、结果存下来，so that 半夜出问题第二天能看到。

#### Acceptance Criteria

1. THE System SHALL 每 15 分钟自动对全部机器跑一次健康检查（HTTP 探活 + 证书检查）。
2. WHEN 检查完成，THE System SHALL 把每台机器的结果写入检查历史表。
3. WHEN 用户点“一键跑测试”，THE System SHALL 立即跑一遍检查套件并在页面显示逐项通过/失败。

### Requirement 5: 一条命令跑起来

**User Story:** As a 评委，I want 不用配数据库、不用编译前端就能把演示跑起来，so that 能在 3 分钟内看到它工作。

#### Acceptance Criteria

1. WHEN 在干净环境执行 `pip install -r requirements.txt && python app.py`，THE System SHALL 在 8000 端口提供服务，无需额外配置。
2. THE System SHALL 使用 SQLite 文件数据库，首次启动自动建表。
3. THE System SHALL 提供 `/healthz` 接口返回 `{"status": "ok"}` 供部署平台探活。
