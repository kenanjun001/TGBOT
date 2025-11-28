#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器
"""

import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database.models import Base


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def init(self):
        """初始化数据库连接"""
        # 确保 SQLite 目录存在
        if settings.DB_TYPE == "sqlite":
            os.makedirs(os.path.dirname(settings.SQLITE_PATH), exist_ok=True)
        
        # 创建引擎
        self.engine = create_async_engine(
            settings.database_url,
            echo=settings.DEBUG,
            poolclass=NullPool if settings.DB_TYPE == "sqlite" else None,
        )
        
        # 创建会话工厂
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 创建表
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_db():
    """初始化数据库"""
    db_manager = get_db_manager()
    await db_manager.init()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于依赖注入）"""
    db_manager = get_db_manager()
    async for session in db_manager.get_session():
        yield session
