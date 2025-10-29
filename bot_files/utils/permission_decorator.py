# -*- coding: utf-8 -*-
"""
Permission Decorator - Decorator để kiểm tra quyền trước khi thực thi lệnh
"""
import discord
from discord.ext import commands
import functools
import logging

logger = logging.getLogger(__name__)

def check_permission():
    """
    Decorator để kiểm tra quyền lệnh
    Sử dụng hệ thống permission động
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Tìm ctx trong args
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if not ctx:
                logger.error("Không tìm thấy Context trong permission decorator")
                return await func(*args, **kwargs)
            
            # Lấy tên lệnh
            command_name = ctx.command.name if ctx.command else "unknown"
            
            # Kiểm tra xem bot có permission system không
            if not hasattr(ctx.bot, 'permission_manager'):
                # Nếu không có permission system, cho phép tất cả
                return await func(*args, **kwargs)
            
            permission_manager = ctx.bot.permission_manager
            
            # Kiểm tra quyền
            has_permission, reason = permission_manager.check_command_permission(ctx, command_name)
            
            if not has_permission:
                # Tạo embed thông báo không có quyền
                error_embed = discord.Embed(
                    title="❌ Không có quyền",
                    description=reason,
                    color=discord.Color.red()
                )
                
                required_level = permission_manager.get_command_permission(command_name)
                
                error_embed.add_field(
                    name="📋 Chi tiết",
                    value=(
                        f"**Lệnh:** `{command_name}`\n"
                        f"**Yêu cầu quyền:** `{required_level}`"
                    ),
                    inline=False
                )
                
                # Giải thích cách có quyền
                if required_level == "supreme_admin":
                    how_to_get = "Liên hệ Supreme Admin để được cấp quyền"
                elif required_level == "admin":
                    how_to_get = "Liên hệ Admin hoặc Supreme Admin để được cấp quyền"
                else:
                    how_to_get = "Lệnh này dành cho tất cả user"
                
                error_embed.add_field(
                    name="💡 Cách có quyền",
                    value=how_to_get,
                    inline=False
                )
                
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            # Có quyền, thực thi lệnh
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_permission(level):
    """
    Decorator để yêu cầu permission level cụ thể
    
    Args:
        level (str): "supreme_admin", "admin", hoặc "user"
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Tìm ctx trong args
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if not ctx:
                logger.error("Không tìm thấy Context trong require_permission decorator")
                return await func(*args, **kwargs)
            
            user_id = ctx.author.id
            
            # Kiểm tra quyền theo level
            if level == "supreme_admin":
                if user_id != ctx.bot.supreme_admin_id:
                    error_embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Lệnh này chỉ dành cho Supreme Admin!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=error_embed, mention_author=True)
                    return
            elif level == "admin":
                if user_id not in ctx.bot.admin_ids and user_id != ctx.bot.supreme_admin_id:
                    error_embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Lệnh này chỉ dành cho Admin trở lên!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=error_embed, mention_author=True)
                    return
            # level == "user" thì ai cũng được dùng
            
            # Có quyền, thực thi lệnh
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
