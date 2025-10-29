"""
Base class cho tất cả commands
"""
import discord
from discord.ext import commands
import logging
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

class BaseCommand:
    """Base class cho tất cả commands"""
    
    def __init__(self, bot_instance):
        """
        Khởi tạo base command
        
        Args:
            bot_instance: Instance của AutoReplyBot
        """
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
    
    def rate_limit_10s(self, func):
        """
        Decorator để áp dụng rate limiting 10 giây cho command
        """
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            current_time = datetime.now()
            user_id = ctx.author.id
            
            # Kiểm tra rate limit
            if self.bot_instance.is_user_rate_limited(user_id, current_time):
                reset_time = self.bot_instance.get_rate_limit_reset_time(user_id, current_time)
                await ctx.reply(
                    f"{ctx.author.mention} ⏰ Bạn đang bị rate limit! "
                    f"Vui lòng chờ **{reset_time}** giây trước khi sử dụng lệnh tiếp theo.",
                    mention_author=True
                )
                return
            
            # Thêm command vào lịch sử
            self.bot_instance.add_user_command(user_id, current_time)
            
            # Thực thi command
            await func(ctx, *args, **kwargs)
        
        return wrapper
    
    async def execute_with_rate_limit(self, ctx, command_func, *args, **kwargs):
        """
        Wrapper để thực thi command với rate limiting (legacy method)
        
        Args:
            ctx: Discord context
            command_func: Function cần thực thi
            *args, **kwargs: Arguments cho function
        """
        current_time = datetime.now()
        user_id = ctx.author.id
        
        # Kiểm tra rate limit
        if self.bot_instance.is_user_rate_limited(user_id, current_time):
            reset_time = self.bot_instance.get_rate_limit_reset_time(user_id, current_time)
            await ctx.reply(
                f"{ctx.author.mention} ⏰ Bạn đang bị rate limit! "
                f"Vui lòng chờ **{reset_time}** giây trước khi sử dụng lệnh tiếp theo.",
                mention_author=True
            )
            return
        
        # Thêm command vào lịch sử
        self.bot_instance.add_user_command(user_id, current_time)
        
        # Thực thi command
        await command_func(*args, **kwargs)
    
    def has_warn_permission(self, user_id: int, guild_permissions) -> bool:
        """
        Kiểm tra quyền warn
        
        Args:
            user_id: ID của user
            guild_permissions: Quyền của user trong server
            
        Returns:
            bool: True nếu có quyền
        """
        return self.bot_instance.has_warn_permission(user_id, guild_permissions)
    
    async def get_muted_role_cached(self, guild: discord.Guild):
        """
        Get cached muted role
        
        Args:
            guild: Discord guild
            
        Returns:
            Optional[discord.Role]: Muted role hoặc None
        """
        return await self.bot_instance.get_muted_role_cached(guild)
    
    def register_commands(self):
        """
        Method để register commands - phải được override
        """
        raise NotImplementedError("Subclass must implement register_commands method")
