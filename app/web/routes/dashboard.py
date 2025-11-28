#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪表盘路由
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.web.auth import get_session_token, validate_session
from app.services.stats import StatsService
from app.services.message import MessageService
from app.services.user import UserService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_db)):
    """仪表盘页面"""
    # 检查登录状态
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    # 获取统计数据
    stats_service = StatsService(session)
    message_service = MessageService(session)
    user_service = UserService(session)
    
    overview = await stats_service.get_overview_stats()
    today_stats = await stats_service.get_today_stats()
    recent_messages = await message_service.get_recent_messages(10)
    chart_data = await stats_service.get_stats_range(7)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user_session,
            "overview": overview,
            "today": today_stats,
            "recent_messages": recent_messages,
            "chart_data": chart_data,
            "active_page": "dashboard"
        }
    )
