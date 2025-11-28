#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="your-secret-key-change-me")
    
    # Telegram 配置
    BOT_TOKEN: str = Field(default="")
    ADMIN_IDS: str = Field(default="")  # 逗号分隔的管理员 TG ID
    
    # 数据库配置
    DB_TYPE: str = Field(default="sqlite")  # sqlite, mysql, postgres
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=3306)
    DB_NAME: str = Field(default="tg_relay_bot")
    DB_USER: str = Field(default="root")
    DB_PASSWORD: str = Field(default="")
    SQLITE_PATH: str = Field(default="data/bot.db")
    
    # Web 配置
    WEB_HOST: str = Field(default="0.0.0.0")
    WEB_PORT: int = Field(default=8080)
    
    # 验证配置
    VERIFICATION_TYPE: str = Field(default="math")  # math, button
    VERIFICATION_TIMEOUT: int = Field(default=60)  # 秒
    MAX_VERIFICATION_FAILS: int = Field(default=3)
    TEMP_BAN_DURATION: int = Field(default=3600)  # 临时封禁时长(秒)
    
    # 通知配置
    QUIET_HOURS_START: int = Field(default=23)  # 静音开始时间
    QUIET_HOURS_END: int = Field(default=7)  # 静音结束时间
    ENABLE_QUIET_HOURS: bool = Field(default=False)
    
    # 自动回复配置
    AUTO_REPLY_ENABLED: bool = Field(default=False)
    AUTO_REPLY_MESSAGE: str = Field(default="您好，我目前不在线，稍后会回复您。")
    
    # Web 管理员账号
    WEB_ADMIN_USERNAME: str = Field(default="admin")
    WEB_ADMIN_PASSWORD: str = Field(default="admin123")
    
    # IP 白名单（逗号分隔，为空则不限制）
    IP_WHITELIST: str = Field(default="")
    
    @property
    def admin_id_list(self) -> List[int]:
        """获取管理员 ID 列表"""
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]
    
    @property
    def ip_whitelist_list(self) -> List[str]:
        """获取 IP 白名单列表"""
        if not self.IP_WHITELIST:
            return []
        return [x.strip() for x in self.IP_WHITELIST.split(",") if x.strip()]
    
    @property
    def database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.DB_TYPE == "sqlite":
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        elif self.DB_TYPE == "mysql":
            return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == "postgres":
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            raise ValueError(f"不支持的数据库类型: {self.DB_TYPE}")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
