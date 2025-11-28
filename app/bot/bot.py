#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 机器人核心
"""

import logging
from aiogram import Bot, Dispatcher, Router

from app.config import settings
from app.bot.handlers import setup_handlers
from app.bot.middlewares import setup_middlewares

logger = logging.getLogger(__name__)

# 全局机器人实例
_bot: Bot = None
_dp: Dispatcher = None


async def create_bot() -> Bot:
    """创建机器人实例"""
    global _bot, _dp
    
    if not settings.BOT_TOKEN:
        raise ValueError("请配置 BOT_TOKEN")
    
    _bot = Bot(
        token=settings.BOT_TOKEN,
        parse_mode="HTML"
    )
    
    _dp = Dispatcher()
    
    # 设置中间件
    setup_middlewares(_dp)
    
    # 设置处理器
    setup_handlers(_dp)
    
    return _bot


async def start_bot(bot: Bot):
    """启动机器人"""
    global _dp
    
    try:
        logger.info("机器人开始轮询...")
        await _dp.start_polling(bot)
    except Exception as e:
        logger.error(f"机器人运行出错: {e}")
        raise


async def stop_bot(bot: Bot):
    """停止机器人"""
    global _dp
    
    if _dp:
        await _dp.stop_polling()
    if bot:
        await bot.session.close()


def get_bot() -> Bot:
    """获取机器人实例"""
    global _bot
    return _bot


def get_dispatcher() -> Dispatcher:
    """获取调度器实例"""
    global _dp
    return _dp


async def restart_bot(new_token: str = None):
    """重启机器人（使用新Token）"""
    global _bot, _dp
    
    try:
        # 停止当前机器人
        if _dp:
            await _dp.stop_polling()
        if _bot:
            await _bot.session.close()
        
        # 如果提供新Token，更新配置
        if new_token:
            settings.BOT_TOKEN = new_token
        
        # 创建新机器人
        _bot = Bot(
            token=settings.BOT_TOKEN,
            parse_mode="HTML"
        )
        
        _dp = Dispatcher()
        setup_middlewares(_dp)
        setup_handlers(_dp)
        
        # 启动新机器人（在后台任务中）
        import asyncio
        asyncio.create_task(_dp.start_polling(_bot))
        
        logger.info("机器人已重启")
        return True
        
    except Exception as e:
        logger.error(f"重启机器人失败: {e}")
        raise
