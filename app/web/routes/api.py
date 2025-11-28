#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 路由
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.web.auth import get_session_token, validate_session
from app.services.stats import StatsService
from app.services.user import UserService
from app.services.message import MessageService
from app.services.admin import AdminService
from app.bot.bot import get_bot
from app.config import settings

router = APIRouter()


class SendMessageRequest(BaseModel):
    user_id: int
    message: str


class AdminCreateRequest(BaseModel):
    tg_id: int
    name: Optional[str] = None


class AdminUpdateRequest(BaseModel):
    name: Optional[str] = None
    receive_messages: Optional[bool] = None
    can_reply: Optional[bool] = None
    is_active: Optional[bool] = None


@router.get("/stats/overview")
async def api_stats_overview(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """获取概览统计"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    stats_service = StatsService(session)
    overview = await stats_service.get_overview_stats()
    return JSONResponse(overview)


@router.get("/stats/chart")
async def api_stats_chart(
    request: Request,
    days: int = 7,
    session: AsyncSession = Depends(get_db)
):
    """获取图表数据"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    stats_service = StatsService(session)
    data = await stats_service.get_stats_range(days)
    return JSONResponse(data)


@router.get("/bot/status")
async def api_bot_status(request: Request):
    """获取机器人状态"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    bot = get_bot()
    if bot:
        try:
            me = await bot.get_me()
            return JSONResponse({
                "running": True,
                "bot_username": me.username,
                "bot_id": me.id
            })
        except Exception:
            pass
    
    return JSONResponse({"running": False})


@router.post("/send")
async def api_send_message(
    request: Request,
    data: SendMessageRequest,
    session: AsyncSession = Depends(get_db)
):
    """发送消息给用户"""
    token = get_session_token(request)
    user_session = validate_session(token)
    if not user_session:
        raise HTTPException(status_code=401, detail="未授权")
    
    user_service = UserService(session)
    message_service = MessageService(session)
    stats_service = StatsService(session)
    admin_service = AdminService(session)
    
    # 获取当前登录的管理员
    admin = await admin_service.get_admin_by_username(user_session.get("username"))
    admin_id = admin.id if admin else None
    
    # 先查找用户
    user = await user_service.get_user_by_tg_id(data.user_id)
    if not user:
        # 可能是通过用户ID发送（Web用户）
        user = await user_service.get_user_by_id(data.user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 发送消息
    if user.source == "telegram" and user.tg_id:
        bot = get_bot()
        if not bot:
            raise HTTPException(status_code=500, detail="机器人未运行")
        
        try:
            await bot.send_message(user.tg_id, data.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 记录消息（包含管理员ID）
    await message_service.create_message(
        user=user,
        direction="out",
        message_type="text",
        content=data.message,
        admin_id=admin_id
    )
    
    await stats_service.increment_outgoing_message()
    
    return JSONResponse({"success": True, "admin_name": admin.display_name if admin else "客服"})


@router.get("/users/export")
async def api_export_users(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """导出用户列表"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    user_service = UserService(session)
    users, _ = await user_service.get_all_users(page=1, per_page=10000)
    
    data = [
        {
            "source": u.source,
            "tg_id": u.tg_id,
            "email": u.email,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "is_verified": u.is_verified,
            "is_blacklisted": u.is_blacklisted,
            "is_whitelisted": u.is_whitelisted,
            "message_count": u.message_count,
            "tags": u.tags,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_message_at": u.last_message_at.isoformat() if u.last_message_at else None
        }
        for u in users
    ]
    
    return JSONResponse(data)


@router.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse({"status": "ok"})


@router.get("/messages/{user_id}")
async def api_get_user_messages(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db)
):
    """获取用户消息数量"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    user_service = UserService(session)
    message_service = MessageService(session)
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    messages, total = await message_service.get_user_messages(user.id, page=1, per_page=100)
    
    return JSONResponse({
        "count": total,
        "user_id": user_id
    })


@router.get("/messages/{user_id}/new")
async def api_get_new_messages(
    request: Request,
    user_id: int,
    last_id: int = Query(0),
    session: AsyncSession = Depends(get_db)
):
    """获取新消息（用于实时刷新）"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    message_service = MessageService(session)
    messages = await message_service.get_new_messages(user_id, last_id)
    
    return JSONResponse({
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "content": m.content,
                "message_type": m.message_type,
                "created_at": m.created_at.isoformat(),
                "admin_name": m.admin.display_name if m.admin else None
            }
            for m in messages
        ]
    })


# ==================== 管理员管理 ====================

