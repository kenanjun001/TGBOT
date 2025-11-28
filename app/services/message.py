#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息服务
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Message, User, Admin


class MessageService:
    """消息服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_message(
        self,
        user: User,
        direction: str,
        message_type: str = "text",
        content: Optional[str] = None,
        file_id: Optional[str] = None,
        file_name: Optional[str] = None,
        tg_message_id: Optional[int] = None,
        forwarded_message_id: Optional[int] = None,
        forwarded_message_ids: Optional[dict] = None,
        triggered_sensitive: bool = False,
        sensitive_words: Optional[List[str]] = None,
        admin_id: Optional[int] = None
    ) -> Message:
        """创建消息记录"""
        message = Message(
            user_id=user.id,
            direction=direction,
            message_type=message_type,
            content=content,
            file_id=file_id,
            file_name=file_name,
            tg_message_id=tg_message_id,
            forwarded_message_id=forwarded_message_id,
            forwarded_message_ids=forwarded_message_ids or {},
            triggered_sensitive=triggered_sensitive,
            sensitive_words=sensitive_words or [],
            replied_by_admin=admin_id
        )
        self.session.add(message)
        
        # 更新用户统计
        user.message_count += 1
        user.last_message_at = datetime.utcnow()
        
        await self.session.flush()
        return message
    
    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """根据 ID 获取消息"""
        result = await self.session.execute(
            select(Message).options(
                selectinload(Message.user),
                selectinload(Message.admin)
            ).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()
    
    async def get_message_by_forwarded_id(
        self, 
        forwarded_id: int,
        admin_tg_id: Optional[int] = None
    ) -> Optional[Message]:
        """根据转发消息 ID 获取消息
        
        Args:
            forwarded_id: 转发消息ID
            admin_tg_id: 管理员TG ID，用于在新格式中查找
        """
        # 先尝试旧格式（单个forwarded_message_id）
        result = await self.session.execute(
            select(Message).options(
                selectinload(Message.user),
                selectinload(Message.admin)
            ).where(
                Message.forwarded_message_id == forwarded_id
            )
        )
        msg = result.scalar_one_or_none()
        if msg:
            return msg
        
        # 尝试新格式：在 forwarded_message_ids JSON 中查找
        result = await self.session.execute(
            select(Message).options(
                selectinload(Message.user),
                selectinload(Message.admin)
            ).where(
                Message.direction == "in"
            ).order_by(Message.created_at.desc()).limit(200)
        )
        messages = result.scalars().all()
        
        for msg in messages:
            if msg.forwarded_message_ids:
                # 如果指定了管理员ID，优先用它查找
                if admin_tg_id and str(admin_tg_id) in msg.forwarded_message_ids:
                    if msg.forwarded_message_ids[str(admin_tg_id)] == forwarded_id:
                        return msg
                else:
                    # 否则遍历所有管理员的转发记录
                    for admin_id_str, fwd_msg_id in msg.forwarded_message_ids.items():
                        if fwd_msg_id == forwarded_id:
                            return msg
        
        return None
    
    async def get_user_messages(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 50,
        order_asc: bool = True  # 默认正序（新消息在下面）
    ) -> tuple[List[Message], int]:
        """获取用户消息（分页）"""
        query = select(Message).options(
            selectinload(Message.admin)
        ).where(Message.user_id == user_id)
        count_query = select(func.count(Message.id)).where(Message.user_id == user_id)
        
        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 排序
        if order_asc:
            query = query.order_by(Message.created_at.asc())
        else:
            query = query.order_by(Message.created_at.desc())
        
        # 分页
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.session.execute(query)
        messages = result.scalars().all()
        
        return messages, total
    
    async def get_new_messages(
        self,
        user_id: int,
        last_id: int = 0
    ) -> List[Message]:
        """获取新消息（用于实时刷新）"""
        result = await self.session.execute(
            select(Message).options(
                selectinload(Message.admin)
            ).where(
                Message.user_id == user_id,
                Message.id > last_id
            ).order_by(Message.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_all_messages(
        self,
        page: int = 1,
        per_page: int = 50,
        search: Optional[str] = None,
        user_id: Optional[int] = None,
        direction: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[Message], int]:
        """获取所有消息（分页）"""
        query = select(Message).options(
            selectinload(Message.user),
            selectinload(Message.admin)
        )
        count_query = select(func.count(Message.id))
        
        conditions = []
        
        if search:
            conditions.append(Message.content.ilike(f"%{search}%"))
        
        if user_id:
            conditions.append(Message.user_id == user_id)
        
        if direction:
            conditions.append(Message.direction == direction)
        
        if start_date:
            conditions.append(Message.created_at >= start_date)
        
        if end_date:
            conditions.append(Message.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        query = query.order_by(Message.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.session.execute(query)
        messages = result.scalars().all()
        
        return messages, total
    
    async def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """获取最近消息"""
        result = await self.session.execute(
            select(Message)
            .options(selectinload(Message.user), selectinload(Message.admin))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def mark_as_read(self, message_id: int):
        """标记为已读"""
        message = await self.get_message_by_id(message_id)
        if message:
            message.is_read = True
            await self.session.flush()
    
    async def mark_as_important(self, message_id: int, important: bool = True):
        """标记为重要"""
        message = await self.get_message_by_id(message_id)
        if message:
            message.is_important = important
            await self.session.flush()
    
    async def get_message_count(self) -> int:
        """获取消息总数"""
        result = await self.session.execute(
            select(func.count(Message.id))
        )
        return result.scalar()
    
    async def get_today_message_count(self) -> int:
        """获取今日消息数"""
        today = datetime.utcnow().date()
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                func.date(Message.created_at) == today
            )
        )
        return result.scalar()
    
    async def get_unread_count(self) -> int:
        """获取未读消息数"""
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                and_(Message.is_read == False, Message.direction == "in")
            )
        )
        return result.scalar()
    
    async def search_messages(
        self,
        keyword: str,
        page: int = 1,
        per_page: int = 50
    ) -> tuple[List[Message], int]:
        """搜索消息"""
        query = select(Message).options(
            selectinload(Message.user),
            selectinload(Message.admin)
        ).where(
            Message.content.ilike(f"%{keyword}%")
        )
        count_query = select(func.count(Message.id)).where(
            Message.content.ilike(f"%{keyword}%")
        )
        
        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        query = query.order_by(Message.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.session.execute(query)
        messages = result.scalars().all()
        
        return messages, total
    
    async def export_messages(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """导出消息"""
        query = select(Message).options(
            selectinload(Message.user),
            selectinload(Message.admin)
        )
        conditions = []
        
        if user_id:
            conditions.append(Message.user_id == user_id)
        if start_date:
            conditions.append(Message.created_at >= start_date)
        if end_date:
            conditions.append(Message.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Message.created_at.asc())
        
        result = await self.session.execute(query)
        messages = result.scalars().all()
        
        return [
            {
                "id": m.id,
                "user_id": m.user.tg_id if m.user.tg_id else m.user.email,
                "username": m.user.username or m.user.email,
                "direction": m.direction,
                "type": m.message_type,
                "content": m.content,
                "admin": m.admin.display_name if m.admin else None,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
