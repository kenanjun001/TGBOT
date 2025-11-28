#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息处理器
"""

import logging
from datetime import datetime
from typing import Optional
from aiogram import Dispatcher, Router, F, Bot
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import Command, CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import User, Message as DBMessage
from app.services.user import UserService
from app.services.message import MessageService
from app.services.sensitive import SensitiveWordService
from app.services.settings import SettingsService
from app.services.stats import StatsService
from app.services.notification import NotificationService
from app.services.admin import AdminService
from app.bot.verification import VerificationManager

logger = logging.getLogger(__name__)

router = Router()


def is_admin(user_id: int) -> bool:
    """检查是否是管理员（快速检查，使用配置文件）"""
    return user_id in settings.admin_id_list


async def is_admin_db(user_id: int, session: AsyncSession) -> bool:
    """检查是否是管理员（数据库检查，包括配置文件和数据库）"""
    # 先检查配置文件
    if user_id in settings.admin_id_list:
        return True
    # 再检查数据库
    admin_service = AdminService(session)
    return await admin_service.is_admin(user_id)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, db_user: User):
    """处理 /start 命令"""
    user_service = UserService(session)
    settings_service = SettingsService(session)
    
    # 管理员直接跳过
    if await is_admin_db(message.from_user.id, session):
        await message.answer(
            "👋 你好，管理员！\n\n"
            "回复任意转发的消息即可回复对应用户。\n"
            "使用 /help 查看更多命令。"
        )
        return
    
    # 检查白名单
    if db_user.is_whitelisted:
        await message.answer(
            "👋 你好！有什么可以帮助你的吗？\n"
            "直接发送消息，我会转达给相关人员。"
        )
        return
    
    # 检查黑名单
    if db_user.is_blacklisted:
        await message.answer("⚠️ 你已被禁止使用此服务。")
        return
    
    # 检查临时封禁
    if VerificationManager.is_temp_banned(db_user):
        remaining = VerificationManager.get_temp_ban_remaining(db_user)
        minutes = remaining // 60
        await message.answer(
            f"⚠️ 由于验证失败次数过多，你已被临时限制。\n"
            f"请在 {minutes} 分钟后再试。"
        )
        return
    
    # 已验证用户
    if db_user.is_verified:
        welcome_msg = await settings_service.get_setting("welcome_message")
        if not welcome_msg:
            welcome_msg = "👋 你好！有什么可以帮助你的吗？\n直接发送消息，我会转达给相关人员。"
        await message.answer(welcome_msg)
        return
    
    # 需要验证
    await start_verification(message, session, db_user)


async def start_verification(message: Message, session: AsyncSession, db_user: User):
    """开始验证流程"""
    user_service = UserService(session)
    settings_service = SettingsService(session)
    
    # 获取验证类型
    v_type = await settings_service.get_setting("verification_type") or settings.VERIFICATION_TYPE
    
    if v_type == "math":
        question, answer = VerificationManager.generate_math_question()
        keyboard = VerificationManager.generate_math_keyboard(answer)
        verification_code = answer
    else:
        question = None
        keyboard = VerificationManager.generate_button_keyboard()
        verification_code = "human"
    
    # 更新用户验证信息
    await user_service.set_verification(
        db_user,
        code=verification_code,
        expires=VerificationManager.get_verification_expires()
    )
    
    # 发送验证消息
    text = VerificationManager.get_verification_message(v_type, question)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("verify_"))
async def handle_verification(callback: CallbackQuery, session: AsyncSession, db_user: User):
    """处理验证回调"""
    user_service = UserService(session)
    stats_service = StatsService(session)
    
    answer = callback.data.replace("verify_", "")
    
    try:
        # 先回应回调，避免超时
        await callback.answer()
    except Exception:
        pass  # 忽略回调超时错误
    
    # 检查是否超时
    if VerificationManager.is_verification_expired(db_user):
        try:
            await callback.message.edit_text(
                "⏰ 验证已超时，请发送任意消息重新开始验证。"
            )
        except Exception:
            pass
        return
    
    # 检查答案
    if answer == db_user.verification_code:
        # 验证成功
        await user_service.set_verified(db_user, True)
        await user_service.reset_verification_fails(db_user)
        await stats_service.increment_verification_success()
        
        try:
            await callback.message.edit_text(
                "✅ 验证成功！\n\n"
                "现在你可以直接发送消息了，我会转达给相关人员。"
            )
        except Exception:
            await callback.message.answer(
                "✅ 验证成功！\n\n"
                "现在你可以直接发送消息了，我会转达给相关人员。"
            )
    else:
        # 验证失败
        await user_service.increment_verification_fails(db_user)
        await stats_service.increment_verification_attempt()
        
        if VerificationManager.should_temp_ban(db_user):
            # 临时封禁
            await user_service.set_temp_ban(
                db_user,
                VerificationManager.get_temp_ban_until()
            )
            minutes = settings.TEMP_BAN_DURATION // 60
            try:
                await callback.message.edit_text(
                    f"❌ 验证失败次数过多，你已被临时限制 {minutes} 分钟。"
                )
            except Exception:
                await callback.message.answer(
                    f"❌ 验证失败次数过多，你已被临时限制 {minutes} 分钟。"
                )
        else:
            remaining = settings.MAX_VERIFICATION_FAILS - db_user.verification_fails
            try:
                await callback.message.edit_text(
                    f"❌ 回答错误，请重试。\n"
                    f"剩余尝试次数：{remaining}\n\n"
                    "发送任意消息重新开始验证。"
                )
            except Exception:
                await callback.message.answer(
                    f"❌ 回答错误，请重试。\n"
                    f"剩余尝试次数：{remaining}\n\n"
                    "发送任意消息重新开始验证。"
                )


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession):
    """帮助命令"""
    if await is_admin_db(message.from_user.id, session):
        text = (
            "📖 <b>管理员命令</b>\n\n"
            "/start - 开始\n"
            "/help - 帮助信息\n"
            "/stats - 查看统计\n"
            "/r <用户ID> <消息> - 回复用户\n"
            "/block <用户ID> - 拉黑用户\n"
            "/unblock <用户ID> - 解除拉黑\n"
            "/whitelist <用户ID> - 添加白名单\n"
            "/broadcast <消息> - 群发消息\n\n"
            "💡 TG用户：直接回复转发的消息\n"
            "💡 Web用户：使用 /r 命令回复"
        )
    else:
        text = (
            "📖 <b>使用帮助</b>\n\n"
            "直接发送消息即可，支持：\n"
            "• 文字消息\n"
            "• 图片\n"
            "• 视频\n"
            "• 文件\n"
            "• 语音消息\n\n"
            "我会将你的消息转达给相关人员。"
        )
    
    await message.answer(text)


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession):
    """统计命令（管理员）"""
    if not await is_admin_db(message.from_user.id, session):
        return
    
    stats_service = StatsService(session)
    stats = await stats_service.get_today_stats()
    
    text = (
        "📊 <b>今日统计</b>\n\n"
        f"• 新用户：{stats.get('new_users', 0)}\n"
        f"• 总消息：{stats.get('total_messages', 0)}\n"
        f"• 收到消息：{stats.get('incoming_messages', 0)}\n"
        f"• 发出消息：{stats.get('outgoing_messages', 0)}\n"
        f"• 验证尝试：{stats.get('verification_attempts', 0)}\n"
        f"• 验证成功：{stats.get('verification_success', 0)}\n"
        f"• 拦截消息：{stats.get('blocked_messages', 0)}"
    )
    
    await message.answer(text)


@router.message(Command("block"))
async def cmd_block(message: Message, session: AsyncSession):
    """拉黑用户命令"""
    if not await is_admin_db(message.from_user.id, session):
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("用法：/block <用户ID> [原因]")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ 无效的用户 ID")
        return
    
    reason = args[2] if len(args) > 2 else None
    
    user_service = UserService(session)
    user = await user_service.get_user_by_tg_id(target_id)
    
    if not user:
        await message.answer("❌ 用户不存在")
        return
    
    await user_service.set_blacklist(user, True, reason)
    await message.answer(f"✅ 已将用户 {target_id} 加入黑名单")


@router.message(Command("unblock"))
async def cmd_unblock(message: Message, session: AsyncSession):
    """解除拉黑命令"""
    if not await is_admin_db(message.from_user.id, session):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("用法：/unblock <用户ID>")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ 无效的用户 ID")
        return
    
    user_service = UserService(session)
    user = await user_service.get_user_by_tg_id(target_id)
    
    if not user:
        await message.answer("❌ 用户不存在")
        return
    
    await user_service.set_blacklist(user, False)
    await message.answer(f"✅ 已将用户 {target_id} 移出黑名单")


@router.message(Command("whitelist"))
async def cmd_whitelist(message: Message, session: AsyncSession):
    """添加白名单命令"""
    if not await is_admin_db(message.from_user.id, session):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("用法：/whitelist <用户ID>")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ 无效的用户 ID")
        return
    
    user_service = UserService(session)
    user = await user_service.get_user_by_tg_id(target_id)
    
    if not user:
        await message.answer("❌ 用户不存在")
        return
    
    await user_service.set_whitelist(user, True)
    await message.answer(f"✅ 已将用户 {target_id} 加入白名单")


@router.message(Command("r"))
async def cmd_reply(message: Message, session: AsyncSession):
    """回复用户命令（用于回复Web客户或TG用户）"""
    if not await is_admin_db(message.from_user.id, session):
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "用法：/r <用户ID> <消息内容>\n"
            "例如：/r 123 你好，请问有什么可以帮您？"
        )
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ 无效的用户 ID")
        return
    
    reply_content = args[2]
    
    user_service = UserService(session)
    message_service = MessageService(session)
    stats_service = StatsService(session)
    admin_service = AdminService(session)
    
    # 获取当前管理员
    admin = await admin_service.get_admin_by_tg_id(message.from_user.id)
    admin_id = admin.id if admin else None
    
    # 先按数据库ID查找
    user = await user_service.get_user_by_id(target_id)
    
    if not user:
        # 再按TG ID查找
        user = await user_service.get_user_by_tg_id(target_id)
    
    if not user:
        await message.answer("❌ 用户不存在")
        return
    
    bot: Bot = message.bot
    
    try:
        # 如果是TG用户，发送TG消息
        if user.source == "telegram" and user.tg_id:
            await bot.send_message(user.tg_id, reply_content)
        
        # 记录消息（无论是TG还是Web用户）
        await message_service.create_message(
            user=user,
            direction="out",
            message_type="text",
            content=reply_content,
            admin_id=admin_id
        )
        
        await stats_service.increment_outgoing_message()
        
        source_icon = "🌐" if user.source == "web" else "🤖"
        await message.answer(f"✅ 已发送给 {source_icon} {user.display_name}")
        
    except Exception as e:
        logger.error(f"回复用户失败: {e}")
        await message.answer(f"❌ 发送失败：{str(e)}")


@router.message(F.reply_to_message)
async def handle_admin_reply(message: Message, session: AsyncSession):
    """处理管理员回复"""
    if not await is_admin_db(message.from_user.id, session):
        # 非管理员按普通消息处理
        await handle_user_message(message, session)
        return
    
    # 获取原消息
    reply_msg = message.reply_to_message
    message_service = MessageService(session)
    user_service = UserService(session)
    target_user = None
    
    # 首先尝试从数据库通过转发消息ID查找（传入当前管理员ID）
    original = await message_service.get_message_by_forwarded_id(
        reply_msg.message_id,
        admin_tg_id=message.from_user.id
    )
    if original:
        target_user = original.user
    elif reply_msg.forward_from:
        # 如果是转发的消息，获取转发来源用户
        target_user = await user_service.get_user_by_tg_id(reply_msg.forward_from.id)
    elif reply_msg.forward_sender_name:
        # 用户隐藏了转发来源
        pass
    
    if not target_user:
        await message.answer("❌ 无法确定回复对象，请回复转发的消息或Web客户消息")
        return
    
    bot: Bot = message.bot
    admin_service = AdminService(session)
    admin = await admin_service.get_admin_by_tg_id(message.from_user.id)
    admin_id = admin.id if admin else None
    
    try:
        # 判断是TG用户还是Web用户
        if target_user.source == "telegram" and target_user.tg_id:
            # TG用户：发送TG消息
            if message.text:
                await bot.send_message(target_user.tg_id, message.text)
            elif message.photo:
                await bot.send_photo(
                    target_user.tg_id,
                    message.photo[-1].file_id,
                    caption=message.caption
                )
            elif message.video:
                await bot.send_video(
                    target_user.tg_id,
                    message.video.file_id,
                    caption=message.caption
                )
            elif message.document:
                await bot.send_document(
                    target_user.tg_id,
                    message.document.file_id,
                    caption=message.caption
                )
            elif message.voice:
                await bot.send_voice(target_user.tg_id, message.voice.file_id)
            elif message.sticker:
                await bot.send_sticker(target_user.tg_id, message.sticker.file_id)
            else:
                await message.answer("❌ 不支持的消息类型")
                return
        
        # 记录消息（无论是TG还是Web用户）
        await message_service.create_message(
            user=target_user,
            direction="out",
            message_type=get_message_type(message),
            content=message.text or message.caption,
            tg_message_id=message.message_id,
            admin_id=admin_id
        )
        
        # 更新统计
        stats_service = StatsService(session)
        await stats_service.increment_outgoing_message()
        
        # 显示回复成功信息
        source_icon = "🌐" if target_user.source == "web" else "🤖"
        await message.answer(f"✅ 已发送给 {source_icon} {target_user.display_name}")
        
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        await message.answer(f"❌ 发送失败：{str(e)}")


@router.message()
async def handle_user_message(message: Message, session: AsyncSession, db_user: User = None):
    """处理用户消息"""
    # 管理员消息不处理
    if await is_admin_db(message.from_user.id, session):
        return
    
    if not db_user:
        user_service = UserService(session)
        db_user = await user_service.get_or_create_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    
    # 检查黑名单
    if db_user.is_blacklisted:
        await message.answer("⚠️ 你已被禁止使用此服务。")
        return
    
    # 检查临时封禁
    if VerificationManager.is_temp_banned(db_user):
        remaining = VerificationManager.get_temp_ban_remaining(db_user)
        minutes = remaining // 60
        await message.answer(
            f"⚠️ 你已被临时限制，请在 {minutes} 分钟后再试。"
        )
        return
    
    # 检查是否需要验证
    if not db_user.is_verified and not db_user.is_whitelisted:
        # 检查是否有进行中的验证（未超时）
        if db_user.verification_code and not VerificationManager.is_verification_expired(db_user):
            # 有进行中的验证，提示用户点击按钮
            await message.answer("⏳ 请点击上方验证按钮完成验证。")
            return
        
        # 开始新的验证
        await start_verification(message, session, db_user)
        return
    
    # 敏感词检测
    sensitive_service = SensitiveWordService(session)
    stats_service = StatsService(session)
    
    content = message.text or message.caption or ""
    
    # 过滤机器人命令（以/开头的消息）
    if content.startswith("/"):
        # 忽略命令消息，不转发给管理员
        return
    
    triggered_words, action = await sensitive_service.check_content(content)
    
    if triggered_words and action == "block":
        await stats_service.increment_blocked_message()
        await message.answer("⚠️ 你的消息包含敏感内容，已被拦截。")
        return
    
    # 转发给所有管理员
    bot: Bot = message.bot
    notification_service = NotificationService(session)
    settings_service = SettingsService(session)
    
    # 获取管理员列表（从数据库）
    from app.services.admin import AdminService
    admin_service = AdminService(session)
    admin_ids = await admin_service.get_admin_tg_ids()
    
    # 如果数据库没有管理员，使用配置文件
    if not admin_ids:
        admin_ids = settings.admin_id_list
    
    # 检查是否在静音时段
    is_quiet = await notification_service.is_quiet_hours()
    
    # 存储每个管理员收到的转发消息ID
    forwarded_message_ids = {}
    
    for admin_id in admin_ids:
        try:
            if not is_quiet:
                forwarded_msg = await message.forward(admin_id)
                forwarded_message_ids[str(admin_id)] = forwarded_msg.message_id
                
                # 如果触发敏感词，发送警告
                if triggered_words:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ 上条消息触发敏感词：{', '.join(triggered_words)}"
                    )
        except Exception as e:
            logger.error(f"转发消息给管理员 {admin_id} 失败: {e}")
    
    # 记录消息
    message_service = MessageService(session)
    user_service = UserService(session)
    
    await message_service.create_message(
        user=db_user,
        direction="in",
        message_type=get_message_type(message),
        content=content,
        tg_message_id=message.message_id,
        forwarded_message_ids=forwarded_message_ids,
        triggered_sensitive=bool(triggered_words),
        sensitive_words=triggered_words
    )
    
    # 更新每日统计
    await stats_service.increment_incoming_message()
    
    # 自动回复检查
    if await settings_service.get_setting("auto_reply_enabled") == "true":
        auto_reply_msg = await settings_service.get_setting("auto_reply_message")
        if auto_reply_msg:
            await message.answer(auto_reply_msg)


def get_message_type(message: Message) -> str:
    """获取消息类型"""
    if message.text:
        return "text"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.document:
        return "document"
    elif message.voice:
        return "voice"
    elif message.sticker:
        return "sticker"
    else:
        return "unknown"


def setup_handlers(dp: Dispatcher):
    """设置处理器"""
    dp.include_router(router)
