#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作日志服务
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import OperationLog


class LogService:
    """操作日志服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_log(
        self,
        operator: str,
        action: str,
        target: Optional[str] = None,
        detail: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> OperationLog:
        """添加操作日志"""
        log = OperationLog(
            operator=operator,
            action=action,
            target=target,
            detail=detail,
            ip_address=ip_address
        )
        self.session.add(log)
        await self.session.flush()
        return log
    
    async def get_logs(
        self,
        page: int = 1,
        per_page: int = 50,
        operator: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[OperationLog], int]:
        """获取操作日志（分页）"""
        query = select(OperationLog)
        count_query = select(func.count(OperationLog.id))
        
        conditions = []
        
        if operator:
            conditions.append(OperationLog.operator == operator)
        if action:
            conditions.append(OperationLog.action.ilike(f"%{action}%"))
        if start_date:
            conditions.append(OperationLog.created_at >= start_date)
        if end_date:
            conditions.append(OperationLog.created_at <= end_date)
        
        if conditions:
            from sqlalchemy import and_
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        query = query.order_by(OperationLog.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        return logs, total
    
    async def get_recent_logs(self, limit: int = 20) -> List[OperationLog]:
        """获取最近的操作日志"""
        result = await self.session.execute(
            select(OperationLog)
            .order_by(OperationLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
