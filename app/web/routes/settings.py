#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置路由
"""

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config import settings
from app.database import get_db
from app.web.auth import get_session_token, validate_session
from app.services.settings import SettingsService
from app.services.sensitive import SensitiveWordService
from app.services.log import LogService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """设置页面"""
    # 检查登录状态
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    settings_service = SettingsService(session)
    all_settings = await settings_service.get_all_settings()
    
    # Token 脱敏显示
    bot_token_masked = ""
    if settings.BOT_TOKEN:
        token_parts = settings.BOT_TOKEN.split(":")
        if len(token_parts) == 2:
            bot_token_masked = token_parts[0] + ":****" + token_parts[1][-4:]
        else:
            bot_token_masked = settings.BOT_TOKEN[:10] + "****"
    
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user_session,
            "settings": all_settings,
            "bot_token_masked": bot_token_masked,
            "env_settings": {
                "bot_token": settings.BOT_TOKEN[:10] + "..." if settings.BOT_TOKEN else "",
                "admin_ids": settings.ADMIN_IDS,
                "db_type": settings.DB_TYPE,
            },
            "active_page": "settings"
        }
    )


@router.post("/verification")
async def update_verification_settings(
    request: Request,
    verification_type: str = Form(...),
    verification_timeout: int = Form(60),
    max_fails: int = Form(3),
    temp_ban_duration: int = Form(3600),
    session: AsyncSession = Depends(get_db)
):
    """更新验证设置"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    settings_service = SettingsService(session)
    log_service = LogService(session)
    
    await settings_service.set_setting("verification_type", verification_type)
    await settings_service.set_setting("verification_timeout", str(verification_timeout))
    await settings_service.set_setting("max_verification_fails", str(max_fails))
    await settings_service.set_setting("temp_ban_duration", str(temp_ban_duration))
    
    await log_service.add_log(
        operator=user_session["username"],
        action="更新验证设置",
        ip_address=request.client.host
    )
    
    return RedirectResponse(url="/settings?tab=verification&success=1", status_code=303)


@router.post("/messages")
async def update_message_settings(
    request: Request,
    welcome_message: str = Form(""),
    auto_reply_enabled: str = Form("false"),
    auto_reply_message: str = Form(""),
    session: AsyncSession = Depends(get_db)
):
    """更新消息设置"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    settings_service = SettingsService(session)
    log_service = LogService(session)
    
    await settings_service.set_setting("welcome_message", welcome_message)
    await settings_service.set_setting("auto_reply_enabled", auto_reply_enabled)
    await settings_service.set_setting("auto_reply_message", auto_reply_message)
    
    await log_service.add_log(
        operator=user_session["username"],
        action="更新消息设置",
        ip_address=request.client.host
    )
    
    return RedirectResponse(url="/settings?tab=messages&success=1", status_code=303)


@router.post("/notification")
async def update_notification_settings(
    request: Request,
    quiet_hours_enabled: str = Form("false"),
    quiet_hours_start: int = Form(23),
    quiet_hours_end: int = Form(7),
    session: AsyncSession = Depends(get_db)
):
    """更新通知设置"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    settings_service = SettingsService(session)
    log_service = LogService(session)
    
    await settings_service.set_setting("quiet_hours_enabled", quiet_hours_enabled)
    await settings_service.set_setting("quiet_hours_start", str(quiet_hours_start))
    await settings_service.set_setting("quiet_hours_end", str(quiet_hours_end))
    
    await log_service.add_log(
        operator=user_session["username"],
        action="更新通知设置",
        ip_address=request.client.host
    )
    
    return RedirectResponse(url="/settings?tab=notification&success=1", status_code=303)


