#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=True, index=True)  # TG用户ID，Web用户为空
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # 用户来源
    source = Column(String(20), default="telegram")  # telegram / web
    email = Column(String(255), nullable=True, index=True)  # Web用户邮箱
    session_token = Column(String(100), nullable=True, index=True)  # Web用户会话
    
    # 验证状态
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(50), nullable=True)
    verification_expires = Column(DateTime, nullable=True)
    verification_fails = Column(Integer, default=0)
    
    # 封禁状态
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(String(500), nullable=True)
    is_whitelisted = Column(Boolean, default=False)
    temp_banned_until = Column(DateTime, nullable=True)
    
    # 标签
    tags = Column(JSON, default=list)
    
    # 统计
    message_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    
    # 关系
    messages = relationship("Message", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.tg_id or self.email}>"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        if self.source == "web":
            return self.email or f"Web_{self.id}"
        if self.username:
            return f"@{self.username}"
        name_parts = []
        if self.first_name:
            name_parts.append(self.first_name)
        if self.last_name:
            name_parts.append(self.last_name)
        return " ".join(name_parts) if name_parts else f"User_{self.tg_id}"
    
    @property
    def source_icon(self) -> str:
        """来源图标"""
        return "🌐" if self.source == "web" else "🤖"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tg_message_id = Column(BigInteger, nullable=True)
    
    # 消息方向: in=用户发给机器人, out=管理员回复
    direction = Column(String(10), nullable=False)  # in, out
    
    # 消息类型
    message_type = Column(String(50), default="text")  # text, photo, video, document, voice, sticker
    
    # 消息内容
    content = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)
    file_name = Column(String(255), nullable=True)
    
    # 转发的消息 ID（用于回复追踪）
    forwarded_message_id = Column(BigInteger, nullable=True)
    
    # 存储每个管理员收到的转发消息ID: {admin_tg_id: message_id}
    forwarded_message_ids = Column(JSON, default=dict)
    
    # 回复者（管理员ID）
    replied_by_admin = Column(Integer, ForeignKey("admins.id"), nullable=True)
    
    # 标记
    is_important = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    
    # 敏感词触发
    triggered_sensitive = Column(Boolean, default=False)
    sensitive_words = Column(JSON, default=list)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = relationship("User", back_populates="messages")
    admin = relationship("Admin", back_populates="replies")
    
    def __repr__(self):
        return f"<Message {self.id} from User {self.user_id}>"


class Admin(Base):
    """管理员表"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)  # 备注名
    username = Column(String(255), nullable=True)
    
    # 权限
    is_super = Column(Boolean, default=False)  # 超级管理员
    can_reply = Column(Boolean, default=True)
    can_blacklist = Column(Boolean, default=True)
    can_manage_admins = Column(Boolean, default=False)
    can_manage_settings = Column(Boolean, default=False)
    
    # 接收消息设置
    receive_messages = Column(Boolean, default=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    replies = relationship("Message", back_populates="admin")
    
    def __repr__(self):
        return f"<Admin {self.tg_id} ({self.name})>"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        if self.name:
            return self.name
        if self.username:
            return f"@{self.username}"
        return f"Admin_{self.tg_id}"


class SensitiveWord(Base):
    """敏感词表"""
    __tablename__ = "sensitive_words"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(255), unique=True, nullable=False, index=True)
    action = Column(String(50), default="warn")  # warn, block
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SensitiveWord {self.word}>"


class QuickReply(Base):
    """快捷回复模板"""
    __tablename__ = "quick_replies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuickReply {self.title}>"


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operator = Column(String(255), nullable=False)  # 操作者
    action = Column(String(255), nullable=False)  # 操作类型
    target = Column(String(255), nullable=True)  # 操作对象
    detail = Column(Text, nullable=True)  # 详细信息
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<OperationLog {self.action} by {self.operator}>"


class SystemSetting(Base):
    """系统设置表"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemSetting {self.key}>"


class DailyStats(Base):
    """每日统计表"""
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD
    new_users = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    incoming_messages = Column(Integer, default=0)
    outgoing_messages = Column(Integer, default=0)
    verification_attempts = Column(Integer, default=0)
    verification_success = Column(Integer, default=0)
    blocked_messages = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<DailyStats {self.date}>"


# 创建索引
Index("idx_messages_user_created", Message.user_id, Message.created_at)
Index("idx_user_verified_blacklist", User.is_verified, User.is_blacklisted)
Index("idx_user_source", User.source)
