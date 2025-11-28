#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户服务
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


class UserService:
    """用户服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_tg_id(self, tg_id: int) -> Optional[User]:
        """根据 TG ID 获取用户"""
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_user(
        self,
        tg_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """获取或创建用户"""
        user = await self.get_user_by_tg_id(tg_id)
        
        if user:
            # 更新用户信息
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.updated_at = datetime.utcnow()
        else:
            # 创建新用户
            user = User(
                tg_id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            self.session.add(user)
        
        await self.session.flush()
        return user
    
    async def set_verification(
        self,
        user: User,
        code: str,
        expires: datetime
    ):
        """设置验证信息"""
        user.verification_code = code
        user.verification_expires = expires
        await self.session.flush()
    
    async def set_verified(self, user: User, verified: bool):
        """设置验证状态"""
        user.is_verified = verified
        if verified:
            user.verification_code = None
            user.verification_expires = None
        await self.session.flush()
    
    async def increment_verification_fails(self, user: User):
        """增加验证失败次数"""
        user.verification_fails += 1
        await self.session.flush()
    
    async def reset_verification_fails(self, user: User):
        """重置验证失败次数"""
        user.verification_fails = 0
        await self.session.flush()
    
    async def set_temp_ban(self, user: User, until: datetime):
        """设置临时封禁"""
        user.temp_banned_until = until
        await self.session.flush()
    
    async def set_blacklist(
        self,
        user: User,
        blacklisted: bool,
        reason: Optional[str] = None
    ):
        """设置黑名单状态"""
        user.is_blacklisted = blacklisted
        user.blacklist_reason = reason if blacklisted else None
        await self.session.flush()
    
    async def set_whitelist(self, user: User, whitelisted: bool):
        """设置白名单状态"""
        user.is_whitelisted = whitelisted
        if whitelisted:
            user.is_verified = True  # 白名单自动通过验证
        await self.session.flush()
    
    async def increment_message_count(self, user: User):
        """增加消息计数"""
        user.message_count += 1
        user.last_message_at = datetime.utcnow()
        await self.session.flush()
    
    async def set_tags(self, user: User, tags: List[str]):
        """设置用户标签"""
        user.tags = tags
        await self.session.flush()
    
    async def add_tag(self, user: User, tag: str):
        """添加用户标签"""
        if tag not in user.tags:
            user.tags = user.tags + [tag]
            await self.session.flush()
    
    async def remove_tag(self, user: User, tag: str):
        """移除用户标签"""
        if tag in user.tags:
            user.tags = [t for t in user.tags if t != tag]
            await self.session.flush()
    
    async def get_all_users(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        filter_verified: Optional[bool] = None,
        filter_blacklisted: Optional[bool] = None,
        filter_tag: Optional[str] = None
    ) -> tuple[List[User], int]:
        """获取所有用户（分页）"""
        query = select(User)
        count_query = select(func.count(User.id))
        
        # 搜索条件
        if search:
            search_filter = User.username.ilike(f"%{search}%") | \
                           User.first_name.ilike(f"%{search}%") | \
                           User.tg_id.cast(str).ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # 筛选条件
        if filter_verified is not None:
            query = query.where(User.is_verified == filter_verified)
            count_query = count_query.where(User.is_verified == filter_verified)
        
        if filter_blacklisted is not None:
            query = query.where(User.is_blacklisted == filter_blacklisted)
            count_query = count_query.where(User.is_blacklisted == filter_blacklisted)
        
        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        return users, total
    
    async def get_user_count(self) -> int:
        """获取用户总数"""
        result = await self.session.execute(
            select(func.count(User.id))
        )
        return result.scalar()
    
    async def get_today_new_users(self) -> int:
        """获取今日新用户数"""
        today = datetime.utcnow().date()
        result = await self.session.execute(
            select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
        )
        return result.scalar()
    
    async def get_verified_user_count(self) -> int:
        """获取已验证用户数"""
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_verified == True)
        )
        return result.scalar()
    
    async def get_blacklisted_users(self) -> List[User]:
        """获取黑名单用户"""
        result = await self.session.execute(
            select(User).where(User.is_blacklisted == True)
        )
        return result.scalars().all()
    
    async def get_whitelisted_users(self) -> List[User]:
        """获取白名单用户"""
        result = await self.session.execute(
            select(User).where(User.is_whitelisted == True)
        )
        return result.scalars().all()
