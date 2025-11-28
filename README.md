# TG 客服机器人 | Telegram Customer Service Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Aiogram-3.0+-blue.svg" alt="Aiogram">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Docker-Ready-brightgreen.svg" alt="Docker">
</p>

<p align="center">
  <b>🤖 一款功能强大的 Telegram 客服系统，支持 Web 客服页面，让客户无需 Telegram 也能联系您</b>
</p>

<p align="center">
  <a href="#-功能特性">功能特性</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-使用教程">使用教程</a> •
  <a href="#-配置说明">配置说明</a> •
  <a href="#-常见问题">常见问题</a>
</p>

---

## ✨ 功能特性

### 🎯 核心功能

| 功能 | 描述 |
|------|------|
| **双入口客服** | Telegram 机器人 + Web 客服页面，客户可自由选择 |
| **多管理员** | 支持多个客服同时在线，消息同步推送，显示回复客服名称 |
| **人机验证** | 防止垃圾消息，支持算术题/按钮验证 |
| **实时对话** | Web 管理后台实时显示消息，无需刷新 |
| **消息记录** | 完整保存所有对话历史，支持搜索导出 |
| **客户评分** | 客户可结束会话并评分，便于服务质量统计 |

### 🛡️ 安全功能

- ✅ 敏感词过滤（警告/拦截两种模式）
- ✅ 用户黑名单/白名单管理
- ✅ 验证失败自动临时封禁
- ✅ 操作日志完整记录
- ✅ 自动过滤机器人命令

### 📊 数据统计

- 📈 每日消息统计图表
- 👥 用户增长趋势
- 📉 验证成功率分析
- 🔍 消息搜索与导出

### 🎨 用户体验

- 🌐 Web 客服页面（客户无需安装 Telegram）
- 💬 类微信/WhatsApp 的对话界面
- 📱 完美支持移动端
- 🌙 静音时段设置
- ⚡ 快捷回复模板

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端入口                            │
├─────────────────────────────┬───────────────────────────────┤
│      Telegram 机器人         │        Web 客服页面           │
│    (用户直接发送消息)         │    (输入邮箱开始对话)          │
└─────────────┬───────────────┴───────────────┬───────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      客服系统后台                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  消息处理   │  │  用户管理   │  │  数据统计   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  敏感词过滤 │  │  人机验证   │  │  日志记录   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│    客服小王 (Telegram)   │     │    客服小李 (Telegram)   │
│   收到消息推送，直接回复  │     │   收到消息推送，直接回复  │
└─────────────────────────┘     └─────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- 一台有公网 IP 的服务器
- Telegram Bot Token（从 [@BotFather](https://t.me/BotFather) 获取）

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/kenanjun001/TGBOT.git
cd TGBOT

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 按提示输入配置信息
```

### 手动部署

```bash
# 1. 克隆项目
git clone https://github.com/kenanjun001/TGBOT.git
cd TGBOT

# 2. 创建配置文件
cp .env.example .env

# 3. 编辑配置
nano .env

# 4. 启动服务
docker compose up -d --build

# 5. 查看日志
docker compose logs -f
```

---

## 📖 使用教程

### 1️⃣ 获取 Telegram Bot Token

1. 打开 Telegram，搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. 获取 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2️⃣ 获取管理员 ID

1. 打开 Telegram，搜索 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息，获取你的用户 ID
3. 多个管理员用逗号分隔：`123456789,987654321`

### 3️⃣ 配置系统

编辑 `.env` 文件：

```env
# 机器人配置
BOT_TOKEN=你的Bot Token
ADMIN_IDS=管理员ID1,管理员ID2

# Web 管理后台
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_ADMIN_USERNAME=admin
WEB_ADMIN_PASSWORD=your_secure_password

# 验证设置
VERIFICATION_TYPE=button  # button 或 math
VERIFICATION_TIMEOUT=60
MAX_VERIFICATION_FAILS=3
```

### 4️⃣ 访问管理后台

- 管理后台：`http://你的服务器IP:8080`
- Web 客服页面：`http://你的服务器IP:8080/chat`

### 5️⃣ 客服回复方式

| 消息来源 | 回复方式 |
|---------|---------|
| TG 用户 | 直接回复转发的消息 |
| Web 用户 | 直接回复转发的消息 |

所有消息都可以直接在 Telegram 中右键回复，无需使用命令！

### 6️⃣ 管理员命令

| 命令 | 说明 |
|------|------|
| `/start` | 开始使用 |
| `/help` | 查看帮助 |
| `/stats` | 查看今日统计 |
| `/block <用户ID>` | 拉黑用户 |
| `/unblock <用户ID>` | 解除拉黑 |
| `/whitelist <用户ID>` | 添加白名单 |

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `BOT_TOKEN` | Telegram Bot Token | 必填 |
| `ADMIN_IDS` | 管理员 ID（逗号分隔） | 必填 |
| `SECRET_KEY` | 会话密钥 | 随机生成 |
| `DB_TYPE` | 数据库类型 | sqlite |
| `WEB_PORT` | Web 端口 | 8080 |
| `WEB_ADMIN_USERNAME` | 后台用户名 | admin |
| `WEB_ADMIN_PASSWORD` | 后台密码 | admin |

### 数据库配置

默认使用 SQLite，也支持 MySQL 和 PostgreSQL：

<details>
<summary>MySQL 配置</summary>

```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=tg_bot
```

使用 MySQL：
```bash
docker compose -f docker-compose.mysql.yml up -d
```

</details>

<details>
<summary>PostgreSQL 配置</summary>

```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DATABASE=tg_bot
```

使用 PostgreSQL：
```bash
docker compose -f docker-compose.postgres.yml up -d
```

</details>

---

## 🔧 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 更新版本
docker compose down
git pull
docker compose up -d --build

# 备份数据
cp -r data/ data_backup_$(date +%Y%m%d)/
```

---

## ❓ 常见问题

<details>
<summary><b>Q: 如何添加客服人员？</b></summary>

在 Web 管理后台 → 设置 → 管理员管理 中添加，输入客服的 Telegram ID 和备注名即可。

</details>

<details>
<summary><b>Q: 如何修改机器人 Token？</b></summary>

在 Web 管理后台 → 设置 → 机器人设置 中可以直接修改 Token 并重启。

</details>

<details>
<summary><b>Q: 如何使用 HTTPS？</b></summary>

推荐使用 Nginx 反向代理 + Let's Encrypt：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

</details>

<details>
<summary><b>Q: Web 客服页面可以嵌入到其他网站吗？</b></summary>

可以使用 iframe 嵌入：

```html
<iframe src="https://your-domain.com/chat" width="400" height="600"></iframe>
```

</details>

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/kenanjun001">kenanjun001</a>
</p>
