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

## 📸 界面预览

<details>
<summary>点击展开截图</summary>

### 管理后台仪表盘
![Dashboard](docs/images/dashboard.png)

### 对话界面
![Chat](docs/images/chat.png)

### Web 客服页面
![Web Chat](docs/images/web-chat.png)

</details>

---

## ✨ 功能特性

### 🎯 核心功能

| 功能 | 描述 |
|------|------|
| **双入口客服** | Telegram 机器人 + Web 客服页面，客户可自由选择 |
| **多管理员** | 支持多个管理员同时在线，消息同步推送 |
| **人机验证** | 防止垃圾消息，支持算术题/按钮验证 |
| **实时对话** | Web 管理后台实时显示消息，无需刷新 |
| **消息记录** | 完整保存所有对话历史，支持搜索导出 |

### 🛡️ 安全功能

- ✅ 敏感词过滤（警告/拦截两种模式）
- ✅ 用户黑名单/白名单管理
- ✅ 验证失败自动临时封禁
- ✅ 操作日志完整记录

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
│      管理员 A (TG)       │     │      管理员 B (TG)       │
│   收到消息推送，可回复    │     │   收到消息推送，可回复    │
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
git clone https://github.com/yourusername/tg-relay-bot.git
cd tg-relay-bot

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 按提示输入配置信息
```

### 手动部署

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/tg-relay-bot.git
cd tg-relay-bot

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

### 5️⃣ 管理员命令

在 Telegram 中可使用以下命令：

| 命令 | 说明 |
|------|------|
| `/start` | 开始使用 |
| `/help` | 查看帮助 |
| `/stats` | 查看今日统计 |
| `/r <用户ID> <消息>` | 回复用户（支持 TG 和 Web 用户） |
| `/block <用户ID>` | 拉黑用户 |
| `/unblock <用户ID>` | 解除拉黑 |
| `/whitelist <用户ID>` | 添加白名单 |
| `/broadcast <消息>` | 群发消息 |

**回复消息的两种方式：**

- **TG 用户**：直接回复转发的消息
- **Web 用户**：使用 `/r <ID> <消息>` 命令

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
| `VERIFICATION_TYPE` | 验证类型 | button |
| `VERIFICATION_TIMEOUT` | 验证超时(秒) | 60 |
| `MAX_VERIFICATION_FAILS` | 最大失败次数 | 3 |
| `TEMP_BAN_DURATION` | 临时封禁时长(秒) | 3600 |
| `ENABLE_QUIET_HOURS` | 启用静音时段 | false |
| `QUIET_HOURS_START` | 静音开始时间 | 23 |
| `QUIET_HOURS_END` | 静音结束时间 | 7 |

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

使用 MySQL 的 docker-compose：
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

使用 PostgreSQL 的 docker-compose：
```bash
docker compose -f docker-compose.postgres.yml up -d
```

</details>

---

## 🌟 功能亮点

### 对比其他方案

| 功能 | 本项目 | LiveChat | Crisp | Tawk.to |
|------|:------:|:--------:|:-----:|:-------:|
| 免费使用 | ✅ | ❌ | 部分 | ✅ |
| 自托管 | ✅ | ❌ | ❌ | ❌ |
| Telegram 集成 | ✅ | ❌ | 插件 | ❌ |
| Web 客服页面 | ✅ | ✅ | ✅ | ✅ |
| 多管理员 | ✅ | 付费 | 付费 | ✅ |
| 人机验证 | ✅ | ❌ | ❌ | ❌ |
| 敏感词过滤 | ✅ | ❌ | ❌ | ❌ |
| 数据完全掌控 | ✅ | ❌ | ❌ | ❌ |
| 中文支持 | ✅ | 部分 | 部分 | 部分 |

### 为什么选择我们？

1. **🆓 完全免费开源** - 无任何隐藏费用
2. **🔒 数据自主可控** - 所有数据存储在您自己的服务器
3. **📱 Telegram 原生体验** - 管理员在 TG 中即可回复
4. **🌐 无需安装** - 客户通过网页即可联系您
5. **⚡ 轻量高效** - Docker 一键部署，资源占用低
6. **🛡️ 安全可靠** - 人机验证 + 敏感词过滤

---

## 📁 项目结构

```
tg-relay-bot/
├── app/
│   ├── bot/                 # Telegram 机器人
│   │   ├── handlers.py      # 消息处理器
│   │   ├── verification.py  # 人机验证
│   │   └── middlewares.py   # 中间件
│   ├── web/                 # Web 管理后台
│   │   ├── routes/          # API 路由
│   │   ├── templates/       # 页面模板
│   │   └── static/          # 静态资源
│   ├── services/            # 业务服务
│   ├── database/            # 数据库模型
│   ├── config.py            # 配置管理
│   └── main.py              # 主入口
├── docker-compose.yml       # Docker 配置
├── Dockerfile               # Docker 镜像
├── requirements.txt         # Python 依赖
├── install.sh               # 安装脚本
└── .env.example             # 配置示例
```

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

# 重新构建
docker compose up -d --build

# 备份数据
cp -r data/ data_backup_$(date +%Y%m%d)/
```

---

## ❓ 常见问题

<details>
<summary><b>Q: 如何修改管理员？</b></summary>

方法一：在 Web 管理后台 → 设置 → 管理员管理 中添加/删除

方法二：修改 `.env` 文件中的 `ADMIN_IDS`，然后重启服务

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
<summary><b>Q: 如何备份数据？</b></summary>

SQLite 数据存储在 `data/` 目录，直接备份该目录即可：

```bash
cp -r data/ backup/
```

</details>

<details>
<summary><b>Q: Web 客服页面可以嵌入到其他网站吗？</b></summary>

可以使用 iframe 嵌入：

```html
<iframe src="http://your-server:8080/chat" width="400" height="600"></iframe>
```

</details>

<details>
<summary><b>Q: 如何查看用户的 ID？</b></summary>

在 Web 管理后台 → 用户管理 中可以看到每个用户的 ID

Web 客服消息推送时也会显示用户 ID：`[ID:123]`

</details>

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## ⭐ Star History

如果这个项目对您有帮助，请给一个 Star ⭐

---

<p align="center">
  Made with ❤️ 
</p>