@router.get("/admins")
async def api_list_admins(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """获取管理员列表"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    admin_service = AdminService(session)
    admins = await admin_service.get_all_admins()
    
    return JSONResponse({
        "admins": [
            {
                "id": a.id,
                "tg_id": a.tg_id,
                "name": a.name,
                "username": a.username,
                "is_super": a.is_super,
                "is_active": a.is_active,
                "receive_messages": a.receive_messages,
                "can_reply": a.can_reply,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in admins
        ]
    })


@router.post("/admins")
async def api_create_admin(
    request: Request,
    data: AdminCreateRequest,
    session: AsyncSession = Depends(get_db)
):
    """添加管理员"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    admin_service = AdminService(session)
    
    # 检查是否已存在
    existing = await admin_service.get_admin_by_tg_id(data.tg_id)
    if existing:
        raise HTTPException(status_code=400, detail="该管理员已存在")
    
    admin = await admin_service.create_admin(
        tg_id=data.tg_id,
        name=data.name
    )
    
    return JSONResponse({
        "success": True,
        "admin": {
            "id": admin.id,
            "tg_id": admin.tg_id,
            "name": admin.name
        }
    })


@router.put("/admins/{admin_id}")
async def api_update_admin(
    request: Request,
    admin_id: int,
    data: AdminUpdateRequest,
    session: AsyncSession = Depends(get_db)
):
    """更新管理员"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    admin_service = AdminService(session)
    admin = await admin_service.get_admin_by_id(admin_id)
    
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    
    await admin_service.update_admin(
        admin,
        name=data.name,
        receive_messages=data.receive_messages,
        can_reply=data.can_reply,
        is_active=data.is_active
    )
    
    return JSONResponse({"success": True})


@router.delete("/admins/{admin_id}")
async def api_delete_admin(
    request: Request,
    admin_id: int,
    session: AsyncSession = Depends(get_db)
):
    """删除管理员"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    admin_service = AdminService(session)
    admin = await admin_service.get_admin_by_id(admin_id)
    
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    
    if admin.is_super:
        raise HTTPException(status_code=400, detail="不能删除超级管理员")
    
    await admin_service.delete_admin(admin)
    
    return JSONResponse({"success": True})


# ==================== 快捷回复 ====================

@router.get("/quick-replies")
async def api_get_quick_replies(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """获取快捷回复列表"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    from sqlalchemy import select
    from app.database.models import QuickReply
    
    result = await session.execute(
        select(QuickReply).order_by(QuickReply.sort_order)
    )
    replies = result.scalars().all()
    
    return JSONResponse({
        "replies": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "sort_order": r.sort_order
            }
            for r in replies
        ]
    })


@router.post("/quick-replies")
async def api_create_quick_reply(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """创建快捷回复"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    data = await request.json()
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    
    if not title or not content:
        raise HTTPException(status_code=400, detail="标题和内容不能为空")
    
    from app.database.models import QuickReply
    
    reply = QuickReply(title=title, content=content)
    session.add(reply)
    await session.flush()
    
    return JSONResponse({
        "success": True,
        "id": reply.id
    })


@router.delete("/quick-replies/{reply_id}")
async def api_delete_quick_reply(
    request: Request,
    reply_id: int,
    session: AsyncSession = Depends(get_db)
):
    """删除快捷回复"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    from sqlalchemy import select
    from app.database.models import QuickReply
    
    result = await session.execute(
        select(QuickReply).where(QuickReply.id == reply_id)
    )
    reply = result.scalar_one_or_none()
    
    if not reply:
        raise HTTPException(status_code=404, detail="快捷回复不存在")
    
    await session.delete(reply)
    
    return JSONResponse({"success": True})


# ==================== 文件上传 ====================

import os
import uuid
from fastapi import UploadFile, File, Form

UPLOAD_DIR = "data/uploads"

@router.post("/upload")
async def api_upload_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Form(...),
    session: AsyncSession = Depends(get_db)
):
    """上传文件"""
    token = get_session_token(request)
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="未授权")
    
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    # 检查文件大小（最大 10MB）
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件太大，最大支持 10MB")
    
    # 创建上传目录
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 生成文件名
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    with open(filepath, "wb") as f:
        f.write(content)
    
    # 记录消息
    user_service = UserService(session)
    message_service = MessageService(session)
    
    user = await user_service.get_user_by_id(user_id)
    if user:
        await message_service.create_message(
            user=user,
            direction="out",
            message_type="image",
            content="[图片]",
            file_id=filename
        )
        
        # 如果是 TG 用户，发送图片
        if user.source == "telegram" and user.tg_id:
            bot = get_bot()
            if bot:
                try:
                    from aiogram.types import FSInputFile
                    photo = FSInputFile(filepath)
                    await bot.send_photo(user.tg_id, photo)
                except Exception as e:
                    print(f"发送图片失败: {e}")
    
    return JSONResponse({
        "success": True,
        "filename": filename,
        "url": f"/api/file/{filename}"
    })


@router.get("/file/{filename}")
async def api_get_file(filename: str):
    """获取文件"""
    from fastapi.responses import FileResponse
    
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(filepath)


# ==================== 满意度评价 ====================

class RatingRequest(BaseModel):
    session_token: str
    rating: int  # 1-5
    comment: Optional[str] = None


@router.post("/rating")
async def api_submit_rating(
    data: RatingRequest,
    session: AsyncSession = Depends(get_db)
):
    """提交满意度评价"""
    from sqlalchemy import select
    from app.database.models import User
    
    # 验证会话
    result = await session.execute(
        select(User).where(User.session_token == data.session_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="会话已过期")
    
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="评分必须在 1-5 之间")
    
    # 保存评价（使用 tags 字段存储）
    tags = user.tags or []
    tags = [t for t in tags if not t.startswith("评分:")]
    tags.append(f"评分:{data.rating}星")
    if data.comment:
        tags = [t for t in tags if not t.startswith("评价:")]
        tags.append(f"评价:{data.comment[:50]}")
    
    user.tags = tags
    await session.flush()
    
    return JSONResponse({
        "success": True,
        "message": "感谢您的评价！"
    })
