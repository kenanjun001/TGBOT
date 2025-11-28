#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TG 传话机器人 - 主入口
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from app.config import settings
from app.database import init_db, get_db_manager
from app.bot import create_bot, start_bot, stop_bot
from app.web.routes import auth, dashboard, users, messages, settings as settings_routes, api, chat
from app.web.routes import websocket as ws_routes
from app.services.admin import AdminService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在初始化数据库...")
    await init_db()
    
    # 初始化管理员
    logger.info("正在初始化管理员...")
    db_manager = get_db_manager()
    async with db_manager.async_session() as session:
        admin_service = AdminService(session)
        await admin_service.init_admins_from_config(settings.admin_id_list)
        await session.commit()
    
    logger.info("正在启动 Telegram 机器人...")
    bot = await create_bot()
    app.state.bot = bot
    asyncio.create_task(start_bot(bot))
    
    logger.info("服务启动完成")
    yield
    
    # 关闭时
    logger.info("正在停止服务...")
    await stop_bot(app.state.bot)
    logger.info("服务已停止")


# 创建 FastAPI 应用
app = FastAPI(
    title="TG 传话机器人",
    description="带人机验证的 Telegram 传话机器人管理系统",
    version="1.0.0",
    lifespan=lifespan
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# 注册路由
app.include_router(auth.router, prefix="", tags=["认证"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
app.include_router(users.router, prefix="/users", tags=["用户管理"])
app.include_router(messages.router, prefix="/messages", tags=["消息管理"])
app.include_router(settings_routes.router, prefix="/settings", tags=["设置"])
app.include_router(api.router, prefix="/api", tags=["API"])
app.include_router(chat.router, prefix="/chat", tags=["客服聊天"])
app.include_router(ws_routes.router, prefix="/ws", tags=["WebSocket"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        reload=settings.DEBUG
    )
