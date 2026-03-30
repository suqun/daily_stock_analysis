# 🚀 绿联 NAS Docker 部署指南

本文档介绍如何将 A股自选股智能分析系统部署到绿联 NAS（如 DXP4800 PLUS）。

---

## 📋 目录结构

```
/volume1/docker/stock/
├── daily_stock_analysis/   # 项目代码（从 Gitee/GitHub 拉取）
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   └── Dockerfile
│   ├── .env                # 环境配置
│   └── ...
├── data/                   # 数据目录
├── logs/                   # 日志目录
├── reports/                # 报告目录
└── strategies/             # 策略目录
```

---

## 🐳 部署步骤

### 1. 开启 NAS SSH

1. 打开绿联云客户端
2. 设置 → 终端安全 → 开启 SSH

### 2. SSH 登录 NAS

```bash
ssh admin@<NAS_IP>
# 例如：ssh admin@192.168.1.100
```

### 3. 安装必要工具（如需要）

```bash
# 安装 git（如已安装可跳过）
sudo apt-get update
sudo apt-get install -y git
```

### 4. 配置 Docker 镜像加速

```bash
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "data-root": "/volume1/@docker",
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
docker info | grep -A5 "Registry Mirrors"
```

### 5. 拉取代码

```bash
# 创建目录
mkdir -p /volume1/docker/stock

# 拉取代码（替换为你的 Gitee/GitHub 地址）
cd /volume1/docker/stock
git clone -b dev https://gitee.com/<你的用户名>/daily_stock_analysis.git daily_stock_analysis
```

### 6. 配置环境变量

```bash
cd /volume1/docker/stock/daily_stock_analysis

# 复制配置模板
cp .env.example .env

# 编辑配置（填入你的 API Key、股票列表等）
nano .env
```

**必须配置项：**
- `STOCK_LIST` - 自选股列表，如 `600519,300750`
- LLM 相关配置（DeepSeek/Gemini/AIHubMix 等）
- 通知渠道配置（可选）

### 7. 创建必要目录

```bash
cd /volume1/docker/stock
mkdir -p data logs reports strategies data/zsxq
```

### 8. 启动服务

```bash
cd /volume1/docker/stock
docker compose -f daily_stock_analysis/docker/docker-compose.yml up -d --build
```

---

## 📦 服务说明

| 服务 | 容器名 | 端口 | 功能 |
|------|--------|------|------|
| server | stock-server | 8080 | Web API + 定时分析 |
| zsxq | stock-zsxq | - | 知识星球会员同步 |

---

## 🤖 QQ 机器人部署（NapCat）

由于 OpenClaw 已停止维护，QQ 机器人需要使用 **NapCat** 单独部署。

### 方案一：使用 NapCat Docker（推荐）

#### 1. 拉取 NapCat 镜像

```bash
# 如果无法直接拉取，需要配置镜像加速或手动导入
docker pull aoscccc/napcat-docker:latest
```

#### 2. 创建配置目录

```bash
mkdir -p /volume1/docker/napcat/{data,logs,config}
```

#### 3. 创建启动脚本

```bash
cd /volume1/docker/napcat

cat > start.sh << 'EOF'
#!/bin/bash
docker run -d \
  --name napcat \
  --restart unless-stopped \
  -p 18789:18789 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e QQ=你的QQ号 \
  -e NAPCAT_MODE=QLOCAL \
  aoscccc/napcat-docker:latest
EOF

chmod +x start.sh
./start.sh
```

#### 4. 配置 NapCat

1. 浏览器访问：`http://<NAS_IP>:18789`
2. 扫描二维码登录 QQ
3. 配置 Webhook：
   - 启用 Webhook
   - Webhook 地址：`http://stock-server:8000/qq/webhook`
   - （如果在同一 docker network 中）

---

### 方案二：手动部署 NapCat

参考官方文档：https://github.com/tencent-connect/NapCat

```bash
# 1. 下载 NapCat
cd /volume1/docker/napcat
wget https://github.com/tencent-connect/NapCat/releases/latest/download/napcat.zip
unzip napcat.zip

# 2. 配置
cp config.example.sh config.sh
nano config.sh  # 修改 QQ 号等配置

# 3. 启动
./start.sh
```

