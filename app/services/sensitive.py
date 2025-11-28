#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敏感词服务
"""

from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SensitiveWord


class SensitiveWordService:
    """敏感词服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._word_cache: Optional[List[SensitiveWord]] = None
    
    async def get_all_words(self) -> List[SensitiveWord]:
        """获取所有敏感词"""
        result = await self.session.execute(
            select(SensitiveWord).order_by(SensitiveWord.id)
        )
        return result.scalars().all()
    
    async def add_word(self, word: str, action: str = "warn") -> SensitiveWord:
        """添加敏感词"""
        # 检查是否已存在
        existing = await self.get_word(word)
        if existing:
            existing.action = action
            await self.session.flush()
            return existing
        
        sensitive_word = SensitiveWord(word=word, action=action)
        self.session.add(sensitive_word)
        await self.session.flush()
        self._word_cache = None  # 清除缓存
        return sensitive_word
    
    async def get_word(self, word: str) -> Optional[SensitiveWord]:
        """获取敏感词"""
        result = await self.session.execute(
            select(SensitiveWord).where(SensitiveWord.word == word)
        )
        return result.scalar_one_or_none()
    
    async def delete_word(self, word_id: int) -> bool:
        """删除敏感词"""
        result = await self.session.execute(
            select(SensitiveWord).where(SensitiveWord.id == word_id)
        )
        word = result.scalar_one_or_none()
        if word:
            await self.session.delete(word)
            await self.session.flush()
            self._word_cache = None
            return True
        return False
    
    async def check_content(self, content: str) -> Tuple[List[str], Optional[str]]:
        """
        检查内容是否包含敏感词
        返回: (触发的敏感词列表, 最严格的动作)
        """
        if not content:
            return [], None
        
        content_lower = content.lower()
        words = await self.get_all_words()
        
        triggered = []
        action = None
        
        for word in words:
            if word.word.lower() in content_lower:
                triggered.append(word.word)
                # block 优先级高于 warn
                if word.action == "block":
                    action = "block"
                elif action != "block":
                    action = "warn"
        
        return triggered, action
    
    async def import_words(self, words: List[str], action: str = "warn") -> int:
        """批量导入敏感词"""
        count = 0
        for word in words:
            word = word.strip()
            if word:
                await self.add_word(word, action)
                count += 1
        return count
    
    async def get_word_count(self) -> int:
        """获取敏感词数量"""
        result = await self.session.execute(
            select(func.count(SensitiveWord.id))
        )
        return result.scalar()
