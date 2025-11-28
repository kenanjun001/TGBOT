#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理路由
"""

from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.web.auth import get_session_token, validate_session
from app.services.user import UserService
from app.services.message import MessageService
from app.services.log import LogService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("", response_class=HTMLResponse)
async def users_list(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    filter_verified: Optional[str] = None,
    filter_blacklisted: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """用户列表页面"""
    # 检查登录状态
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    user_service = UserService(session)
    
    # 处理筛选参数
    verified = None
    if filter_verified == "true":
        verified = True
    elif filter_verified == "false":
        verified = False
    
    blacklisted = None
    if filter_blacklisted == "true":
        blacklisted = True
    elif filter_blacklisted == "false":
        blacklisted = False
    
    users, total = await user_service.get_all_users(
        page=page,
        per_page=20,
        search=search,
        filter_verified=verified,
        filter_blacklisted=blacklisted
    )
    
    total_pages = (total + 19) // 20
    
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user": user_session,
            "users": users,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search or "",
            "filter_verified": filter_verified or "",
            "filter_blacklisted": filter_blacklisted or "",
            "active_page": "users"
        }
    )


@router.get("/{user_id}", response_class=HTMLResponse)
async def user_detail(
    request: Request,
    user_id: int,
    page: int = Query(1, ge=1),
    session: AsyncSession = Depends(get_db)
):
    """用户详情页面"""
    # 检查登录状态
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    user_service = UserService(session)
    message_service = MessageService(session)
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        return RedirectResponse(url="/users", status_code=303)
    
    messages, total = await message_service.get_user_messages(
        user_id=user_id,
        page=page,
        per_page=50
    )
    
    total_pages = (total + 49) // 50
    
    return templates.TemplateResponse(
        "user_detail.html",
        {
            "request": request,
            "user": user_session,
            "target_user": user,
            "messages": messages,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "active_page": "users"
        }
    )


@router.post("/{user_id}/blacklist")
async def toggle_blacklist(
    request: Request,
    user_id: int,
    action: str = Form(...),
    reason: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_db)
):
    """切换黑名单状态"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    user_service = UserService(session)
    log_service = LogService(session)
    
    user = await user_service.get_user_by_id(user_id)
    if user:
        is_blacklisted = action == "add"
        await user_service.set_blacklist(user, is_blacklisted, reason)
        
        # 记录操作日志
        await log_service.add_log(
            operator=user_session["username"],
            action="拉黑用户" if is_blacklisted else "解除拉黑",
            target=str(user.tg_id),
            detail=reason,
            ip_address=request.client.host
        )
    
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/whitelist")
async def toggle_whitelist(
    request: Request,
    user_id: int,
    action: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    """切换白名单状态"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    user_service = UserService(session)
    log_service = LogService(session)
    
    user = await user_service.get_user_by_id(user_id)
    if user:
        is_whitelisted = action == "add"
        await user_service.set_whitelist(user, is_whitelisted)
        
        # 记录操作日志
        await log_service.add_log(
            operator=user_session["username"],
            action="添加白名单" if is_whitelisted else "移除白名单",
            target=str(user.tg_id),
            ip_address=request.client.host
        )
    
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/tags")
async def update_tags(
    request: Request,
    user_id: int,
    tags: str = Form(""),
    session: AsyncSession = Depends(get_db)
):
    """更新用户标签"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    user_service = UserService(session)
    
    user = await user_service.get_user_by_id(user_id)
    if user:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        await user_service.set_tags(user, tag_list)
    
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)
