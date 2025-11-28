#!/bin/bash

# TG 传话机器人 - 交互式安装脚本
# ===================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示 Logo
show_logo() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║                                                   ║"
    echo "║       TG 传话机器人 - 安装向导                    ║"
    echo "║                                                   ║"
    echo "║       带人机验证的 Telegram 传话机器人            ║"
    echo "║                                                   ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查 Docker
check_docker() {
    print_info "检查 Docker 环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "未检测到 Docker，请先安装 Docker"
        echo "安装命令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "未检测到 Docker Compose，请先安装"
        exit 1
    fi
    
    print_success "Docker 环境检查通过"
}

# 生成随机密钥
generate_secret_key() {
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1
}

# 主安装流程
main() {
    show_logo
    check_docker
    
    echo ""
    print_info "开始配置..."
    echo ""
    
    echo ""
    echo "=========================================="
    echo "          Telegram 机器人配置            "
    echo "=========================================="
    echo ""
    
    # Bot Token
    read -p "请输入机器人 Token (从 @BotFather 获取): " bot_token
    if [ -z "$bot_token" ]; then
        print_error "Bot Token 不能为空"
        exit 1
    fi
    
    # Admin IDs
    read -p "请输入管理员 Telegram ID (多个用逗号分隔): " admin_ids
    if [ -z "$admin_ids" ]; then
        print_error "管理员 ID 不能为空"
        exit 1
    fi
    
    echo ""
    echo "=========================================="
    echo "            数据库配置                   "
    echo "=========================================="
    echo ""
    
    echo "请选择数据库类型:"
    echo "  1) SQLite (推荐，简单易用，无需额外配置)"
    echo "  2) MySQL"
    echo "  3) PostgreSQL"
    echo ""
    read -p "请输入选项 [1-3] (默认: 1): " db_choice
    
    DB_TYPE="sqlite"
    DB_HOST="localhost"
    DB_PORT="3306"
    DB_NAME="tg_relay_bot"
    DB_USER="root"
    DB_PASSWORD=""
    COMPOSE_FILE="docker-compose.yml"
    
    case $db_choice in
        2)
            DB_TYPE="mysql"
            COMPOSE_FILE="docker-compose.mysql.yml"
            
            read -p "MySQL 主机 (默认: mysql): " db_host
            DB_HOST=${db_host:-mysql}
            
            read -p "MySQL 端口 (默认: 3306): " db_port
            DB_PORT=${db_port:-3306}
            
            read -p "数据库名称 (默认: tg_relay_bot): " db_name
            DB_NAME=${db_name:-tg_relay_bot}
            
            read -p "数据库用户名 (默认: root): " db_user
            DB_USER=${db_user:-root}
            
            read -sp "数据库密码: " db_password
            DB_PASSWORD=$db_password
            echo ""
            ;;
        3)
            DB_TYPE="postgres"
            COMPOSE_FILE="docker-compose.postgres.yml"
            DB_PORT="5432"
            
            read -p "PostgreSQL 主机 (默认: postgres): " db_host
            DB_HOST=${db_host:-postgres}
            
            read -p "PostgreSQL 端口 (默认: 5432): " db_port
            DB_PORT=${db_port:-5432}
            
            read -p "数据库名称 (默认: tg_relay_bot): " db_name
            DB_NAME=${db_name:-tg_relay_bot}
            
            read -p "数据库用户名 (默认: postgres): " db_user
            DB_USER=${db_user:-postgres}
            
            read -sp "数据库密码: " db_password
            DB_PASSWORD=$db_password
            echo ""
            ;;
        *)
            DB_TYPE="sqlite"
            COMPOSE_FILE="docker-compose.yml"
            print_info "使用 SQLite 数据库"
            ;;
    esac
    
    echo ""
    echo "=========================================="
    echo "          Web 管理后台配置               "
    echo "=========================================="
    echo ""
    
    read -p "Web 端口 (默认: 8080): " web_port
    web_port=${web_port:-8080}
    
    read -p "管理员用户名 (默认: admin): " web_user
    web_user=${web_user:-admin}
    
    read -sp "管理员密码 (默认: admin123): " web_pass
    echo ""
    web_pass=${web_pass:-admin123}
    
    # 生成安全密钥
    secret_key=$(generate_secret_key)
    
    # 直接创建 .env 文件
    print_info "正在创建配置文件..."
    
    cat > .env << ENVEOF
DEBUG=false
SECRET_KEY=${secret_key}

BOT_TOKEN=${bot_token}
ADMIN_IDS=${admin_ids}

DB_TYPE=${DB_TYPE}
SQLITE_PATH=data/bot.db
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

WEB_HOST=0.0.0.0
WEB_PORT=${web_port}
WEB_ADMIN_USERNAME=${web_user}
WEB_ADMIN_PASSWORD=${web_pass}

IP_WHITELIST=

VERIFICATION_TYPE=button
VERIFICATION_TIMEOUT=60
MAX_VERIFICATION_FAILS=3
TEMP_BAN_DURATION=3600

ENABLE_QUIET_HOURS=false
QUIET_HOURS_START=23
QUIET_HOURS_END=7

AUTO_REPLY_ENABLED=false
AUTO_REPLY_MESSAGE=您好，我目前不在线，稍后会回复您。
ENVEOF
    
    print_success "配置文件创建完成"
    
    echo ""
    echo "=========================================="
    echo "              启动服务                   "
    echo "=========================================="
    echo ""
    
    print_info "正在构建并启动服务..."
    
    # 创建数据目录
    mkdir -p data
    
    if docker compose version &> /dev/null; then
        docker compose -f $COMPOSE_FILE up -d --build
    else
        docker-compose -f $COMPOSE_FILE up -d --build
    fi
    
    echo ""
    print_success "安装完成！"
    echo ""
    echo "=========================================="
    echo "              访问信息                   "
    echo "=========================================="
    echo ""
    echo -e "  Web 管理后台: ${GREEN}http://localhost:$web_port${NC}"
    echo -e "  用户名: ${GREEN}$web_user${NC}"
    echo -e "  密码: ${GREEN}$web_pass${NC}"
    echo ""
    echo "=========================================="
    echo ""
    print_info "常用命令:"
    echo "  查看日志: docker compose -f $COMPOSE_FILE logs -f"
    echo "  停止服务: docker compose -f $COMPOSE_FILE down"
    echo "  重启服务: docker compose -f $COMPOSE_FILE restart"
    echo ""
}

# 运行主函数
main
