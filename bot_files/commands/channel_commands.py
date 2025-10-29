"""
VIP Channel Management Commands - Create/Delete Channels, Categories, Role Management
Ported from proj.py VIP Admin Bot
"""
import discord
from discord.ext import commands
import logging
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class ChannelCommands(BaseCommand):
    """Class chứa các commands quản lý channel và category VIP"""
    
    def register_commands(self):
        """Register channel management commands"""
        
        @self.bot.command(name='vipcreateChannel')
        async def vip_create_channel(ctx, guild_id: int, name: str, channel_type: str, category_id: int = None):
            """
            Tạo channel mới trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipcreateChannel <guild_id> <name> <text|voice> [category_id]
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_create_channel_impl(ctx, guild_id, name, channel_type, category_id)
        
        @self.bot.command(name='vipdeleteChannel')
        async def vip_delete_channel(ctx, channel_id: int):
            """
            Xóa channel theo ID (Chỉ Supreme Admin)
            
            Usage: ;vipdeleteChannel <channel_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_delete_channel_impl(ctx, channel_id)
        
        @self.bot.command(name='vipcreateCategory')
        async def vip_create_category(ctx, guild_id: int, *, name: str):
            """
            Tạo category mới trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipcreateCategory <guild_id> <name>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_create_category_impl(ctx, guild_id, name)
        
        @self.bot.command(name='vipdeleteCategory')
        async def vip_delete_category(ctx, category_id: int):
            """
            Xóa category theo ID (Chỉ Supreme Admin)
            
            Usage: ;vipdeleteCategory <category_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_delete_category_impl(ctx, category_id)
        
        @self.bot.command(name='vipgiveRole')
        async def vip_give_role(ctx, guild_id: int, user_id: int, *, role_name_or_id: str):
            """
            Thêm role cho user trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipgiveRole <guild_id> <user_id> <role_id_or_name>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_give_role_impl(ctx, guild_id, user_id, role_name_or_id)
        
        @self.bot.command(name='viptakeRole')
        async def vip_take_role(ctx, guild_id: int, user_id: int, *, role_name_or_id: str):
            """
            Xóa role khỏi user trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;viptakeRole <guild_id> <user_id> <role_id_or_name>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_take_role_impl(ctx, guild_id, user_id, role_name_or_id)
    
    def vip_embed(self, title: str, description: str = "", color: int = 0xFFD700):
        """Tạo VIP embed với style đặc biệt"""
        e = discord.Embed(title=title, description=description or "", color=color)
        e.set_footer(text="VIP Admin Bot")
        e.timestamp = datetime.utcnow()
        return e
    
    def append_action_log(self, text: str):
        """Log action to file"""
        try:
            with open("actions.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.utcnow().isoformat()} - {text}\n")
        except Exception:
            logger.exception("Failed to write actions.log")
    
    async def _vip_create_channel_impl(self, ctx, guild_id: int, name: str, channel_type: str, category_id: int):
        """Implementation của VIP create channel command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            category = guild.get_channel(category_id) if category_id else None
            
            if channel_type.lower() == "voice":
                channel = await guild.create_voice_channel(name, category=category)
            else:
                channel = await guild.create_text_channel(name, category=category)
            
            embed = self.vip_embed(
                "✅ VIP Create Channel Thành Công",
                f"**Channel:** {channel.name} (ID: {channel.id})\n"
                f"**Type:** {channel_type.title()}\n"
                f"**Guild:** {guild.name} (ID: {guild_id})\n"
                f"**Category:** {category.name if category else 'Không có'}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP created channel {channel.name} ({channel.id}) in {guild_id}")
            logger.info(f"VIP create channel: {channel.name} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền tạo channel trong guild này", color=0xFF5A5F))
        except discord.HTTPException as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi HTTP: {str(e)}", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP create channel error: {e}")
    
    async def _vip_delete_channel_impl(self, ctx, channel_id: int):
        """Implementation của VIP delete channel command"""
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            guild_name = channel.guild.name
            channel_name = channel.name
            
            await channel.delete()
            
            embed = self.vip_embed(
                "🗑️ VIP Delete Channel Thành Công",
                f"**Channel:** {channel_name} (ID: {channel_id})\n"
                f"**Guild:** {guild_name}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP deleted channel {channel_id}")
            logger.info(f"VIP delete channel: {channel_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền xóa channel này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy channel", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP delete channel error: {e}")
    
    async def _vip_create_category_impl(self, ctx, guild_id: int, name: str):
        """Implementation của VIP create category command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            category = await guild.create_category(name)
            
            embed = self.vip_embed(
                "✅ VIP Create Category Thành Công",
                f"**Category:** {category.name} (ID: {category.id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP created category {category.name} ({category.id}) in {guild_id}")
            logger.info(f"VIP create category: {category.name} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền tạo category trong guild này", color=0xFF5A5F))
        except discord.HTTPException as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi HTTP: {str(e)}", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP create category error: {e}")
    
    async def _vip_delete_category_impl(self, ctx, category_id: int):
        """Implementation của VIP delete category command"""
        try:
            channel = self.bot.get_channel(category_id)
            if channel and isinstance(channel, discord.CategoryChannel):
                guild_name = channel.guild.name
                category_name = channel.name
                
                await channel.delete()
                
                embed = self.vip_embed(
                    "🗑️ VIP Delete Category Thành Công",
                    f"**Category:** {category_name} (ID: {category_id})\n"
                    f"**Guild:** {guild_name}"
                )
                await ctx.reply(embed=embed)
                
                self.append_action_log(f"VIP deleted category {category_id}")
                logger.info(f"VIP delete category: {category_id} by {ctx.author.id}")
            else:
                await ctx.reply(embed=self.vip_embed("Error", "Không phải category hoặc ID không hợp lệ", color=0xFF5A5F))
                
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền xóa category này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy category", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP delete category error: {e}")
    
    async def _vip_give_role_impl(self, ctx, guild_id: int, user_id: int, role_name_or_id: str):
        """Implementation của VIP give role command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            
            # Tìm role theo ID hoặc tên
            role = None
            if role_name_or_id.isdigit():
                role = discord.utils.get(guild.roles, id=int(role_name_or_id))
            if role is None:
                role = discord.utils.get(guild.roles, name=role_name_or_id)
            
            if role is None:
                await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy role", color=0xFF5A5F))
                return
            
            await member.add_roles(role)
            
            embed = self.vip_embed(
                "✅ VIP Give Role Thành Công",
                f"**User:** {member} (ID: {user_id})\n"
                f"**Role:** {role.name} (ID: {role.id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP added role {role.name}({role.id}) to {user_id} in {guild_id}")
            logger.info(f"VIP give role: {role.name} to {user_id} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền thêm role trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy member hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP give role error: {e}")
    
    async def _vip_take_role_impl(self, ctx, guild_id: int, user_id: int, role_name_or_id: str):
        """Implementation của VIP take role command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            
            # Tìm role theo ID hoặc tên
            role = None
            if role_name_or_id.isdigit():
                role = discord.utils.get(guild.roles, id=int(role_name_or_id))
            if role is None:
                role = discord.utils.get(guild.roles, name=role_name_or_id)
            
            if role is None:
                await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy role", color=0xFF5A5F))
                return
            
            await member.remove_roles(role)
            
            embed = self.vip_embed(
                "✅ VIP Take Role Thành Công",
                f"**User:** {member} (ID: {user_id})\n"
                f"**Role:** {role.name} (ID: {role.id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP removed role {role.name}({role.id}) from {user_id} in {guild_id}")
            logger.info(f"VIP take role: {role.name} from {user_id} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền xóa role trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy member hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP take role error: {e}")
