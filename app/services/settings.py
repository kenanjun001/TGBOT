#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置服务
"""

from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SystemSetting, QuickReply


class SettingsService:
    """设置服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_setting(self, key: str) -> Optional[str]:
        """获取设置值"""
        result = await self.session.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None
    
    async def set_setting(self, key: str, value: str):
        """设置值"""
        result = await self.session.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            self.session.add(setting)
        
        await self.session.flush()
    
    async def get_all_settings(self) -> Dict[str, str]:
        """获取所有设置"""
        result = await self.session.execute(select(SystemSetting))
        settings = result.scalars().all()
        return {s.key: s.value for s in settings}
    
    async def delete_setting(self, key: str) -> bool:
        """删除设置"""
        result = await self.session.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting:
            await self.session.delete(setting)
            await self.session.flush()
            return True
        return False
    
    # 快捷回复管理
    async def get_quick_replies(self):
        """获取所有快捷回复"""
        result = await self.session.execute(
            select(QuickReply).order_by(QuickReply.sort_order)
        )
        return result.scalars().all()
    
    async def add_quick_reply(self, title: str, content: str) -> QuickReply:
        """添加快捷回复"""
        reply = QuickReply(title=title, content=content)
        self.session.add(reply)
        await self.session.flush()
        return reply
    
    async def update_quick_reply(
        self,
        reply_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[QuickReply]:
        """更新快捷回复"""
        result = await self.session.execute(
            select(QuickReply).where(QuickReply.id == reply_id)
        )
        reply = result.scalar_one_or_none()
        
        if reply:
            if title is not None:
                reply.title = title
            if content is not None:
                reply.content = content
            await self.session.flush()
        
        return reply
    
    async def delete_quick_reply(self, reply_id: int) -> bool:
        """删除快捷回复"""
        result = await self.session.execute(
            select(QuickReply).where(QuickReply.id == reply_id)
        )
        reply = result.scalar_one_or_none()
        
        if reply:
            await self.session.delete(reply)
            await self.session.flush()
            return True
        return False
