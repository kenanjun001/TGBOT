#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 客服聊天路由
"""

import secrets
import re
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database import get_db
from app.database.models import User, Message
from app.services.user import UserService
from app.services.message import MessageService
from app.services.admin import AdminService
from app.bot.bot import get_bot

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


class StartChatRequest(BaseModel):
    email: str


class SendMessageRequest(BaseModel):
    session_token: str
    message: str


class GetMessagesRequest(BaseModel):
    session_token: str
    last_id: Optional[int] = 0


def validate_email(email: str) -> bool:
    """简单的邮箱验证"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@router.get("", response_class=HTMLResponse)
async def chat_page(request: Request):
    """客服聊天页面"""
    return templates.TemplateResponse(
        "chat.html",
        {"request": request}
    )


@router.post("/start")
async def start_chat(
    data: StartChatRequest,
    session: AsyncSession = Depends(get_db)
):
    """开始聊天会话"""
    email = data.email.strip().lower()
    
    if not validate_email(email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    user_service = UserService(session)
    
    # 查找或创建Web用户
    result = await session.execute(
        select(User).where(User.email == email, User.source == "web")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # 创建新Web用户
        session_token = secrets.token_urlsafe(32)
        user = User(
            source="web",
            email=email,
            session_token=session_token,
            is_verified=True  # Web用户默认已验证
        )
        session.add(user)
        await session.flush()
    else:
        # 更新会话令牌
        session_token = secrets.token_urlsafe(32)
        user.session_token = session_token
        user.updated_at = datetime.utcnow()
        await session.flush()
    
    return JSONResponse({
        "success": True,
        "session_token": session_token,
        "user_id": user.id
    })


@router.post("/send")
async def send_message(
    data: SendMessageRequest,
    session: AsyncSession = Depends(get_db)
):
    """发送消息"""
    # 验证会话
    result = await session.execute(
        select(User).where(User.session_token == data.session_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="会话已过期，请重新输入邮箱")
    
    if user.is_blacklisted:
        raise HTTPException(status_code=403, detail="您已被禁止发送消息")
    
    message_content = data.message.strip()
    if not message_content:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    if len(message_content) > 2000:
        raise HTTPException(status_code=400, detail="消息太长，请限制在2000字以内")
    
    # 保存消息
    message_service = MessageService(session)
    msg = await message_service.create_message(
        user=user,
        direction="in",
        message_type="text",
        content=message_content
    )
    
    # 转发给所有管理员（使用可直接回复的方式）
    bot = get_bot()
    if bot:
        admin_service = AdminService(session)
        admin_ids = await admin_service.get_admin_tg_ids()
        
        # 先发送提示信息
        header_text = (
            f"🌐 <b>Web客服消息</b>\n"
            f"📧 {user.email or '未知邮箱'}"
        )
        
        for admin_id in admin_ids:
            try:
                # 发送头部信息
                await bot.send_message(
                    admin_id,
                    header_text,
                    parse_mode="HTML"
                )
                
                # 发送消息内容（管理员可以直接回复这条消息）
                sent_msg = await bot.send_message(
                    admin_id,
                    message_content
                )
                
                # 记录转发消息ID，用于回复追踪
                msg.forwarded_message_id = sent_msg.message_id
                await session.flush()
                
            except Exception as e:
                print(f"发送通知给管理员 {admin_id} 失败: {e}")
    
    return JSONResponse({
        "success": True,
        "message_id": msg.id,
        "created_at": msg.created_at.isoformat()
    })


@router.post("/messages")
async def get_messages(
    data: GetMessagesRequest,
    session: AsyncSession = Depends(get_db)
):
    """获取消息列表"""
    # 验证会话
    result = await session.execute(
        select(User).where(User.session_token == data.session_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="会话已过期")
    
    # 获取消息
    message_service = MessageService(session)
    messages, total = await message_service.get_user_messages(
        user_id=user.id,
        page=1,
        per_page=100
    )
    
    # 只返回新消息
    if data.last_id:
        messages = [m for m in messages if m.id > data.last_id]
    
    return JSONResponse({
        "success": True,
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "admin_name": m.admin.display_name if m.admin else None
            }
            for m in messages
        ],
        "total": total
    })


@router.get("/history/{session_token}")
async def get_chat_history(
    session_token: str,
    session: AsyncSession = Depends(get_db)
):
    """获取聊天历史"""
    result = await session.execute(
        select(User).where(User.session_token == session_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="会话已过期")
    
    message_service = MessageService(session)
    messages, total = await message_service.get_user_messages(
        user_id=user.id,
        page=1,
        per_page=100
    )
    
    return JSONResponse({
        "success": True,
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "admin_name": m.admin.display_name if m.admin else None
            }
            for m in messages
        ]
    })


@router.post("/upload")
async def upload_chat_file(
    session_token: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db)
):
    """Web客服上传图片"""
    import os
    import uuid
    
    # 验证会话
    result = await session.execute(
        select(User).where(User.session_token == session_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="会话已过期")
    
    if user.is_blacklisted:
        raise HTTPException(status_code=403, detail="您已被禁止发送消息")
    
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持图片格式")
    
    # 读取文件
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片太大，最大5MB")
    
    # 保存文件
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # 保存消息
    message_service = MessageService(session)
    msg = await message_service.create_message(
        user=user,
        direction="in",
        message_type="image",
        content="[图片]",
        file_id=filename
    )
    
    # 通知管理员（可直接回复）
    bot = get_bot()
    if bot:
        admin_service = AdminService(session)
        admin_ids = await admin_service.get_admin_tg_ids()
        
        for admin_id in admin_ids:
            try:
                # 先发送头部信息
                await bot.send_message(
                    admin_id,
                    f"🌐 <b>Web客服图片</b>\n📧 {user.email or '未知邮箱'}",
                    parse_mode="HTML"
                )
                
                # 发送图片（管理员可以直接回复）
                from aiogram.types import FSInputFile
                photo = FSInputFile(filepath)
                sent_msg = await bot.send_photo(admin_id, photo)
                
                # 记录转发消息ID
                msg.forwarded_message_id = sent_msg.message_id
                await session.flush()
                
            except Exception as e:
                print(f"发送图片通知失败: {e}")
    
    return JSONResponse({
        "success": True,
        "message_id": msg.id
    })
