#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计服务
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DailyStats, User, Message


class StatsService:
    """统计服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def _get_or_create_today_stats(self) -> DailyStats:
        """获取或创建今日统计"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        result = await self.session.execute(
            select(DailyStats).where(DailyStats.date == today)
        )
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = DailyStats(date=today)
            self.session.add(stats)
            await self.session.flush()
        
        return stats
    
    async def get_today_stats(self) -> Dict[str, int]:
        """获取今日统计"""
        stats = await self._get_or_create_today_stats()
        return {
            "new_users": stats.new_users,
            "total_messages": stats.total_messages,
            "incoming_messages": stats.incoming_messages,
            "outgoing_messages": stats.outgoing_messages,
            "verification_attempts": stats.verification_attempts,
            "verification_success": stats.verification_success,
            "blocked_messages": stats.blocked_messages
        }
    
    async def increment_new_user(self):
        """增加新用户数"""
        stats = await self._get_or_create_today_stats()
        stats.new_users += 1
        await self.session.flush()
    
    async def increment_message_count(self):
        """增加消息数"""
        stats = await self._get_or_create_today_stats()
        stats.total_messages += 1
        await self.session.flush()
    
    async def increment_incoming_message(self):
        """增加收到消息数"""
        stats = await self._get_or_create_today_stats()
        stats.total_messages += 1
        stats.incoming_messages += 1
        await self.session.flush()
    
    async def increment_outgoing_message(self):
        """增加发出消息数"""
        stats = await self._get_or_create_today_stats()
        stats.total_messages += 1
        stats.outgoing_messages += 1
        await self.session.flush()
    
    async def increment_verification_attempt(self):
        """增加验证尝试次数"""
        stats = await self._get_or_create_today_stats()
        stats.verification_attempts += 1
        await self.session.flush()
    
    async def increment_verification_success(self):
        """增加验证成功次数"""
        stats = await self._get_or_create_today_stats()
        stats.verification_attempts += 1
        stats.verification_success += 1
        await self.session.flush()
    
    async def increment_blocked_message(self):
        """增加拦截消息数"""
        stats = await self._get_or_create_today_stats()
        stats.blocked_messages += 1
        await self.session.flush()
    
    async def get_stats_range(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取一段时间的统计数据"""
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        result = await self.session.execute(
            select(DailyStats)
            .where(DailyStats.date >= start_date)
            .where(DailyStats.date <= end_date)
            .order_by(DailyStats.date)
        )
        stats_list = result.scalars().all()
        
        return [
            {
                "date": s.date,
                "new_users": s.new_users,
                "total_messages": s.total_messages,
                "incoming_messages": s.incoming_messages,
                "outgoing_messages": s.outgoing_messages,
                "verification_attempts": s.verification_attempts,
                "verification_success": s.verification_success,
                "blocked_messages": s.blocked_messages
            }
            for s in stats_list
        ]
    
    async def get_overview_stats(self) -> Dict[str, Any]:
        """获取概览统计"""
        # 总用户数
        user_count_result = await self.session.execute(
            select(func.count(User.id))
        )
        total_users = user_count_result.scalar()
        
        # 已验证用户数
        verified_count_result = await self.session.execute(
            select(func.count(User.id)).where(User.is_verified == True)
        )
        verified_users = verified_count_result.scalar()
        
        # 总消息数
        message_count_result = await self.session.execute(
            select(func.count(Message.id))
        )
        total_messages = message_count_result.scalar()
        
        # 今日新用户
        today = datetime.utcnow().date()
        today_users_result = await self.session.execute(
            select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
        )
        today_users = today_users_result.scalar()
        
        # 今日消息
        today_messages_result = await self.session.execute(
            select(func.count(Message.id)).where(
                func.date(Message.created_at) == today
            )
        )
        today_messages = today_messages_result.scalar()
        
        # 黑名单用户数
        blacklist_result = await self.session.execute(
            select(func.count(User.id)).where(User.is_blacklisted == True)
        )
        blacklisted_users = blacklist_result.scalar()
        
        return {
            "total_users": total_users,
            "verified_users": verified_users,
            "total_messages": total_messages,
            "today_users": today_users,
            "today_messages": today_messages,
            "blacklisted_users": blacklisted_users,
            "verification_rate": round(verified_users / total_users * 100, 1) if total_users > 0 else 0
        }
