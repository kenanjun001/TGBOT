#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息管理路由
"""

from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import json

from app.database import get_db
from app.web.auth import get_session_token, validate_session
from app.services.message import MessageService
from app.services.user import UserService
from app.services.settings import SettingsService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("", response_class=HTMLResponse)
async def messages_list(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    user_id: Optional[int] = None,
    direction: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """消息列表页面"""
    # 检查登录状态
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    message_service = MessageService(session)
    
    messages, total = await message_service.get_all_messages(
        page=page,
        per_page=50,
        search=search,
        user_id=user_id,
        direction=direction
    )
    
    total_pages = (total + 49) // 50
    
    return templates.TemplateResponse(
        "messages.html",
        {
            "request": request,
            "user": user_session,
            "messages": messages,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search or "",
            "filter_user_id": user_id or "",
            "filter_direction": direction or "",
            "active_page": "messages"
        }
    )


@router.get("/search", response_class=HTMLResponse)
async def search_messages(
    request: Request,
    keyword: str = Query(""),
    page: int = Query(1, ge=1),
    session: AsyncSession = Depends(get_db)
):
    """搜索消息页面"""
    # 检查登录状态
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    message_service = MessageService(session)
    
    if keyword:
        messages, total = await message_service.search_messages(
            keyword=keyword,
            page=page,
            per_page=50
        )
    else:
        messages, total = [], 0
    
    total_pages = (total + 49) // 50
    
    return templates.TemplateResponse(
        "messages_search.html",
        {
            "request": request,
            "user": user_session,
            "messages": messages,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "keyword": keyword,
            "active_page": "messages"
        }
    )


@router.post("/{message_id}/important")
async def toggle_important(
    request: Request,
    message_id: int,
    session: AsyncSession = Depends(get_db)
):
    """切换重要标记"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return JSONResponse({"error": "未登录"}, status_code=401)
    
    message_service = MessageService(session)
    message = await message_service.get_message_by_id(message_id)
    
    if message:
        await message_service.mark_as_important(message_id, not message.is_important)
        return JSONResponse({"success": True, "is_important": not message.is_important})
    
    return JSONResponse({"error": "消息不存在"}, status_code=404)


@router.get("/export")
async def export_messages(
    request: Request,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """导出消息"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    message_service = MessageService(session)
    
    # 解析日期
    start = None
    end = None
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass
    
    data = await message_service.export_messages(
        user_id=user_id,
        start_date=start,
        end_date=end
    )
    
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename=messages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


@router.get("/quick-replies", response_class=HTMLResponse)
async def quick_replies_page(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """快捷回复管理页面"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    settings_service = SettingsService(session)
    replies = await settings_service.get_quick_replies()
    
    return templates.TemplateResponse(
        "quick_replies.html",
        {
            "request": request,
            "user": user_session,
            "replies": replies,
            "active_page": "messages"
        }
    )


@router.post("/quick-replies/add")
async def add_quick_reply(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    """添加快捷回复"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    settings_service = SettingsService(session)
    await settings_service.add_quick_reply(title, content)
    
    return RedirectResponse(url="/messages/quick-replies", status_code=303)


@router.post("/quick-replies/{reply_id}/delete")
async def delete_quick_reply(
    request: Request,
    reply_id: int,
    session: AsyncSession = Depends(get_db)
):
    """删除快捷回复"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    settings_service = SettingsService(session)
    await settings_service.delete_quick_reply(reply_id)
    
    return RedirectResponse(url="/messages/quick-replies", status_code=303)
