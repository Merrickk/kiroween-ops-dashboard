# 在 Oracle AMD-2（Debian 13）上部署 Ops Dashboard

这台机出站 80 端口被安全列表静默丢弃，https（443）全通，所以 pip 走 https 没问题。
入站 22 已关，走 Cloudflare Tunnel 访问；部署本身在机器上直接操作。

## 步骤（机器上执行，一条命令一行）

```bash
sudo apt-get update && sudo apt-get install -y python3-venv git
```

```bash
sudo mkdir -p /opt/ops-dashboard && sudo chown ubuntu:ubuntu /opt/ops-dashboard
```

```bash
git clone https://github.com/Merrickk/kiroween-ops-dashboard.git /opt/ops-dashboard
```

```bash
python3 -m venv /opt/ops-dashboard/.venv && /opt/ops-dashboard/.venv/bin/pip install -r /opt/ops-dashboard/requirements.txt
```

```bash
sudo cp /opt/ops-dashboard/deploy/ops-dashboard.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now ops-dashboard
```

```bash
curl -s http://127.0.0.1:8000/healthz
```

## 对外发布

在 Cloudflare Zero Trust 后台给已有隧道加一条 Public Hostname，
指向 `http://localhost:8000`，域名例如 `ops.<你的域名>`。
加完后公开地址就是 `https://ops.<你的域名>`，评委直接打开就能看。

## 查看日志

```bash
sudo journalctl -u ops-dashboard -f
```
