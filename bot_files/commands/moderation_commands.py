"""
VIP Moderation Commands - Ban, Kick, Timeout, Voice Mute
Ported from proj.py VIP Admin Bot
"""
import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
from .base import BaseCommand

logger = logging.getLogger(__name__)

class ModerationCommands(BaseCommand):
    """Class chứa các commands moderation VIP"""
    
    def register_commands(self):
        """Register moderation commands"""
        
        @self.bot.command(name='vipban')
        async def vip_ban(ctx, guild_id: int, user_id: int, *, reason: str = None):
            """
            Ban user từ guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipban <guild_id> <user_id> [reason]
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_ban_impl(ctx, guild_id, user_id, reason)
        
        @self.bot.command(name='vipunban')
        async def vip_unban(ctx, guild_id: int, user_id: int):
            """
            Unban user từ guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipunban <guild_id> <user_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_unban_impl(ctx, guild_id, user_id)
        
        @self.bot.command(name='vipkick')
        async def vip_kick(ctx, guild_id: int, user_id: int, *, reason: str = None):
            """
            Kick user từ guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipkick <guild_id> <user_id> [reason]
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_kick_impl(ctx, guild_id, user_id, reason)
        
        @self.bot.command(name='viptimeout')
        async def vip_timeout(ctx, guild_id: int, user_id: int, minutes: int):
            """
            Timeout user trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;viptimeout <guild_id> <user_id> <minutes>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_timeout_impl(ctx, guild_id, user_id, minutes)
        
        @self.bot.command(name='vipuntimeout')
        async def vip_untimeout(ctx, guild_id: int, user_id: int):
            """
            Remove timeout user trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipuntimeout <guild_id> <user_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_untimeout_impl(ctx, guild_id, user_id)
        
        @self.bot.command(name='vipvoicemute')
        async def vip_voice_mute(ctx, guild_id: int, user_id: int):
            """
            Voice mute user trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipvoicemute <guild_id> <user_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_voice_mute_impl(ctx, guild_id, user_id)
        
        @self.bot.command(name='vipvoiceunmute')
        async def vip_voice_unmute(ctx, guild_id: int, user_id: int):
            """
            Voice unmute user trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipvoiceunmute <guild_id> <user_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_voice_unmute_impl(ctx, guild_id, user_id)
    
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
    
    async def _vip_ban_impl(self, ctx, guild_id: int, user_id: int, reason: str):
        """Implementation của VIP ban command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            user = await self.bot.fetch_user(user_id)
            await guild.ban(user, reason=reason)
            
            embed = self.vip_embed(
                "🚫 VIP Ban Thành Công",
                f"**User:** {user} (ID: {user_id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})\n"
                f"**Reason:** {reason or 'Không có lý do'}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP banned {user_id} in guild {guild_id} reason={reason}")
            logger.info(f"VIP ban: {user_id} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền ban trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy user hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP ban error: {e}")
    
    async def _vip_unban_impl(self, ctx, guild_id: int, user_id: int):
        """Implementation của VIP unban command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            user = await self.bot.fetch_user(user_id)
            await guild.unban(user)
            
            embed = self.vip_embed(
                "✅ VIP Unban Thành Công",
                f"**User:** {user} (ID: {user_id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP unbanned {user_id} in guild {guild_id}")
            logger.info(f"VIP unban: {user_id} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền unban trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy user hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP unban error: {e}")
    
    async def _vip_kick_impl(self, ctx, guild_id: int, user_id: int, reason: str):
        """Implementation của VIP kick command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            await member.kick(reason=reason)
            
            embed = self.vip_embed(
                "👢 VIP Kick Thành Công",
                f"**User:** {member} (ID: {user_id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})\n"
                f"**Reason:** {reason or 'Không có lý do'}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP kicked {user_id} from guild {guild_id} reason={reason}")
            logger.info(f"VIP kick: {user_id} from {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền kick trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy member hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP kick error: {e}")
    
    async def _vip_timeout_impl(self, ctx, guild_id: int, user_id: int, minutes: int):
        """Implementation của VIP timeout command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            until = datetime.utcnow() + timedelta(minutes=minutes)
            await member.edit(communication_disabled_until=until)
            
            embed = self.vip_embed(
                "⏳ VIP Timeout Thành Công",
                f"**User:** {member} (ID: {user_id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})\n"
                f"**Duration:** {minutes} phút"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP timed out {user_id} in {guild_id} for {minutes}m")
            logger.info(f"VIP timeout: {user_id} in {guild_id} for {minutes}m by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền timeout trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy member hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP timeout error: {e}")
    
    async def _vip_untimeout_impl(self, ctx, guild_id: int, user_id: int):
        """Implementation của VIP untimeout command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            await member.edit(communication_disabled_until=None)
            
            embed = self.vip_embed(
                "✅ VIP Remove Timeout Thành Công",
                f"**User:** {member} (ID: {user_id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP removed timeout for {user_id} in {guild_id}")
            logger.info(f"VIP untimeout: {user_id} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền remove timeout trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy member hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP untimeout error: {e}")
    
    async def _vip_voice_mute_impl(self, ctx, guild_id: int, user_id: int):
        """Implementation của VIP voice mute command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            await member.edit(mute=True)
            
            embed = self.vip_embed(
                "🔇 VIP Voice Mute Thành Công",
                f"**User:** {member} (ID: {user_id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP voice-muted {user_id} in {guild_id}")
            logger.info(f"VIP voice mute: {user_id} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền voice mute trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy member hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP voice mute error: {e}")
    
    async def _vip_voice_unmute_impl(self, ctx, guild_id: int, user_id: int):
        """Implementation của VIP voice unmute command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            await member.edit(mute=False)
            
            embed = self.vip_embed(
                "🔊 VIP Voice Unmute Thành Công",
                f"**User:** {member} (ID: {user_id})\n"
                f"**Guild:** {guild.name} (ID: {guild_id})"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP voice-unmuted {user_id} in {guild_id}")
            logger.info(f"VIP voice unmute: {user_id} in {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền voice unmute trong guild này", color=0xFF5A5F))
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy member hoặc guild", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP voice unmute error: {e}")
