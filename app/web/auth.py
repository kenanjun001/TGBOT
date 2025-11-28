#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 认证依赖
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
import hashlib
import secrets

from app.config import settings


# 简单的 session 存储（生产环境建议用 Redis）
_sessions: dict = {}

# 登录失败记录
_login_fails: dict = {}
MAX_LOGIN_FAILS = 5
LOGIN_BLOCK_DURATION = 300  # 秒


def get_session_token(request: Request) -> Optional[str]:
    """从 cookie 获取 session token"""
    return request.cookies.get("session_token")


def create_session(username: str) -> str:
    """创建 session"""
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    return token


def validate_session(token: str) -> Optional[dict]:
    """验证 session"""
    if not token or token not in _sessions:
        return None
    
    session = _sessions[token]
    if datetime.utcnow() > session["expires_at"]:
        del _sessions[token]
        return None
    
    return session


def destroy_session(token: str):
    """销毁 session"""
    if token in _sessions:
        del _sessions[token]


def check_login_block(ip: str) -> bool:
    """检查 IP 是否被封禁"""
    if ip not in _login_fails:
        return False
    
    fails = _login_fails[ip]
    if fails["count"] >= MAX_LOGIN_FAILS:
        if datetime.utcnow() < fails["blocked_until"]:
            return True
        else:
            # 解除封禁
            del _login_fails[ip]
    return False


def record_login_fail(ip: str):
    """记录登录失败"""
    if ip not in _login_fails:
        _login_fails[ip] = {"count": 0, "blocked_until": None}
    
    _login_fails[ip]["count"] += 1
    
    if _login_fails[ip]["count"] >= MAX_LOGIN_FAILS:
        _login_fails[ip]["blocked_until"] = datetime.utcnow() + timedelta(seconds=LOGIN_BLOCK_DURATION)


def clear_login_fails(ip: str):
    """清除登录失败记录"""
    if ip in _login_fails:
        del _login_fails[ip]


def check_ip_whitelist(ip: str) -> bool:
    """检查 IP 白名单"""
    whitelist = settings.ip_whitelist_list
    if not whitelist:
        return True  # 没有配置白名单则允许所有
    return ip in whitelist


async def get_current_user(request: Request) -> dict:
    """获取当前登录用户"""
    token = get_session_token(request)
    session = validate_session(token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    return session


async def require_auth(request: Request):
    """需要登录的依赖"""
    token = get_session_token(request)
    session = validate_session(token)
    
    if not session:
        # 返回重定向而不是异常
        return None
    
    return session


def verify_password(password: str) -> bool:
    """验证密码"""
    return password == settings.WEB_ADMIN_PASSWORD


def hash_password(password: str) -> str:
    """哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()
