#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人机验证模块
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.config import settings
from app.database.models import User

logger = logging.getLogger(__name__)


class VerificationManager:
    """验证管理器"""
    
    @staticmethod
    def generate_math_question() -> Tuple[str, str]:
        """生成数学题验证"""
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        op = random.choice(["+", "-", "×"])
        
        if op == "+":
            answer = a + b
        elif op == "-":
            # 确保结果为正数
            if a < b:
                a, b = b, a
            answer = a - b
        else:
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            answer = a * b
        
        question = f"{a} {op} {b} = ?"
        return question, str(answer)
    
    @staticmethod
    def generate_math_keyboard(correct_answer: str) -> InlineKeyboardMarkup:
        """生成数学题选项键盘"""
        correct = int(correct_answer)
        
        # 生成干扰项
        options = {correct}
        while len(options) < 4:
            offset = random.randint(-5, 5)
            if offset != 0:
                wrong = correct + offset
                if wrong >= 0:
                    options.add(wrong)
        
        options = list(options)
        random.shuffle(options)
        
        # 创建按钮
        buttons = []
        for opt in options:
            buttons.append(
                InlineKeyboardButton(
                    text=str(opt),
                    callback_data=f"verify_{opt}"
                )
            )
        
        return InlineKeyboardMarkup(inline_keyboard=[buttons])
    
    @staticmethod
    def generate_button_keyboard() -> InlineKeyboardMarkup:
        """生成按钮验证键盘"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ 我不是机器人",
                        callback_data="verify_human"
                    )
                ]
            ]
        )
    
    @staticmethod
    def get_verification_message(verification_type: str, question: Optional[str] = None) -> str:
        """获取验证提示消息"""
        if verification_type == "math":
            return (
                "🔐 <b>人机验证</b>\n\n"
                f"请在 {settings.VERIFICATION_TIMEOUT} 秒内回答以下问题：\n\n"
                f"<code>{question}</code>\n\n"
                "请点击正确答案："
            )
        else:
            return (
                "🔐 <b>人机验证</b>\n\n"
                f"请在 {settings.VERIFICATION_TIMEOUT} 秒内点击下方按钮完成验证："
            )
    
    @staticmethod
    def is_verification_expired(user: User) -> bool:
        """检查验证是否超时"""
        if not user.verification_expires:
            return True
        return datetime.utcnow() > user.verification_expires
    
    @staticmethod
    def is_temp_banned(user: User) -> bool:
        """检查是否被临时封禁"""
        if not user.temp_banned_until:
            return False
        return datetime.utcnow() < user.temp_banned_until
    
    @staticmethod
    def get_temp_ban_remaining(user: User) -> int:
        """获取临时封禁剩余时间（秒）"""
        if not user.temp_banned_until:
            return 0
        remaining = user.temp_banned_until - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))
    
    @staticmethod
    def should_temp_ban(user: User) -> bool:
        """检查是否应该临时封禁"""
        return user.verification_fails >= settings.MAX_VERIFICATION_FAILS
    
    @staticmethod
    def get_temp_ban_until() -> datetime:
        """获取临时封禁结束时间"""
        return datetime.utcnow() + timedelta(seconds=settings.TEMP_BAN_DURATION)
    
    @staticmethod
    def get_verification_expires() -> datetime:
        """获取验证过期时间"""
        return datetime.utcnow() + timedelta(seconds=settings.VERIFICATION_TIMEOUT)
