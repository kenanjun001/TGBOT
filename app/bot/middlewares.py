#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器人中间件
"""

import logging
from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.database import get_db_manager
from app.services.user import UserService
from app.services.stats import StatsService

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """数据库会话中间件"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        db_manager = get_db_manager()
        async with db_manager.async_session() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise


class UserMiddleware(BaseMiddleware):
    """用户信息中间件"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # 获取用户信息
        from_user = None
        if isinstance(event, Message):
            from_user = event.from_user
        elif isinstance(event, CallbackQuery):
            from_user = event.from_user
        
        if from_user:
            session = data.get("session")
            if session:
                user_service = UserService(session)
                user = await user_service.get_or_create_user(
                    tg_id=from_user.id,
                    username=from_user.username,
                    first_name=from_user.first_name,
                    last_name=from_user.last_name
                )
                data["db_user"] = user
        
        return await handler(event, data)


class StatsMiddleware(BaseMiddleware):
    """统计中间件"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        result = await handler(event, data)
        
        # 更新统计
        session = data.get("session")
        from_user = None
        if isinstance(event, Message):
            from_user = event.from_user
        elif isinstance(event, CallbackQuery):
            from_user = event.from_user
            
        if session and from_user:
            stats_service = StatsService(session)
            await stats_service.increment_message_count()
        
        return result


def setup_middlewares(dp: Dispatcher):
    """设置中间件"""
    # 消息中间件
    dp.message.middleware(DatabaseMiddleware())
    dp.message.middleware(UserMiddleware())
    
    # 回调查询中间件
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(UserMiddleware())