@router.post("/bot")
async def update_bot_settings(
    request: Request,
    bot_token: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    """更新机器人Token"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    log_service = LogService(session)
    
    # 检查是否是新Token（不是脱敏的旧Token）
    if "****" in bot_token:
        # 用户没有修改Token
        return RedirectResponse(url="/settings?success=1", status_code=303)
    
    # 验证Token格式
    if not bot_token or ":" not in bot_token:
        return RedirectResponse(url="/settings?error=invalid_token", status_code=303)
    
    # 更新.env文件
    import os
    env_path = ".env"
    
    try:
        # 读取现有.env
        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_content = f.read()
        
        # 替换或添加BOT_TOKEN
        lines = env_content.split("\n")
        new_lines = []
        token_found = False
        
        for line in lines:
            if line.startswith("BOT_TOKEN="):
                new_lines.append(f"BOT_TOKEN={bot_token}")
                token_found = True
            else:
                new_lines.append(line)
        
        if not token_found:
            new_lines.insert(0, f"BOT_TOKEN={bot_token}")
        
        # 写入.env
        with open(env_path, "w") as f:
            f.write("\n".join(new_lines))
        
        # 记录日志
        await log_service.add_log(
            operator=user_session["username"],
            action="更新机器人Token",
            detail="Token已更新，需要重启服务",
            ip_address=request.client.host
        )
        
        # 尝试重启机器人
        try:
            from app.bot.bot import restart_bot
            await restart_bot(bot_token)
        except Exception as e:
            print(f"重启机器人失败: {e}")
        
        return RedirectResponse(url="/settings?success=bot_updated", status_code=303)
        
    except Exception as e:
        print(f"保存Token失败: {e}")
        return RedirectResponse(url="/settings?error=save_failed", status_code=303)


@router.get("/sensitive", response_class=HTMLResponse)
async def sensitive_words_page(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """敏感词管理页面"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    sensitive_service = SensitiveWordService(session)
    words = await sensitive_service.get_all_words()
    
    return templates.TemplateResponse(
        "sensitive_words.html",
        {
            "request": request,
            "user": user_session,
            "words": words,
            "active_page": "settings"
        }
    )


@router.post("/sensitive/add")
async def add_sensitive_word(
    request: Request,
    word: str = Form(...),
    action: str = Form("warn"),
    session: AsyncSession = Depends(get_db)
):
    """添加敏感词"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    sensitive_service = SensitiveWordService(session)
    log_service = LogService(session)
    
    await sensitive_service.add_word(word.strip(), action)
    
    await log_service.add_log(
        operator=user_session["username"],
        action="添加敏感词",
        target=word,
        ip_address=request.client.host
    )
    
    return RedirectResponse(url="/settings/sensitive", status_code=303)


@router.post("/sensitive/{word_id}/delete")
async def delete_sensitive_word(
    request: Request,
    word_id: int,
    session: AsyncSession = Depends(get_db)
):
    """删除敏感词"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    sensitive_service = SensitiveWordService(session)
    log_service = LogService(session)
    
    await sensitive_service.delete_word(word_id)
    
    await log_service.add_log(
        operator=user_session["username"],
        action="删除敏感词",
        target=str(word_id),
        ip_address=request.client.host
    )
    
    return RedirectResponse(url="/settings/sensitive", status_code=303)


@router.post("/sensitive/import")
async def import_sensitive_words(
    request: Request,
    words_text: str = Form(""),
    action: str = Form("warn"),
    session: AsyncSession = Depends(get_db)
):
    """批量导入敏感词"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    sensitive_service = SensitiveWordService(session)
    log_service = LogService(session)
    
    words = [w.strip() for w in words_text.split("\n") if w.strip()]
    count = await sensitive_service.import_words(words, action)
    
    await log_service.add_log(
        operator=user_session["username"],
        action="批量导入敏感词",
        detail=f"导入 {count} 个敏感词",
        ip_address=request.client.host
    )
    
    return RedirectResponse(url="/settings/sensitive", status_code=303)


@router.get("/logs", response_class=HTMLResponse)
async def operation_logs_page(
    request: Request,
    page: int = 1,
    session: AsyncSession = Depends(get_db)
):
    """操作日志页面"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    
    log_service = LogService(session)
    logs, total = await log_service.get_logs(page=page, per_page=50)
    
    total_pages = (total + 49) // 50
    
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "user": user_session,
            "logs": logs,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "active_page": "settings"
        }
    )
