#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员服务
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Admin


class AdminService:
    """管理员服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_admin_by_id(self, admin_id: int) -> Optional[Admin]:
        """根据ID获取管理员"""
        result = await self.session.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        return result.scalar_one_or_none()
    
    async def get_admin_by_tg_id(self, tg_id: int) -> Optional[Admin]:
        """根据TG ID获取管理员"""
        result = await self.session.execute(
            select(Admin).where(Admin.tg_id == tg_id)
        )
        return result.scalar_one_or_none()
    
    async def get_admin_by_username(self, username: str) -> Optional[Admin]:
        """根据用户名获取管理员"""
        result = await self.session.execute(
            select(Admin).where(Admin.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_all_admins(self) -> List[Admin]:
        """获取所有管理员"""
        result = await self.session.execute(
            select(Admin).order_by(Admin.created_at)
        )
        return result.scalars().all()
    
    async def get_active_admins(self) -> List[Admin]:
        """获取所有活跃管理员"""
        result = await self.session.execute(
            select(Admin).where(
                Admin.is_active == True,
                Admin.receive_messages == True
            )
        )
        return result.scalars().all()
    
    async def get_admin_tg_ids(self) -> List[int]:
        """获取所有活跃管理员的TG ID"""
        admins = await self.get_active_admins()
        return [a.tg_id for a in admins]
    
    async def create_admin(
        self,
        tg_id: int,
        name: Optional[str] = None,
        username: Optional[str] = None,
        is_super: bool = False
    ) -> Admin:
        """创建管理员"""
        admin = Admin(
            tg_id=tg_id,
            name=name,
            username=username,
            is_super=is_super,
            can_manage_admins=is_super,
            can_manage_settings=is_super
        )
        self.session.add(admin)
        await self.session.flush()
        return admin
    
    async def update_admin(
        self,
        admin: Admin,
        name: Optional[str] = None,
        receive_messages: Optional[bool] = None,
        can_reply: Optional[bool] = None,
        can_blacklist: Optional[bool] = None,
        is_active: Optional[bool] = None
    ):
        """更新管理员信息"""
        if name is not None:
            admin.name = name
        if receive_messages is not None:
            admin.receive_messages = receive_messages
        if can_reply is not None:
            admin.can_reply = can_reply
        if can_blacklist is not None:
            admin.can_blacklist = can_blacklist
        if is_active is not None:
            admin.is_active = is_active
        await self.session.flush()
    
    async def delete_admin(self, admin: Admin):
        """删除管理员"""
        await self.session.delete(admin)
        await self.session.flush()
    
    async def is_admin(self, tg_id: int) -> bool:
        """检查是否是管理员"""
        admin = await self.get_admin_by_tg_id(tg_id)
        return admin is not None and admin.is_active
    
    async def init_admins_from_config(self, admin_ids: List[int]):
        """从配置初始化管理员"""
        for i, tg_id in enumerate(admin_ids):
            existing = await self.get_admin_by_tg_id(tg_id)
            if not existing:
                await self.create_admin(
                    tg_id=tg_id,
                    name=f"管理员{i+1}" if i > 0 else "主管理员",
                    is_super=(i == 0)  # 第一个是超级管理员
                )