---

### 3. 配置 .env 文件

确保 `.env` 中包含以下配置：

```env
# OpenClaw（旧方式，已废弃）
# QQ_OPENCLAW_URL=http://127.0.0.1:18789
# QQ_OPENCLAW_SECRET=xxx
# QQ_OPENCLAW_TOKEN=xxx

# QQ 机器人官方 API
QQ_BOT_APP_ID=1903695709
QQ_BOT_APP_SECRET=你的APP_SECRET
QQ_BOT_TOKEN=你的BOT_TOKEN
QQ_ADMIN_QQ=你的QQ号
```

---

### 4. NapCat 常用命令

```bash
# 查看日志
docker logs -f napcat

# 重启
docker restart napcat

# 停止
docker stop napcat
```

---

## 🔧 常用管理命令

```bash
cd /volume1/docker/stock

# 启动所有服务
docker compose -f daily_stock_analysis/docker/docker-compose.yml up -d --build

# 启动指定服务
docker compose -f daily_stock_analysis/docker/docker-compose.yml up -d server

# 查看容器状态
docker ps

# 查看所有容器（含已停止）
docker ps -a

# 查看日志
docker logs stock-server        # Web 服务日志
docker logs stock-zsxq         # 知识星球同步日志

# 实时查看日志
docker logs -f stock-server

# 重启服务
docker restart stock-server

# 停止服务
docker compose -f daily_stock_analysis/docker/docker-compose.yml down

# 更新代码后重新部署
cd /volume1/docker/stock/daily_stock_analysis
git pull
cd /volume1/docker/stock
docker compose -f daily_stock_analysis/docker/docker-compose.yml up -d --build
```

---

## 🌐 访问 Web 界面

服务启动后，在浏览器访问：

```
http://<NAS_IP>:8080
```

**注意**：如果无法访问，需要在绿联 NAS 防火墙开放 8080 端口：

1. 绿联云客户端 → 设置 → 防火墙
2. 添加规则 → TCP → 8080

---

## ❓ 常见问题

### 1. Docker 构建失败

**问题**：`failed to resolve source metadata`

**解决**：确保 Docker 镜像加速已配置，重启 Docker 后重试。

```bash
sudo systemctl restart docker
cd /volume1/docker/stock
docker compose -f daily_stock_analysis/docker/docker-compose.yml up -d --build
```

### 2. 拉取镜像超时

**问题**：`request canceled while waiting for connection`

**解决**：
1. 检查网络连接
2. 确认镜像加速配置生效
3. 尝试手动导入镜像（见下文）

### 3. 手动导入镜像（离线安装）

如果网络无法访问 Docker Hub，可以在其他电脑下载镜像后导入：

```bash
# 在有网络的电脑上
docker pull python:3.11-slim-bookworm
docker pull node:22-slim
docker save -o nas-images.tar python:3.11-slim-bookworm node:22-slim

# 复制到 NAS
scp nas-images.tar admin@<NAS_IP>:/tmp/

# 在 NAS 上导入
docker load -i /tmp/nas-images.tar
```

### 4. Web 无法访问

**解决**：
1. 检查容器是否运行：`docker ps`
2. 检查端口是否监听：`netstat -tlnp | grep 8080`
3. 检查防火墙是否开放

---

## 🔄 更新部署

```bash
# SSH 登录
ssh admin@<NAS_IP>

# 进入代码目录，更新代码
cd /volume1/docker/stock/daily_stock_analysis
git pull

# 重新构建并启动
cd /volume1/docker/stock
docker compose -f daily_stock_analysis/docker/docker-compose.yml up -d --build

# 查看日志确认启动成功
docker logs -f stock-server
```

---

## 📁 数据备份

```bash
# 打包数据（排除大文件）
cd /volume1/docker/stock
tar -czvf stock-backup.tar.gz \
  daily_stock_analysis/.env \
  data/ \
  reports/ \
  logs/ \
  strategies/
```

---

## 🗑️ 清理

```bash
# 删除旧镜像（释放空间）
docker image prune -a

# 清理构建缓存
docker builder prune

# 查看磁盘使用
docker system df
```

---

**祝部署顺利！🎉**
