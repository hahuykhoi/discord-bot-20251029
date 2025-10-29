# -*- coding: utf-8 -*-
"""
Nickname Commands - Hệ thống kiểm soát biệt danh cố định
"""
import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NicknameCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.nickname_data_file = 'data/nickname_control.json'
        self.nickname_data = self.load_nickname_data()
        self.monitoring_tasks = {}  # Lưu trữ các task monitoring
    
    def load_nickname_data(self):
        """Load nickname data từ file JSON"""
        if os.path.exists(self.nickname_data_file):
            try:
                with open(self.nickname_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_nickname_data(self):
        """Save nickname data vào file JSON"""
        try:
            os.makedirs(os.path.dirname(self.nickname_data_file), exist_ok=True)
            with open(self.nickname_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.nickname_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu nickname data: {e}")
    
    def register_commands(self):
        """Register nickname commands"""
        
        @self.bot.command(name='nickcontrol')
        async def nickname_control_command(ctx, action=None, target: discord.Member = None, *, nickname=None):
            """
            Kiểm soát biệt danh cố định cho user
            
            Usage:
            ;nickcontrol set @user <biệt danh> - Đặt biệt danh cố định
            ;nickcontrol remove @user - Bỏ kiểm soát biệt danh
            ;nickcontrol list - Xem danh sách đang kiểm soát
            ;nickcontrol status @user - Xem trạng thái user
            """
            try:
                # Kiểm tra quyền admin
                if not self.bot_instance.is_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Admin mới có thể sử dụng lệnh này!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                if not action:
                    await self.show_nickname_help(ctx)
                    return
                
                if action == "set":
                    await self.set_nickname_control(ctx, target, nickname)
                elif action == "remove":
                    await self.remove_nickname_control(ctx, target)
                elif action == "list":
                    await self.list_controlled_nicknames(ctx)
                elif action == "status":
                    await self.check_nickname_status(ctx, target)
                else:
                    await self.show_nickname_help(ctx)
                    
            except Exception as e:
                logger.error(f"Lỗi trong nickname control command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {e}", mention_author=True)
        
        @self.bot.command(name='setnick')
        async def set_nickname_command(ctx, target: discord.Member = None, *, nickname=None):
            """
            Đặt biệt danh cho user (một lần, không kiểm soát)
            
            Usage: ;setnick @user <biệt danh>
            """
            try:
                # Kiểm tra quyền admin
                if not self.bot_instance.is_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Admin mới có thể sử dụng lệnh này!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                if not target or not nickname:
                    embed = discord.Embed(
                        title="📝 Hướng dẫn sử dụng",
                        description="`;setnick @user <biệt danh>`",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="Ví dụ",
                        value="`;setnick @user 🎭 Tên Tạm Thời`",
                        inline=False
                    )
                    embed.add_field(
                        name="Lưu ý",
                        value="Lệnh này chỉ đặt tên 1 lần, không kiểm soát liên tục",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra quyền bot
                if not ctx.guild.me.guild_permissions.manage_nicknames:
                    embed = discord.Embed(
                        title="❌ Thiếu quyền",
                        description="Bot cần quyền `Manage Nicknames` để đổi biệt danh!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra có thể đổi nick user này không
                if target.top_role >= ctx.guild.me.top_role:
                    embed = discord.Embed(
                        title="❌ Không thể đổi nick",
                        description=f"Không thể đổi biệt danh của {target.mention} vì role cao hơn bot!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Đổi biệt danh
                old_nick = target.display_name
                await target.edit(nick=nickname, reason=f"Đổi bởi {ctx.author}")
                
                embed = discord.Embed(
                    title="✅ Đã đổi biệt danh",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="👤 User", value=target.mention, inline=True)
                embed.add_field(name="📝 Biệt danh cũ", value=old_nick, inline=True)
                embed.add_field(name="🆕 Biệt danh mới", value=nickname, inline=True)
                embed.add_field(name="👮 Thực hiện bởi", value=ctx.author.mention, inline=False)
                embed.add_field(name="💡 Lưu ý", value="Đây là lệnh đổi tên 1 lần, không kiểm soát liên tục", inline=False)
                
                await ctx.reply(embed=embed, mention_author=True)
                logger.info(f"Admin {ctx.author} đổi nick của {target} từ '{old_nick}' thành '{nickname}'")
                
            except discord.Forbidden:
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Bot không có quyền đổi biệt danh của user này!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
            except Exception as e:
                logger.error(f"Lỗi khi đổi nickname: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {e}", mention_author=True)
    
    async def show_nickname_help(self, ctx):
        """Hiển thị hướng dẫn sử dụng"""
        embed = discord.Embed(
            title="🎭 Hệ thống Kiểm soát Biệt danh",
            description="Đặt biệt danh cố định và tự động khôi phục khi user đổi tên",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📋 Lệnh có sẵn",
            value=(
                "`;nickcontrol set @user <biệt danh>` - Đặt biệt danh cố định\n"
                "`;nickcontrol remove @user` - Bỏ kiểm soát\n"
                "`;nickcontrol list` - Xem danh sách đang kiểm soát\n"
                "`;nickcontrol status @user` - Xem trạng thái user\n"
                "`;setnick @user <biệt danh>` - Đặt nick một lần (không kiểm soát)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Ví dụ sử dụng",
            value=(
                "`;nickcontrol set @user 🎭 Tên Cố Định`\n"
                "`;nickcontrol remove @user`\n"
                "`;setnick @user 👑 Tên Tạm Thời`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Cách hoạt động",
            value=(
                "• **Kiểm soát tức thì**: Bot phát hiện ngay khi user đổi tên\n"
                "• **Khôi phục ngay lập tức**: Không có delay, đổi lại tức thì\n"
                "• **Chỉ 1 tên**: Mỗi user chỉ có 1 biệt danh cố định\n"
                "• **Quyền cần thiết**: Admin + Manage Nicknames"
            ),
            inline=False
        )
        
        embed.set_footer(text="Nickname Control System • Chỉ Admin sử dụng được")
        await ctx.reply(embed=embed, mention_author=True)
    
    async def set_nickname_control(self, ctx, target, nickname):
        """Đặt biệt danh cố định cho user"""
        if not target or not nickname:
            embed = discord.Embed(
                title="❌ Thiếu thông tin",
                description="Vui lòng mention user và nhập biệt danh!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="📝 Cách sử dụng",
                value="`;nickcontrol set @user <biệt danh>`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Kiểm tra quyền bot
        if not ctx.guild.me.guild_permissions.manage_nicknames:
            embed = discord.Embed(
                title="❌ Thiếu quyền",
                description="Bot cần quyền `Manage Nicknames` để kiểm soát biệt danh!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Kiểm tra có thể đổi nick user này không
        if target.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Không thể kiểm soát",
                description=f"Không thể kiểm soát biệt danh của {target.mention} vì role cao hơn bot!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        try:
            # Đặt nickname ngay lập tức
            old_nick = target.display_name
            await target.edit(nick=nickname, reason=f"Nickname Control - Đặt bởi {ctx.author}")
            
            # Lưu vào data để kiểm soát
            guild_data = self.nickname_data.get(str(ctx.guild.id), {})
            guild_data[str(target.id)] = {
                "controlled_nickname": nickname,
                "set_by": ctx.author.id,
                "set_at": datetime.now().isoformat(),
                "active": True,
                "original_nick": old_nick
            }
            self.nickname_data[str(ctx.guild.id)] = guild_data
            self.save_nickname_data()
            
            # Không cần monitoring task - sử dụng event handler
            
            embed = discord.Embed(
                title="✅ Đã đặt kiểm soát biệt danh",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 User", value=target.mention, inline=True)
            embed.add_field(name="📝 Biệt danh cũ", value=old_nick, inline=True)
            embed.add_field(name="🎭 Biệt danh cố định", value=nickname, inline=True)
            embed.add_field(name="👮 Đặt bởi", value=ctx.author.mention, inline=True)
            embed.add_field(
                name="⚙️ Chế độ kiểm soát",
                value="Bot sẽ khôi phục tên này NGAY LẬP TỨC khi user đổi tên khác",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Admin {ctx.author} đặt kiểm soát nickname '{nickname}' cho {target}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Không có quyền",
                description="Bot không có quyền đổi biệt danh của user này!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
        except Exception as e:
            logger.error(f"Lỗi khi đặt nickname control: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra: {e}", mention_author=True)
    
    async def remove_nickname_control(self, ctx, target):
        """Bỏ kiểm soát biệt danh cho user"""
        if not target:
            embed = discord.Embed(
                title="❌ Thiếu thông tin",
                description="Vui lòng mention user cần bỏ kiểm soát!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        guild_data = self.nickname_data.get(str(ctx.guild.id), {})
        user_data = guild_data.get(str(target.id))
        
        if not user_data or not user_data.get("active", False):
            embed = discord.Embed(
                title="❌ Không tìm thấy",
                description=f"{target.mention} không có kiểm soát biệt danh đang hoạt động!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Không cần dừng monitoring task - chỉ cập nhật data
        
        # Cập nhật data
        user_data["active"] = False
        user_data["removed_by"] = ctx.author.id
        user_data["removed_at"] = datetime.now().isoformat()
        self.save_nickname_data()
        
        embed = discord.Embed(
            title="✅ Đã bỏ kiểm soát biệt danh",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 User", value=target.mention, inline=True)
        embed.add_field(name="🎭 Biệt danh đã kiểm soát", value=user_data.get("controlled_nickname", "N/A"), inline=True)
        embed.add_field(name="👮 Bỏ bởi", value=ctx.author.mention, inline=True)
        embed.add_field(name="💡 Lưu ý", value="User giờ có thể đổi biệt danh tự do", inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} bỏ kiểm soát nickname cho {target}")
    
    async def list_controlled_nicknames(self, ctx):
        """Xem danh sách user đang được kiểm soát biệt danh"""
        guild_data = self.nickname_data.get(str(ctx.guild.id), {})
        controlled_users = []
        
        for user_id, data in guild_data.items():
            if data.get("active", False):
                try:
                    user = ctx.guild.get_member(int(user_id))
                    if user:
                        controlled_users.append((user, data))
                except:
                    continue
        
        embed = discord.Embed(
            title="🎭 Danh sách Kiểm soát Biệt danh",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if not controlled_users:
            embed.description = "Hiện tại không có user nào đang được kiểm soát biệt danh."
        else:
            embed.description = f"Có {len(controlled_users)} user đang được kiểm soát:"
            
            for user, data in controlled_users[:10]:  # Giới hạn 10 user
                set_by = ctx.guild.get_member(data.get("set_by"))
                set_by_name = set_by.display_name if set_by else "Unknown"
                
                embed.add_field(
                    name=f"👤 {user.display_name}",
                    value=(
                        f"🎭 Tên cố định: {data.get('controlled_nickname', 'N/A')}\n"
                        f"👮 Đặt bởi: {set_by_name}\n"
                        f"📅 Từ: {data.get('set_at', 'Unknown')[:10]}"
                    ),
                    inline=True
                )
            
            if len(controlled_users) > 10:
                embed.add_field(
                    name="📊 Thống kê",
                    value=f"Và {len(controlled_users) - 10} user khác...",
                    inline=False
                )
        
        embed.set_footer(text="Nickname Control System • Controlled List")
        await ctx.reply(embed=embed, mention_author=True)
    
    async def check_nickname_status(self, ctx, target):
        """Kiểm tra trạng thái kiểm soát biệt danh của user"""
        if not target:
            embed = discord.Embed(
                title="❌ Thiếu thông tin",
                description="Vui lòng mention user cần kiểm tra!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        guild_data = self.nickname_data.get(str(ctx.guild.id), {})
        user_data = guild_data.get(str(target.id))
        
        embed = discord.Embed(
            title=f"🎭 Trạng thái Kiểm soát - {target.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if not user_data:
            embed.description = "User này chưa từng được kiểm soát biệt danh."
        else:
            is_active = user_data.get("active", False)
            embed.add_field(name="📊 Trạng thái", value="🟢 Đang kiểm soát" if is_active else "🔴 Đã dừng", inline=True)
            
            if is_active:
                embed.add_field(name="🎭 Biệt danh cố định", value=user_data.get("controlled_nickname", "N/A"), inline=True)
                
                set_by = ctx.guild.get_member(user_data.get("set_by"))
                embed.add_field(name="👮 Đặt bởi", value=set_by.mention if set_by else "Unknown", inline=True)
                embed.add_field(name="📅 Đặt lúc", value=user_data.get("set_at", "Unknown"), inline=True)
                embed.add_field(name="📝 Tên gốc", value=user_data.get("original_nick", "N/A"), inline=True)
                
                embed.add_field(name="🔍 Monitoring", value="🟢 Event Handler", inline=True)
            else:
                removed_by = ctx.guild.get_member(user_data.get("removed_by"))
                embed.add_field(name="👮 Bỏ bởi", value=removed_by.mention if removed_by else "Unknown", inline=True)
                embed.add_field(name="📅 Bỏ lúc", value=user_data.get("removed_at", "Unknown"), inline=True)
        
        embed.set_footer(text="Nickname Control System • Status Check")
        await ctx.reply(embed=embed, mention_author=True)
    
    # Không cần monitoring task - sử dụng event handler
    
    async def handle_member_update(self, before, after):
        """Xử lý khi member update (được gọi từ on_member_update event)"""
        # Kiểm tra nếu nickname thay đổi
        if before.display_name != after.display_name:
            guild_data = self.nickname_data.get(str(after.guild.id), {})
            user_data = guild_data.get(str(after.id))
            
            if user_data and user_data.get("active", False):
                controlled_nickname = user_data.get("controlled_nickname")
                if controlled_nickname and after.display_name != controlled_nickname:
                    # User đổi tên khác với tên được kiểm soát
                    try:
                        await after.edit(nick=controlled_nickname, reason="Nickname Control - Tự động khôi phục")
                        logger.info(f"Đã khôi phục nickname '{controlled_nickname}' cho {after} (từ '{after.display_name}')")
                    except discord.Forbidden:
                        logger.warning(f"Không có quyền khôi phục nickname cho {after}")
                    except Exception as e:
                        logger.error(f"Lỗi khi khôi phục nickname cho {after}: {e}")
    
    async def cleanup_tasks(self):
        """Cleanup - không cần thiết vì không có background tasks"""
        logger.info("Nickname Control System - Không có tasks cần cleanup")
