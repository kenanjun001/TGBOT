#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 路由
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储活跃的 WebSocket 连接
# key: user_id, value: set of WebSocket connections
active_connections: Dict[int, Set[WebSocket]] = {}


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    @staticmethod
    async def connect(websocket: WebSocket, user_id: int):
        """建立连接"""
        await websocket.accept()
        if user_id not in active_connections:
            active_connections[user_id] = set()
        active_connections[user_id].add(websocket)
        logger.info(f"WebSocket 连接建立: user_id={user_id}")
    
    @staticmethod
    def disconnect(websocket: WebSocket, user_id: int):
        """断开连接"""
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]
        logger.info(f"WebSocket 连接断开: user_id={user_id}")
    
    @staticmethod
    async def send_to_user(user_id: int, message: dict):
        """发送消息给指定用户的所有连接"""
        if user_id in active_connections:
            dead_connections = set()
            for websocket in active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"发送 WebSocket 消息失败: {e}")
                    dead_connections.add(websocket)
            
            # 清理死连接
            for ws in dead_connections:
                active_connections[user_id].discard(ws)
    
    @staticmethod
    async def broadcast_new_message(user_id: int, message_data: dict):
        """广播新消息"""
        await ConnectionManager.send_to_user(user_id, {
            "type": "new_message",
            "message": message_data
        })


manager = ConnectionManager()


@router.websocket("/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int):
    """聊天 WebSocket 端点"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 保持连接，接收心跳
            data = await websocket.receive_text()
            
            # 处理心跳
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        manager.disconnect(websocket, user_id)


# 供其他模块调用的函数
async def notify_new_message(user_id: int, message_data: dict):
    """通知新消息（供消息服务调用）"""
    await manager.broadcast_new_message(user_id, message_data)
