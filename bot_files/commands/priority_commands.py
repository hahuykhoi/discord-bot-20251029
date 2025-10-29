"""
Priority user management commands
"""
import discord
from discord.ext import commands
import logging
from .base import BaseCommand

logger = logging.getLogger(__name__)

class PriorityCommands(BaseCommand):
    """Class chứa các commands quản lý priority users"""
    
    def register_commands(self):
        """Register priority management commands"""
        
        @self.bot.command(name='addpriority')
        async def add_priority(ctx, user_id: int):
            """
            Thêm user ID vào danh sách priority (bypass rate limiting)
            
            Usage: !addpriority <user_id>
            """
            await self._add_priority_impl(ctx, user_id)
        
        @self.bot.command(name='removepriority')
        async def remove_priority(ctx, user_id: int):
            """
            Xóa user ID khỏi danh sách priority
            
            Usage: !removepriority <user_id>
            """
            await self._remove_priority_impl(ctx, user_id)
        
        @self.bot.command(name='listpriority')
        async def list_priority(ctx):
            """
            Hiển thị danh sách priority user IDs
            
            Usage: !listpriority
            """
            await self._list_priority_impl(ctx)
    
    async def _add_priority_impl(self, ctx, user_id: int):
        """
        Implementation thực tế của addpriority command
        """
        # Chỉ server administrator mới có thể thêm priority
        if not ctx.author.guild_permissions.administrator:
            await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Administrator mới có thể sử dụng lệnh này!", mention_author=True)
            return
        
        if user_id in self.bot_instance.priority_users:
            await ctx.reply(f"{ctx.author.mention} ❌ User ID `{user_id}` đã có trong danh sách priority!", mention_author=True)
            return
        
        self.bot_instance.priority_users.add(user_id)  # Set operation O(1)
        await self._save_priority_users()
        
        embed = discord.Embed(
            title="⚡ Đã thêm Priority User",
            description=f"User ID `{user_id}` đã được thêm vào danh sách priority.",
            color=discord.Color.gold()
        )
        embed.add_field(name="Quyền được cấp", value="Bypass rate limiting - commands chạy ngay lập tức", inline=False)
        embed.add_field(name="Tổng priority users", value=f"{len(self.bot_instance.priority_users)} người", inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Priority user ID {user_id} được thêm bởi {ctx.author} ({ctx.author.id})")
    
    async def _remove_priority_impl(self, ctx, user_id: int):
        """
        Implementation thực tế của removepriority command
        """
        # Chỉ server administrator mới có thể xóa priority
        if not ctx.author.guild_permissions.administrator:
            await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Administrator mới có thể sử dụng lệnh này!", mention_author=True)
            return
        
        if user_id not in self.bot_instance.priority_users:
            await ctx.reply(f"{ctx.author.mention} ❌ User ID `{user_id}` không có trong danh sách priority!", mention_author=True)
            return
        
        self.bot_instance.priority_users.discard(user_id)  # Set operation O(1)
        await self._save_priority_users()
        
        embed = discord.Embed(
            title="⚡ Đã xóa Priority User",
            description=f"User ID `{user_id}` đã được xóa khỏi danh sách priority.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Tổng priority users còn lại", value=f"{len(self.bot_instance.priority_users)} người", inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Priority user ID {user_id} được xóa bởi {ctx.author} ({ctx.author.id})")
    
    async def _list_priority_impl(self, ctx):
        """
        Implementation thực tế của listpriority command
        """
        # Kiểm tra quyền sử dụng dynamic permission system
        if hasattr(self.bot_instance, 'permission_manager'):
            has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'listpriority')
            if not has_permission:
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền xem danh sách priority users!", mention_author=True)
                return
        else:
            # Fallback: Kiểm tra quyền admin nếu không có permission system
            if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền xem danh sách priority users!", mention_author=True)
                return
        
        if not self.bot_instance.priority_users:
            embed = discord.Embed(
                title="⚡ Danh sách Priority Users",
                description="Chưa có priority user nào được thêm vào danh sách.",
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="⚡ Danh sách Priority Users",
                description=f"Có **{len(self.bot_instance.priority_users)}** priority users trong danh sách:",
                color=discord.Color.gold()
            )
            
            priority_list = "\n".join([f"• `{user_id}`" for user_id in self.bot_instance.priority_users])
            embed.add_field(name="User IDs", value=priority_list, inline=False)
            embed.add_field(name="Quyền", value="Bypass rate limiting - commands chạy ngay lập tức", inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def _save_priority_users(self):
        """
        Lưu danh sách priority users vào file JSON
        """
        import json
        priority_file = self.bot_instance.config.get('priority_file', 'data/priority.json')
        try:
            priority_data = {
                "priority_users": list(self.bot_instance.priority_users),
                "description": "Danh sách User IDs được bypass rate limiting"
            }
            with open(priority_file, 'w', encoding='utf-8') as f:
                json.dump(priority_data, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu priority users thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu priority users: {e}")
