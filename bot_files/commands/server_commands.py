"""
VIP Server Management Commands - Guild Info, Invite Links, Template Setup
Ported from proj.py VIP Admin Bot
"""
import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class ServerCommands(BaseCommand):
    """Class chứa các commands quản lý server VIP"""
    
    def register_commands(self):
        """Register server management commands"""
        
        @self.bot.command(name='viplistGuilds')
        async def vip_list_guilds(ctx):
            """
            Liệt kê tất cả guilds mà bot đang tham gia (Chỉ Supreme Admin)
            
            Usage: ;viplistGuilds
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_list_guilds_impl(ctx)
        
        @self.bot.command(name='viplistChannels')
        async def vip_list_channels(ctx, guild_id: int):
            """
            Liệt kê tất cả channels trong guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;viplistChannels <guild_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_list_channels_impl(ctx, guild_id)
        
        @self.bot.command(name='vipcreateInvite')
        async def vip_create_invite(ctx, guild_id: int):
            """
            Tạo invite link cho guild cụ thể (Chỉ Supreme Admin)
            
            Usage: ;vipcreateInvite <guild_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_create_invite_impl(ctx, guild_id)
        
        @self.bot.command(name='vipsetupTemplate')
        async def vip_setup_template(ctx, guild_id: int):
            """
            Áp dụng VIP template cho guild (tạo roles, categories, channels) (Chỉ Supreme Admin)
            
            Usage: ;vipsetupTemplate <guild_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_setup_template_impl(ctx, guild_id)
        
        @self.bot.command(name='vipwho')
        async def vip_who(ctx, user_id: int):
            """
            Xem thông tin chi tiết của user theo ID (Chỉ Supreme Admin)
            
            Usage: ;vipwho <user_id>
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            await self._vip_who_impl(ctx, user_id)
    
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
    
    async def _vip_list_guilds_impl(self, ctx):
        """Implementation của VIP list guilds command"""
        try:
            if not self.bot.guilds:
                await ctx.reply(embed=self.vip_embed("VIP Guild List", "Bot không tham gia guild nào"))
                return
            
            guild_list = []
            for i, guild in enumerate(self.bot.guilds, 1):
                guild_list.append(f"**{i}.** {guild.name}\n"
                                f"   └ ID: `{guild.id}`\n"
                                f"   └ Members: {guild.member_count}")
                
                # Giới hạn 10 guilds per embed để tránh quá dài
                if i >= 10:
                    guild_list.append(f"**...và {len(self.bot.guilds) - 10} guilds khác**")
                    break
            
            embed = self.vip_embed(
                "🏰 VIP Guild List",
                "\n\n".join(guild_list)
            )
            embed.add_field(
                name="📊 Tổng quan",
                value=f"**Tổng guilds:** {len(self.bot.guilds)}\n"
                      f"**Tổng members:** {sum(g.member_count for g in self.bot.guilds)}",
                inline=False
            )
            
            await ctx.reply(embed=embed)
            logger.info(f"VIP list guilds by {ctx.author.id}")
            
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP list guilds error: {e}")
    
    async def _vip_list_channels_impl(self, ctx, guild_id: int):
        """Implementation của VIP list channels command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            if not guild.channels:
                await ctx.reply(embed=self.vip_embed("VIP Channel List", f"Guild **{guild.name}** không có channel nào"))
                return
            
            # Phân loại channels
            text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
            voice_channels = [ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)]
            categories = [ch for ch in guild.channels if isinstance(ch, discord.CategoryChannel)]
            
            embed = self.vip_embed(
                f"📋 VIP Channel List - {guild.name}",
                f"**Guild ID:** {guild_id}"
            )
            
            if categories:
                cat_list = [f"📁 {cat.name} (`{cat.id}`)" for cat in categories[:10]]
                embed.add_field(
                    name=f"📁 Categories ({len(categories)})",
                    value="\n".join(cat_list) + (f"\n...và {len(categories) - 10} categories khác" if len(categories) > 10 else ""),
                    inline=False
                )
            
            if text_channels:
                text_list = [f"💬 {ch.name} (`{ch.id}`)" for ch in text_channels[:10]]
                embed.add_field(
                    name=f"💬 Text Channels ({len(text_channels)})",
                    value="\n".join(text_list) + (f"\n...và {len(text_channels) - 10} channels khác" if len(text_channels) > 10 else ""),
                    inline=False
                )
            
            if voice_channels:
                voice_list = [f"🔊 {ch.name} (`{ch.id}`)" for ch in voice_channels[:10]]
                embed.add_field(
                    name=f"🔊 Voice Channels ({len(voice_channels)})",
                    value="\n".join(voice_list) + (f"\n...và {len(voice_channels) - 10} channels khác" if len(voice_channels) > 10 else ""),
                    inline=False
                )
            
            await ctx.reply(embed=embed)
            logger.info(f"VIP list channels for {guild_id} by {ctx.author.id}")
            
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP list channels error: {e}")
    
    async def _vip_create_invite_impl(self, ctx, guild_id: int):
        """Implementation của VIP create invite command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            # Tìm text channel đầu tiên mà bot có quyền tạo invite
            invite_channel = None
            for channel in guild.text_channels:
                perms = channel.permissions_for(guild.me)
                if perms.create_instant_invite:
                    invite_channel = channel
                    break
            
            if invite_channel is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền tạo invite trong guild này", color=0xFF5A5F))
                return
            
            # Tạo invite link không giới hạn thời gian và số lần sử dụng
            invite = await invite_channel.create_invite(max_age=0, max_uses=0)
            
            embed = self.vip_embed(
                "🔗 VIP Create Invite Thành Công",
                f"**Guild:** {guild.name} (ID: {guild_id})\n"
                f"**Channel:** {invite_channel.name}\n"
                f"**Invite Link:** {invite.url}"
            )
            await ctx.reply(embed=embed)
            
            self.append_action_log(f"VIP created invite for guild {guild_id} -> {invite.url}")
            logger.info(f"VIP create invite for {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có quyền tạo invite", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP create invite error: {e}")
    
    async def _vip_setup_template_impl(self, ctx, guild_id: int):
        """Implementation của VIP setup template command"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.reply(embed=self.vip_embed("Error", "Bot không có trong guild đó", color=0xFF5A5F))
                return
            
            # Gửi thông báo bắt đầu
            progress_embed = self.vip_embed(
                "⚙️ VIP Setup Template",
                "Đang áp dụng VIP template cho server...\n⏳ Vui lòng chờ..."
            )
            progress_msg = await ctx.reply(embed=progress_embed)
            
            # Tạo roles nếu chưa có
            existing_roles = {r.name: r for r in guild.roles}
            roles_to_create = [
                ("Admin", discord.Colour.red(), discord.Permissions(administrator=True)),
                ("Moderator", discord.Colour.blue(), discord.Permissions(manage_messages=True, kick_members=True, ban_members=True)),
                ("VIP", discord.Colour.gold(), discord.Permissions.none()),
                ("Member", discord.Colour.default(), discord.Permissions.none()),
            ]
            
            created_roles = []
            for role_name, color, perms in roles_to_create:
                if role_name not in existing_roles:
                    try:
                        role = await guild.create_role(name=role_name, colour=color, permissions=perms)
                        created_roles.append(role.name)
                        await asyncio.sleep(1)  # Rate limit protection
                    except Exception as e:
                        logger.error(f"Error creating role {role_name}: {e}")
            
            # Tạo categories và channels
            try:
                # Welcome & Info Category
                cat_info = await guild.create_category("📌 Welcome & Info")
                await asyncio.sleep(1)
                await guild.create_text_channel("📜-rules", category=cat_info)
                await asyncio.sleep(1)
                await guild.create_text_channel("📢-announcements", category=cat_info)
                await asyncio.sleep(1)
                
                # General Category
                cat_general = await guild.create_category("💬 General")
                await asyncio.sleep(1)
                await guild.create_text_channel("general-chat", category=cat_general)
                await asyncio.sleep(1)
                await guild.create_voice_channel("General Voice", category=cat_general)
                await asyncio.sleep(1)
                
                # VIP Lounge Category
                cat_vip = await guild.create_category("🌟 VIP Lounge")
                await asyncio.sleep(1)
                await guild.create_text_channel("vip-chat", category=cat_vip)
                await asyncio.sleep(1)
                await guild.create_voice_channel("VIP Voice", category=cat_vip)
                
            except Exception as e:
                logger.error(f"Error creating channels: {e}")
            
            # Cập nhật thông báo hoàn thành
            final_embed = self.vip_embed(
                "✅ VIP Setup Template Hoàn Thành",
                f"**Guild:** {guild.name} (ID: {guild_id})\n\n"
                f"**🎭 Roles đã tạo:** {', '.join(created_roles) if created_roles else 'Không có (đã tồn tại)'}\n\n"
                f"**📁 Categories đã tạo:**\n"
                f"• 📌 Welcome & Info\n"
                f"• 💬 General\n"
                f"• 🌟 VIP Lounge\n\n"
                f"**📋 Channels đã tạo:**\n"
                f"• 📜-rules, 📢-announcements\n"
                f"• general-chat, General Voice\n"
                f"• vip-chat, VIP Voice"
            )
            await progress_msg.edit(embed=final_embed)
            
            self.append_action_log(f"VIP applied template to guild {guild_id}")
            logger.info(f"VIP setup template for {guild_id} by {ctx.author.id}")
            
        except discord.Forbidden:
            await ctx.reply(embed=self.vip_embed("Error", "Bot không có đủ quyền để setup template", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP setup template error: {e}")
    
    async def _vip_who_impl(self, ctx, user_id: int):
        """Implementation của VIP who command"""
        try:
            user = await self.bot.fetch_user(user_id)
            
            embed = self.vip_embed(
                "👤 VIP User Info",
                f"**User:** {user}\n"
                f"**ID:** {user_id}\n"
                f"**Created:** {user.created_at.strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
                f"**Bot:** {'Yes' if user.bot else 'No'}"
            )
            
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
            
            # Thêm thông tin guild nếu user là member
            guild_info = []
            for guild in self.bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    guild_info.append(f"• {guild.name} (`{guild.id}`)")
            
            if guild_info:
                embed.add_field(
                    name="🏰 Mutual Guilds",
                    value="\n".join(guild_info[:10]) + (f"\n...và {len(guild_info) - 10} guilds khác" if len(guild_info) > 10 else ""),
                    inline=False
                )
            
            await ctx.reply(embed=embed)
            logger.info(f"VIP who {user_id} by {ctx.author.id}")
            
        except discord.NotFound:
            await ctx.reply(embed=self.vip_embed("Error", "Không tìm thấy user với ID này", color=0xFF5A5F))
        except Exception as e:
            await ctx.reply(embed=self.vip_embed("Error", f"Lỗi: {str(e)}", color=0xFF5A5F))
            logger.error(f"VIP who error: {e}")
