"""
VIP Message Management Commands - Send, Delete, Purge Messages
Ported from proj.py VIP Admin Bot
"""
import discord
from discord.ext import commands
import logging
from datetime import datetime
from pathlib import Path
from .base import BaseCommand

logger = logging.getLogger(__name__)

class MessageCommands(BaseCommand):
    """Class chứa các commands quản lý tin nhắn VIP"""
    
    def register_commands(self):
        """Register message management commands"""
        
        @self.bot.command(name='vipsend')
        async def vip_send(ctx, channel_id: int, *, message: str):
            """
            Gửi tin nhắn đến channel cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipsend <channel_id> <message>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_send_impl(ctx, channel_id, message)
        
        @self.bot.command(name='vipsendFile')
        async def vip_send_file(ctx, channel_id: int, filepath: str, *, caption: str = None):
            """
            Gửi file đến channel cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipsendFile <channel_id> <filepath> [caption]
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_send_file_impl(ctx, channel_id, filepath, caption)
        
        @self.bot.command(name='vipdelete')
        async def vip_delete(ctx, channel_id: int, message_id: int):
            """
            Xóa tin nhắn cụ thể trong channel (Chỉ Supreme Admin)
            
            Usage: ;vipdelete <channel_id> <message_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_delete_impl(ctx, channel_id, message_id)
        
        @self.bot.command(name='vippurge')
        async def vip_purge(ctx, channel_id: int, limit: int):
            """
            Xóa nhiều tin nhắn trong channel (Chỉ Supreme Admin)
            
            Usage: ;vippurge <channel_id> <limit>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_purge_impl(ctx, channel_id, limit)
        
        @self.bot.command(name='vipdm')
        async def vip_dm(ctx, user_id: int, *, message: str):
            """
            Gửi DM đến user cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipdm <user_id> <message>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_dm_impl(ctx, user_id, message)
    
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
    
    async def _vip_send_impl(self, ctx, channel_id: int, message: str):
        """Implementation của VIP send command"""
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            
            sent_message = await channel.send(message)
            
            embed = self.vip_embed(
                "✅ VIP Send Message Thành Công",
                f"**Channel:** {channel.name} (ID: {channel_id})\n"
                f"**Guild:** {channel.guild.name}\n"
                f"**Message ID:** {sent_message.id}\n"
                f"**Content:** {message[:100]}{'...' if len(message) > 100 else ''}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP send to {channel_id}: {message[:200]}")
            logger.info(f"VIP send message to {channel_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền gửi tin nhắn trong channel này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy channel", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP send error: {e}")
    
    async def _vip_send_file_impl(self, ctx, channel_id: int, filepath: str, caption: str):
        """Implementation của VIP send file command"""
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            
            file_path = Path(filepath)
            if not file_path.exists():
                await ctx.reply(embed=self.vip_embed("Error", "File không tồn tại", color=0xFF5A5F))
                return
            
            # Kiểm tra kích thước file (Discord limit 8MB cho bots)
            file_size = file_path.stat().st_size
            if file_size > 8 * 1024 * 1024:  # 8MB
                await ctx.reply(embed=self.vip_embed("Error", "File quá lớn (>8MB)", color=0xFF5A5F))
                return
            
            sent_message = await channel.send(content=caption, file=discord.File(str(file_path)))
            
            embed = self.vip_embed(
                "✅ VIP Send File Thành Công",
                f"**Channel:** {channel.name} (ID: {channel_id})\n"
                f"**Guild:** {channel.guild.name}\n"
                f"**File:** {file_path.name}\n"
                f"**Size:** {file_size / 1024:.1f} KB\n"
                f"**Message ID:** {sent_message.id}"
            )
            if caption:
                embed.add_field(name="Caption", value=caption[:500], inline=False)
            
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP sendfile {filepath} -> {channel_id}")
            logger.info(f"VIP send file to {channel_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền gửi file trong channel này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy channel", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP send file error: {e}")
    
    async def _vip_delete_impl(self, ctx, channel_id: int, message_id: int):
        """Implementation của VIP delete command"""
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            
            # Lưu thông tin trước khi xóa
            message_content = message.content[:100] + ('...' if len(message.content) > 100 else '')
            message_author = str(message.author)
            
            await message.delete()
            
            embed = self.vip_embed(
                "🗑️ VIP Delete Message Thành Công",
                f"**Channel:** {channel.name} (ID: {channel_id})\n"
                f"**Guild:** {channel.guild.name}\n"
                f"**Message ID:** {message_id}\n"
                f"**Author:** {message_author}\n"
                f"**Content:** {message_content}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP deleted message {message_id} in {channel_id}")
            logger.info(f"VIP delete message {message_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền xóa tin nhắn trong channel này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy channel hoặc message", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP delete error: {e}")
    
    async def _vip_purge_impl(self, ctx, channel_id: int, limit: int):
        """Implementation của VIP purge command"""
        try:
            if limit <= 0 or limit > 100:
                await ctx.reply(embed=self.vip_embed("Error", "Limit phải từ 1-100", color=0xFF5A5F))
                return
            
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            
            deleted = await channel.purge(limit=limit)
            
            embed = self.vip_embed(
                "🧹 VIP Purge Messages Thành Công",
                f"**Channel:** {channel.name} (ID: {channel_id})\n"
                f"**Guild:** {channel.guild.name}\n"
                f"**Deleted:** {len(deleted)} messages\n"
                f"**Requested:** {limit} messages"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP purged {len(deleted)} messages in {channel_id}")
            logger.info(f"VIP purge {len(deleted)} messages in {channel_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền xóa tin nhắn trong channel này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy channel", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP purge error: {e}")
    
    async def _vip_dm_impl(self, ctx, user_id: int, message: str):
        """Implementation của VIP DM command"""
        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(message)
            
            embed = self.vip_embed(
                "✅ VIP Send DM Thành Công",
                f"**User:** {user} (ID: {user_id})\n"
                f"**Message:** {message[:200]}{'...' if len(message) > 200 else ''}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP sent DM to {user_id}: {message[:200]}")
            logger.info(f"VIP send DM to {user_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Không thể gửi DM cho user này (có thể đã chặn bot)", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy user", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP DM error: {e}")
