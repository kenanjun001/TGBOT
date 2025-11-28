#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证路由
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.web.auth import (
    create_session, destroy_session, get_session_token,
    validate_session, verify_password, check_login_block,
    record_login_fail, clear_login_fails, check_ip_whitelist
)
from app.database import get_db
from app.services.log import LogService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页重定向"""
    token = get_session_token(request)
    if validate_session(token):
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """登录页面"""
    # 检查是否已登录
    token = get_session_token(request)
    if validate_session(token):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error}
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """处理登录"""
    client_ip = request.client.host
    
    # 检查 IP 白名单
    if not check_ip_whitelist(client_ip):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "IP 地址不在允许范围内"}
        )
    
    # 检查是否被封禁
    if check_login_block(client_ip):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "登录失败次数过多，请稍后再试"}
        )
    
    # 验证用户名密码
    if username == settings.WEB_ADMIN_USERNAME and verify_password(password):
        clear_login_fails(client_ip)
        token = create_session(username)
        
        # 记录登录日志
        async for session in get_db():
            log_service = LogService(session)
            await log_service.add_log(
                operator=username,
                action="登录",
                detail="登录成功",
                ip_address=client_ip
            )
        
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            max_age=86400,  # 24小时
            samesite="lax"
        )
        return response
    
    # 登录失败
    record_login_fail(client_ip)
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "用户名或密码错误"}
    )


@router.get("/logout")
async def logout(request: Request):
    """退出登录"""
    token = get_session_token(request)
    if token:
        destroy_session(token)
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_token")
    return response
