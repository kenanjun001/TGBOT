#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务
"""

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.settings import SettingsService

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings_service = SettingsService(session)
    
    async def is_quiet_hours(self) -> bool:
        """检查是否在静音时段"""
        # 从设置获取静音配置
        enabled = await self.settings_service.get_setting("quiet_hours_enabled")
        if enabled != "true":
            return False
        
        start_hour = await self.settings_service.get_setting("quiet_hours_start")
        end_hour = await self.settings_service.get_setting("quiet_hours_end")
        
        if not start_hour or not end_hour:
            return False
        
        try:
            start = int(start_hour)
            end = int(end_hour)
        except ValueError:
            return False
        
        current_hour = datetime.utcnow().hour
        
        if start <= end:
            # 例如 23:00 - 07:00 不跨天
            return start <= current_hour < end
        else:
            # 跨天情况 例如 23:00 - 07:00
            return current_hour >= start or current_hour < end
    
    async def should_notify(self) -> bool:
        """检查是否应该发送通知"""
        if await self.is_quiet_hours():
            return False
        return True
    
    async def get_notification_admins(self) -> List[int]:
        """获取应该接收通知的管理员列表"""
        # TODO: 从数据库获取启用通知的管理员
        return settings.admin_id_list
