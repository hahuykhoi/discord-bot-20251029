# -*- coding: utf-8 -*-
"""
Slash Commands - Các lệnh slash (/) cho Discord bot
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class SlashCommands(BaseCommand):
    """Class chứa các slash commands"""
    def register_commands(self):
        """Register slash commands - Chỉ giữ lại /dm, /chat và /giveaway (từ giveaway_commands.py)"""
        
        # Admin check function
        def is_admin(user_id: int) -> bool:
            """Kiểm tra user có phải admin không"""
            ALLOWED_USER_ID = 1264908798003253314
            return user_id == ALLOWED_USER_ID
        
        # DM command - Gửi DM cho user với số lượng tin nhắn (Admin only)
        @self.bot.tree.command(name="dm", description="Gửi DM cho user (Admin only)")
        async def slash_dm(interaction: discord.Interaction, 
                          user: discord.User, 
                          message: str, 
                          count: int = 1):
            """Slash command /dm - Gửi DM với số lượng tin nhắn tùy chỉnh"""
            try:
                # Kiểm tra quyền admin
                if not is_admin(interaction.user.id):
                    await interaction.response.send_message(
                        "❌ Bạn không có quyền sử dụng lệnh này!",
                        ephemeral=True
                    )
                    return
                
                # Validate count
                if count < 1 or count > 10:
                    await interaction.response.send_message(
                        "❌ Số lượng tin nhắn phải từ 1-10!",
                        ephemeral=True
                    )
                    return
                
                # Validate message
                if not message or message.strip() == "":
                    await interaction.response.send_message(
                        "❌ Vui lòng cung cấp nội dung tin nhắn!",
                        ephemeral=True
                    )
                    return
                
                # Kiểm tra user
                if user.bot:
                    await interaction.response.send_message(
                        "❌ Không thể gửi DM cho bot!",
                        ephemeral=True
                    )
                    return
                
                if user.id == interaction.user.id:
                    await interaction.response.send_message(
                        "❌ Không thể gửi DM cho chính mình!",
                        ephemeral=True
                    )
                    return
                
                # Respond first
                await interaction.response.send_message(
                    f"🔄 Đang gửi {count} tin nhắn cho {user.mention}...",
                    ephemeral=True
                )
                
                # Gửi tin nhắn với số lượng chỉ định
                success_count = 0
                for i in range(count):
                    try:
                        await user.send(message)
                        success_count += 1
                    except discord.Forbidden:
                        break
                    except Exception as e:
                        logger.error(f"Error sending DM {i+1}: {e}")
                        break
                
                # Thông báo kết quả
                if success_count == count:
                    await interaction.followup.send(
                        f"✅ Đã gửi thành công {success_count} tin nhắn cho {user.mention}!",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⚠️ Chỉ gửi được {success_count}/{count} tin nhắn cho {user.mention}!",
                        ephemeral=True
                    )
                
                logger.info(f"Slash DM: {interaction.user} sent {success_count} messages to {user}")
                
            except Exception as e:
                logger.error(f"Error in slash dm: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Có lỗi xảy ra!", ephemeral=True)

        # Chat command - Bot gửi tin nhắn trong channel (Admin only)
        @self.bot.tree.command(name="chat", description="Bot gửi tin nhắn trong channel (Admin only)")
        async def slash_chat(interaction: discord.Interaction, 
                            message: str, 
                            count: int = 1):
            """Slash command /chat - Gửi tin nhắn với số lượng tùy chỉnh"""
            try:
                # Kiểm tra quyền admin
                if not is_admin(interaction.user.id):
                    await interaction.response.send_message(
                        "❌ Bạn không có quyền sử dụng lệnh này!",
                        ephemeral=True
                    )
                    return
                
                # Validate count
                if count < 1 or count > 10:
                    await interaction.response.send_message(
                        "❌ Số lượng tin nhắn phải từ 1-10!",
                        ephemeral=True
                    )
                    return
                
                # Validate message
                if not message or message.strip() == "":
                    await interaction.response.send_message(
                        "❌ Vui lòng cung cấp nội dung tin nhắn!",
                        ephemeral=True
                    )
                    return
                
                # Kiểm tra permissions
                if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
                    await interaction.response.send_message(
                        "❌ Bot không có quyền gửi tin nhắn trong channel này!",
                        ephemeral=True
                    )
                    return
                
                # Respond first
                await interaction.response.send_message(
                    f"🔄 Đang gửi {count} tin nhắn...",
                    ephemeral=True
                )
                
                # Gửi tin nhắn với số lượng chỉ định
                success_count = 0
                for i in range(count):
                    try:
                        await interaction.channel.send(message)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error sending message {i+1}: {e}")
                        break
                
                # Thông báo kết quả
                await interaction.followup.send(
                    f"✅ Đã gửi thành công {success_count} tin nhắn!",
                    ephemeral=True
                )
                
                logger.info(f"Slash Chat: {interaction.user} sent {success_count} messages in {interaction.channel}")
                
            except Exception as e:
                logger.error(f"Error in slash chat: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Có lỗi xảy ra!", ephemeral=True)
    
    # Giveaway commands được đăng ký trong giveaway_commands.py
    # Chỉ còn lại /dm và /chat ở đây
                    'reply': lambda content, **kwargs: interaction.response.send_message(content, **kwargs)
                })()
                
                from .taixiu_commands import TaiXiuCommands
                taixiu_cmd = TaiXiuCommands(self.bot_instance)
                
                if choice.lower() in ['tai', 'tài']:
                    await taixiu_cmd.taixiu_command(fake_ctx, 'tai', amount)
                elif choice.lower() in ['xiu', 'xỉu']:
                    await taixiu_cmd.taixiu_command(fake_ctx, 'xiu', amount)
                else:
                    await interaction.response.send_message("❌ Chọn 'tai' hoặc 'xiu'!", ephemeral=True)
                    
            except Exception as e:
                logger.error(f"Error in slash taixiu: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Cash command
        @self.bot.tree.command(name="cash", description="Xem số dư ví tiền")
        async def slash_cash(interaction: discord.Interaction):
            """Slash command /cash"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .wallet_commands import WalletCommands
                wallet_cmd = WalletCommands(self.bot_instance)
                await wallet_cmd._cash_impl(fake_ctx)
                
            except Exception as e:
                logger.error(f"Error in slash cash: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Daily command
        @self.bot.tree.command(name="daily", description="Nhận phần thưởng hàng ngày")
        async def slash_daily(interaction: discord.Interaction):
            """Slash command /daily"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .daily_commands import DailyCommands
                daily_cmd = DailyCommands(self.bot_instance)
                await daily_cmd._daily_impl(fake_ctx)
                
            except Exception as e:
                logger.error(f"Error in slash daily: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Ask AI command
        @self.bot.tree.command(name="ask", description="Hỏi AI")
        async def slash_ask(interaction: discord.Interaction, question: str):
            """Slash command /ask"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda content, **kwargs: interaction.response.send_message(content, **kwargs)
                })()
                
                from .ai_commands import AICommands
                ai_cmd = AICommands(self.bot_instance)
                await ai_cmd._ask_impl(fake_ctx, question)
                
            except Exception as e:
                logger.error(f"Error in slash ask: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Status command
        @self.bot.tree.command(name="status", description="Xem trạng thái bot")
        async def slash_status(interaction: discord.Interaction):
            """Slash command /status"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .info_commands import InfoCommands
                info_cmd = InfoCommands(self.bot_instance)
                await info_cmd._status_impl(fake_ctx)
                
            except Exception as e:
                logger.error(f"Error in slash status: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # DM command - Gửi DM cho user với số lượng tin nhắn
        @self.bot.tree.command(name="dm", description="Gửi DM cho user (Admin only)")
        async def slash_dm(interaction: discord.Interaction, 
                          user: discord.User, 
                          message: str, 
                          count: int = 1):
            """Slash command /dm - Gửi DM với số lượng tin nhắn tùy chỉnh"""
            try:
                # Kiểm tra quyền admin
                ALLOWED_USER_ID = 1264908798003253314
                if interaction.user.id != ALLOWED_USER_ID:
                    await interaction.response.send_message(
                        "❌ Bạn không có quyền sử dụng lệnh này!",
                        ephemeral=True
                    )
                    return
                
                # Validate count
                if count < 1 or count > 10:
                    await interaction.response.send_message(
                        "❌ Số lượng tin nhắn phải từ 1-10!",
                        ephemeral=True
                    )
                    return
                
                # Validate message
                if not message or message.strip() == "":
                    await interaction.response.send_message(
                        "❌ Vui lòng cung cấp nội dung tin nhắn!",
                        ephemeral=True
                    )
                    return
                
                # Kiểm tra user
                if user.bot:
                    await interaction.response.send_message(
                        "❌ Không thể gửi DM cho bot!",
                        ephemeral=True
                    )
                    return
                
                if user.id == interaction.user.id:
                    await interaction.response.send_message(
                        "❌ Không thể gửi DM cho chính mình!",
                        ephemeral=True
                    )
                    return
                
                # Respond first
                await interaction.response.send_message(
                    f"🔄 Đang gửi {count} tin nhắn cho {user.mention}...",
                    ephemeral=True
                )
                
                # Gửi tin nhắn với số lượng chỉ định
                success_count = 0
                for i in range(count):
                    try:
                        await user.send(message)
                        success_count += 1
                    except discord.Forbidden:
                        break
                    except Exception as e:
                        logger.error(f"Error sending DM {i+1}: {e}")
                        break
                
                # Thông báo kết quả
                if success_count == count:
                    await interaction.followup.send(
                        f"✅ Đã gửi thành công {success_count} tin nhắn cho {user.mention}!",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⚠️ Chỉ gửi được {success_count}/{count} tin nhắn cho {user.mention}!",
                        ephemeral=True
                    )
                
                logger.info(f"Slash DM: {interaction.user} sent {success_count} messages to {user}")
                
            except Exception as e:
                logger.error(f"Error in slash dm: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Có lỗi xảy ra!", ephemeral=True)

        # Chat command - Cập nhật với số lượng tin nhắn
        @self.bot.tree.command(name="chat", description="Bot gửi tin nhắn trong channel (Admin only)")
        async def slash_chat(interaction: discord.Interaction, 
                            message: str, 
                            count: int = 1):
            """Slash command /chat - Gửi tin nhắn với số lượng tùy chỉnh"""
            try:
                # Kiểm tra quyền admin
                ALLOWED_USER_ID = 1264908798003253314
                if interaction.user.id != ALLOWED_USER_ID:
                    await interaction.response.send_message(
                        "❌ Bạn không có quyền sử dụng lệnh này!",
                        ephemeral=True
                    )
                    return
                
                # Validate count
                if count < 1 or count > 10:
                    await interaction.response.send_message(
                        "❌ Số lượng tin nhắn phải từ 1-10!",
                        ephemeral=True
                    )
                    return
                
                # Validate message
                if not message or message.strip() == "":
                    await interaction.response.send_message(
                        "❌ Vui lòng cung cấp nội dung tin nhắn!",
                        ephemeral=True
                    )
                    return
                
                # Kiểm tra permissions
                if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
                    await interaction.response.send_message(
                        "❌ Bot không có quyền gửi tin nhắn trong channel này!",
                        ephemeral=True
                    )
                    return
                
                # Respond first
                await interaction.response.send_message(
                    f"🔄 Đang gửi {count} tin nhắn...",
                    ephemeral=True
                )
                
                # Gửi tin nhắn với số lượng chỉ định
                success_count = 0
                for i in range(count):
                    try:
                        await interaction.channel.send(message)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error sending message {i+1}: {e}")
                        break
                
                # Thông báo kết quả
                await interaction.followup.send(
                    f"✅ Đã gửi thành công {success_count} tin nhắn!",
                    ephemeral=True
                )
                
                logger.info(f"Slash Chat: {interaction.user} sent {success_count} messages in {interaction.channel}")
                
            except Exception as e:
                logger.error(f"Error in slash chat: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Có lỗi xảy ra!", ephemeral=True)

        # Help command
        @self.bot.tree.command(name="help", description="Hướng dẫn sử dụng bot")
        async def slash_help(interaction: discord.Interaction):
            """Slash command /help"""
            try:
                embed = discord.Embed(
                    title="🤖 Hướng dẫn sử dụng Bot",
                    description="Bot Discord đa chức năng với games, AI, và nhiều tiện ích khác",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="🎮 Games:",
                    value=(
                        "`/taixiu <tai/xiu> <số tiền>` - Chơi tài xỉu\n"
                        "`/rps <rock/paper/scissors> <tiền>` - Kéo búa bao\n"
                        "`/slot <tiền>` - Slot machine\n"
                        "`/flipcoin <heads/tails> <tiền>` - Tung xu\n"
                        "`/blackjack <tiền>` - Chơi blackjack"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Game Stats:",
                    value=(
                        "`/taixiustats [user]` - Stats tài xỉu\n"
                        "`/rpsstats [user]` - Stats RPS\n"
                        "`/slotstats [user]` - Stats slot\n"
                        "`/bjstats [user]` - Stats blackjack\n"
                        "`/flipstats [user]` - Stats flip coin"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Leaderboards:",
                    value=(
                        "`/rpsleaderboard` - Top RPS\n"
                        "`/slotleaderboard` - Top slot\n"
                        "`/flipleaderboard` - Top flip\n"
                        "`/dailyleaderboard` - Top daily"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Tiền tệ:",
                    value=(
                        "`/cash` - Xem số dư\n"
                        "`/daily` - Nhận thưởng hàng ngày\n"
                        "`/conbac` - Nhận role + 100k\n"
                        "`/moneystats` - Thống kê tiền\n"
                        "`/dailystats [user]` - Stats daily"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🤖 AI & Info:",
                    value=(
                        "`/ask <câu hỏi>` - Hỏi AI\n"
                        "`/aistatus` - Trạng thái AI\n"
                        "`/apistatus` - Trạng thái API\n"
                        "`/bot` - Thông tin bot\n"
                        "`/nhom` - Thông tin server\n"
                        "`/test` - Test bot"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🌐 Network & Media:",
                    value=(
                        "`/netping` - Kiểm tra ping\n"
                        "`/netstat` - Thống kê mạng\n"
                        "`/tiktok <user>` - Info TikTok\n"
                        "`/github <user>` - Info GitHub\n"
                        "`/video <name>` - Gửi video\n"
                        "`/spotify <url>` - Spotify"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🎵 Music & Utils:",
                    value=(
                        "`/join` - Bot join voice\n"
                        "`/stopmusic` - Dừng nhạc\n"
                        "`/feedback <text>` - Gửi feedback\n"
                        "`/bio [content]` - Cập nhật bio\n"
                        "`/debug [content]` - Debug info\n"
                        "`/preview <content>` - Preview"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="👑 Admin Commands (1/2):",
                    value=(
                        "`/warn <user> <lý do>` - Cảnh báo user\n"
                        "`/warnings [user]` - Xem warnings\n"
                        "`/mute <user> <time> [reason]` - Mute user\n"
                        "`/unmute <user>` - Unmute user\n"
                        "`/muteinfo [user]` - Info mute\n"
                        "`/kick <user> [reason]` - Kick user\n"
                        "`/ban <user> [reason]` - Ban user\n"
                        "`/unban <user_id>` - Unban user"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="👑 Admin Commands (2/2):",
                    value=(
                        "`/addpriority <id>` - Thêm priority\n"
                        "`/removepriority <id>` - Xóa priority\n"
                        "`/listpriority` - List priority\n"
                        "`/walletstats` - Stats wallet\n"
                        "`/purge <amount>` - Xóa tin nhắn\n"
                        "`/announce <channel> <msg>` - Thông báo\n"
                        "`/dm <user> <message> [count]` - Gửi DM (1-10 lần)\n"
                        "`/chat <message> [count]` - Bot gửi tin nhắn (1-10 lần)\n"
                        "`/reloadwallet` - Reload wallet"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🔧 Channel & Server:",
                    value=(
                        "`/createchannel <name> [type]` - Tạo channel\n"
                        "`/deletechannel <channel>` - Xóa channel\n"
                        "`/addemoji <name> <url>` - Thêm emoji\n"
                        "`/removeemoji <name>` - Xóa emoji\n"
                        "`/serverinfo` - Info server chi tiết\n"
                        "`/membercount` - Số lượng thành viên\n"
                        "`/setpermission <user> <perm> <value>` - Set quyền\n"
                        "`/checkpermission [user]` - Kiểm tra quyền"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="💾 Backup & System:",
                    value=(
                        "`/backup` - Tạo backup (Admin)\n"
                        "`/backupstatus` - Trạng thái backup\n"
                        "`/githubbackup` - Backup GitHub (Admin)\n"
                        "`/downloadfile <url> [folder]` - Tải file từ GitHub\n"
                        "`/listfiles <url> [path]` - List files GitHub\n"
                        "`/shutdown` - Tắt bot (Supreme Admin)\n"
                        "`/restart` - Restart bot (Supreme Admin)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="⚙️ System & Maintenance:",
                    value=(
                        "`/maintenancestatus` - Trạng thái bảo trì\n"
                        "`/listvideo` - Danh sách video\n"
                        "`/status` - Trạng thái bot\n"
                        "`/menu` - Menu tổng hợp\n"
                        "`/help` - Hướng dẫn này"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Lưu ý:",
                    value=(
                        "• **70+ Slash Commands** có sẵn\n"
                        "• Bot hỗ trợ cả prefix (`;`) và slash commands (`/`)\n"
                        "• Một số lệnh chỉ dành cho admin hoặc supreme admin\n"
                        "• Sử dụng `/menu` để truy cập menu tương tác\n"
                        "• Tất cả lệnh đều có error handling và permission checks"
                    ),
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in slash help: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # RPS command
        @self.bot.tree.command(name="rps", description="Chơi kéo búa bao")
        async def slash_rps(interaction: discord.Interaction, 
                           choice: str, 
                           amount: int):
            """Slash command /rps"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .rps_commands import RPSCommands
                rps_cmd = RPSCommands(self.bot_instance)
                
                if choice.lower() in ['rock', 'paper', 'scissors']:
                    await rps_cmd.rps_command(fake_ctx, choice.lower(), amount)
                else:
                    await interaction.response.send_message("❌ Chọn 'rock', 'paper', hoặc 'scissors'!", ephemeral=True)
                    
            except Exception as e:
                logger.error(f"Error in slash rps: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Slot command
        @self.bot.tree.command(name="slot", description="Chơi slot machine")
        async def slash_slot(interaction: discord.Interaction, amount: int):
            """Slash command /slot"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .slot_commands import SlotCommands
                slot_cmd = SlotCommands(self.bot_instance)
                await slot_cmd.slot_command(fake_ctx, amount)
                    
            except Exception as e:
                logger.error(f"Error in slash slot: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Flipcoin command
        @self.bot.tree.command(name="flipcoin", description="Tung đồng xu")
        async def slash_flipcoin(interaction: discord.Interaction, 
                                choice: str, 
                                amount: int):
            """Slash command /flipcoin"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .flip_coin_commands import FlipCoinCommands
                flip_cmd = FlipCoinCommands(self.bot_instance)
                
                if choice.lower() in ['heads', 'tails', 'ngửa', 'sấp']:
                    await flip_cmd.flipcoin_command(fake_ctx, choice.lower(), amount)
                else:
                    await interaction.response.send_message("❌ Chọn 'heads' hoặc 'tails'!", ephemeral=True)
                    
            except Exception as e:
                logger.error(f"Error in slash flipcoin: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Blackjack command
        @self.bot.tree.command(name="blackjack", description="Chơi blackjack")
        async def slash_blackjack(interaction: discord.Interaction, amount: int):
            """Slash command /blackjack"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .blackjack_commands import BlackjackCommands
                bj_cmd = BlackjackCommands(self.bot_instance)
                await bj_cmd.blackjack_command(fake_ctx, amount)
                    
            except Exception as e:
                logger.error(f"Error in slash blackjack: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Warn command (Admin only)
        @self.bot.tree.command(name="warn", description="Cảnh báo user (Admin only)")
        async def slash_warn(interaction: discord.Interaction, 
                            user: discord.Member, 
                            reason: str):
            """Slash command /warn"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .warn_commands import WarnCommands
                warn_cmd = WarnCommands(self.bot_instance)
                await warn_cmd._warn_impl(fake_ctx, user, reason)
                    
            except Exception as e:
                logger.error(f"Error in slash warn: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Statistics Commands
        @self.bot.tree.command(name="taixiustats", description="Xem thống kê tài xỉu")
        async def slash_taixiustats(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /taixiustats"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .taixiu_commands import TaiXiuCommands
                taixiu_cmd = TaiXiuCommands(self.bot_instance)
                await taixiu_cmd.taixiu_stats_command(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash taixiustats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="rpsstats", description="Xem thống kê RPS")
        async def slash_rpsstats(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /rpsstats"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .rps_commands import RPSCommands
                rps_cmd = RPSCommands(self.bot_instance)
                await rps_cmd.rps_stats_command(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash rpsstats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="slotstats", description="Xem thống kê slot")
        async def slash_slotstats(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /slotstats"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .slot_commands import SlotCommands
                slot_cmd = SlotCommands(self.bot_instance)
                await slot_cmd.slot_stats_command(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash slotstats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="bjstats", description="Xem thống kê blackjack")
        async def slash_bjstats(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /bjstats"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .blackjack_commands import BlackjackCommands
                bj_cmd = BlackjackCommands(self.bot_instance)
                await bj_cmd.blackjack_stats_command(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash bjstats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="flipstats", description="Xem thống kê flip coin")
        async def slash_flipstats(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /flipstats"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .flip_coin_commands import FlipCoinCommands
                flip_cmd = FlipCoinCommands(self.bot_instance)
                await flip_cmd.flip_stats_command(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash flipstats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="dailystats", description="Xem thống kê daily")
        async def slash_dailystats(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /dailystats"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .daily_commands import DailyCommands
                daily_cmd = DailyCommands(self.bot_instance)
                await daily_cmd._daily_stats_impl(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash dailystats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Leaderboard Commands
        @self.bot.tree.command(name="rpsleaderboard", description="Bảng xếp hạng RPS")
        async def slash_rpsleaderboard(interaction: discord.Interaction):
            """Slash command /rpsleaderboard"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .rps_commands import RPSCommands
                rps_cmd = RPSCommands(self.bot_instance)
                await rps_cmd.rps_leaderboard_command(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash rpsleaderboard: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="slotleaderboard", description="Bảng xếp hạng slot")
        async def slash_slotleaderboard(interaction: discord.Interaction):
            """Slash command /slotleaderboard"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .slot_commands import SlotCommands
                slot_cmd = SlotCommands(self.bot_instance)
                await slot_cmd.slot_leaderboard_command(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash slotleaderboard: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="flipleaderboard", description="Bảng xếp hạng flip coin")
        async def slash_flipleaderboard(interaction: discord.Interaction):
            """Slash command /flipleaderboard"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .flip_coin_commands import FlipCoinCommands
                flip_cmd = FlipCoinCommands(self.bot_instance)
                await flip_cmd.flip_leaderboard_command(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash flipleaderboard: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="dailyleaderboard", description="Bảng xếp hạng daily")
        async def slash_dailyleaderboard(interaction: discord.Interaction):
            """Slash command /dailyleaderboard"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .daily_commands import DailyCommands
                daily_cmd = DailyCommands(self.bot_instance)
                await daily_cmd._daily_leaderboard_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash dailyleaderboard: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Info Commands
        @self.bot.tree.command(name="bot", description="Thông tin về bot")
        async def slash_bot(interaction: discord.Interaction):
            """Slash command /bot"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .info_commands import InfoCommands
                info_cmd = InfoCommands(self.bot_instance)
                await info_cmd._bot_info_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash bot: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="nhom", description="Thông tin server")
        async def slash_nhom(interaction: discord.Interaction):
            """Slash command /nhom"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .info_commands import InfoCommands
                info_cmd = InfoCommands(self.bot_instance)
                await info_cmd._server_info_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash nhom: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="test", description="Kiểm tra bot hoạt động")
        async def slash_test(interaction: discord.Interaction):
            """Slash command /test"""
            try:
                embed = discord.Embed(
                    title="✅ Bot đang hoạt động!",
                    description=f"Xin chào {interaction.user.mention}! Bot đang hoạt động bình thường.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="📊 Thông tin:",
                    value=f"• Ping: {round(self.bot.latency * 1000)}ms\n• Server: {interaction.guild.name}",
                    inline=False
                )
                await interaction.response.send_message(embed=embed)
                    
            except Exception as e:
                logger.error(f"Error in slash test: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Network Commands
        @self.bot.tree.command(name="netping", description="Kiểm tra ping mạng")
        async def slash_netping(interaction: discord.Interaction):
            """Slash command /netping"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .network_commands import NetworkCommands
                net_cmd = NetworkCommands(self.bot_instance)
                await net_cmd._ping_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash netping: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="netstat", description="Thống kê mạng")
        async def slash_netstat(interaction: discord.Interaction):
            """Slash command /netstat"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .network_commands import NetworkCommands
                net_cmd = NetworkCommands(self.bot_instance)
                await net_cmd._netstat_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash netstat: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Wallet Commands
        @self.bot.tree.command(name="conbac", description="Nhận role Con Bạc + 100k")
        async def slash_conbac(interaction: discord.Interaction):
            """Slash command /conbac"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .wallet_commands import WalletCommands
                wallet_cmd = WalletCommands(self.bot_instance)
                await wallet_cmd._conbac_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash conbac: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="moneystats", description="Thống kê tiền tệ")
        async def slash_moneystats(interaction: discord.Interaction):
            """Slash command /moneystats"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .wallet_commands import WalletCommands
                wallet_cmd = WalletCommands(self.bot_instance)
                await wallet_cmd._money_stats_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash moneystats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="walletstats", description="Thống kê wallet system")
        async def slash_walletstats(interaction: discord.Interaction):
            """Slash command /walletstats"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể xem thống kê wallet!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .wallet_commands import WalletCommands
                wallet_cmd = WalletCommands(self.bot_instance)
                await wallet_cmd._wallet_stats_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash walletstats: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Admin Commands
        @self.bot.tree.command(name="warnings", description="Xem cảnh báo của user")
        async def slash_warnings(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /warnings"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .warn_commands import WarnCommands
                warn_cmd = WarnCommands(self.bot_instance)
                await warn_cmd._warnings_impl(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash warnings: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="mute", description="Mute user (Admin only)")
        async def slash_mute(interaction: discord.Interaction, 
                            user: discord.Member, 
                            duration: str, 
                            reason: str = "Không có lý do"):
            """Slash command /mute"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .mute_commands import MuteCommands
                mute_cmd = MuteCommands(self.bot_instance)
                await mute_cmd._mute_impl(fake_ctx, user, duration, reason)
                    
            except Exception as e:
                logger.error(f"Error in slash mute: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="unmute", description="Unmute user (Admin only)")
        async def slash_unmute(interaction: discord.Interaction, user: discord.Member):
            """Slash command /unmute"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .mute_commands import MuteCommands
                mute_cmd = MuteCommands(self.bot_instance)
                await mute_cmd._unmute_impl(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash unmute: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="muteinfo", description="Xem thông tin mute")
        async def slash_muteinfo(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /muteinfo"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .mute_commands import MuteCommands
                mute_cmd = MuteCommands(self.bot_instance)
                await mute_cmd._mute_info_impl(fake_ctx, user)
                    
            except Exception as e:
                logger.error(f"Error in slash muteinfo: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # AI Commands
        @self.bot.tree.command(name="aistatus", description="Trạng thái AI")
        async def slash_aistatus(interaction: discord.Interaction):
            """Slash command /aistatus"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .ai_commands import AICommands
                ai_cmd = AICommands(self.bot_instance)
                await ai_cmd._ai_status_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash aistatus: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="apistatus", description="Trạng thái API")
        async def slash_apistatus(interaction: discord.Interaction):
            """Slash command /apistatus"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .ai_commands import AICommands
                ai_cmd = AICommands(self.bot_instance)
                await ai_cmd._api_status_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash apistatus: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Feedback Commands
        @self.bot.tree.command(name="feedback", description="Gửi feedback")
        async def slash_feedback(interaction: discord.Interaction, content: str):
            """Slash command /feedback"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .feedback_commands import FeedbackCommands
                feedback_cmd = FeedbackCommands(self.bot_instance)
                await feedback_cmd._feedback_impl(fake_ctx, content)
                    
            except Exception as e:
                logger.error(f"Error in slash feedback: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Music Commands
        @self.bot.tree.command(name="join", description="Bot join voice channel")
        async def slash_join(interaction: discord.Interaction):
            """Slash command /join"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .music_commands import MusicCommands
                music_cmd = MusicCommands(self.bot_instance)
                await music_cmd._join_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash join: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="stopmusic", description="Dừng nhạc")
        async def slash_stopmusic(interaction: discord.Interaction):
            """Slash command /stopmusic"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .music_commands import MusicCommands
                music_cmd = MusicCommands(self.bot_instance)
                await music_cmd._stop_music_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash stopmusic: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Media Commands
        @self.bot.tree.command(name="tiktok", description="Thông tin TikTok user")
        async def slash_tiktok(interaction: discord.Interaction, username: str):
            """Slash command /tiktok"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .tiktok_commands import TikTokCommands
                tiktok_cmd = TikTokCommands(self.bot_instance)
                await tiktok_cmd._tiktok_impl(fake_ctx, username)
                    
            except Exception as e:
                logger.error(f"Error in slash tiktok: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="github", description="Thông tin GitHub user")
        async def slash_github(interaction: discord.Interaction, username: str):
            """Slash command /github"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .github_commands import GitHubCommands
                github_cmd = GitHubCommands(self.bot_instance)
                await github_cmd._github_impl(fake_ctx, username)
                    
            except Exception as e:
                logger.error(f"Error in slash github: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="video", description="Gửi video")
        async def slash_video(interaction: discord.Interaction, name: str):
            """Slash command /video"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda content, **kwargs: interaction.response.send_message(content, **kwargs)
                })()
                
                from .video_commands import VideoCommands
                video_cmd = VideoCommands(self.bot_instance)
                await video_cmd._video_impl(fake_ctx, name)
                    
            except Exception as e:
                logger.error(f"Error in slash video: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="listvideo", description="Danh sách video")
        async def slash_listvideo(interaction: discord.Interaction):
            """Slash command /listvideo"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .video_commands import VideoCommands
                video_cmd = VideoCommands(self.bot_instance)
                await video_cmd._list_video_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash listvideo: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="spotify", description="Spotify tools")
        async def slash_spotify(interaction: discord.Interaction, url: str):
            """Slash command /spotify"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .spotify_commands import SpotifyCommands
                spotify_cmd = SpotifyCommands(self.bot_instance)
                await spotify_cmd._spotify_impl(fake_ctx, url)
                    
            except Exception as e:
                logger.error(f"Error in slash spotify: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Communication Commands
        @self.bot.tree.command(name="bio", description="Cập nhật bio bot")
        async def slash_bio(interaction: discord.Interaction, content: str = None):
            """Slash command /bio"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .info_commands import InfoCommands
                info_cmd = InfoCommands(self.bot_instance)
                if content:
                    await info_cmd._bio_update_impl(fake_ctx, content)
                else:
                    await info_cmd._bot_info_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash bio: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Priority Commands (Admin)
        @self.bot.tree.command(name="addpriority", description="Thêm priority user (Admin)")
        async def slash_addpriority(interaction: discord.Interaction, user_id: str):
            """Slash command /addpriority"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể sử dụng lệnh này!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .priority_commands import PriorityCommands
                priority_cmd = PriorityCommands(self.bot_instance)
                await priority_cmd._add_priority_impl(fake_ctx, int(user_id))
                    
            except Exception as e:
                logger.error(f"Error in slash addpriority: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="removepriority", description="Xóa priority user (Admin)")
        async def slash_removepriority(interaction: discord.Interaction, user_id: str):
            """Slash command /removepriority"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể sử dụng lệnh này!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .priority_commands import PriorityCommands
                priority_cmd = PriorityCommands(self.bot_instance)
                await priority_cmd._remove_priority_impl(fake_ctx, int(user_id))
                    
            except Exception as e:
                logger.error(f"Error in slash removepriority: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="listpriority", description="Danh sách priority users")
        async def slash_listpriority(interaction: discord.Interaction):
            """Slash command /listpriority"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .priority_commands import PriorityCommands
                priority_cmd = PriorityCommands(self.bot_instance)
                await priority_cmd._list_priority_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash listpriority: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Maintenance Commands
        @self.bot.tree.command(name="maintenancestatus", description="Trạng thái bảo trì")
        async def slash_maintenancestatus(interaction: discord.Interaction):
            """Slash command /maintenancestatus"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .maintenance_commands import MaintenanceCommands
                maintenance_cmd = MaintenanceCommands(self.bot_instance)
                await maintenance_cmd._maintenance_status_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash maintenancestatus: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Debug Commands
        @self.bot.tree.command(name="debug", description="Debug information")
        async def slash_debug(interaction: discord.Interaction, content: str = None):
            """Slash command /debug"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .ai_commands import AICommands
                ai_cmd = AICommands(self.bot_instance)
                if content:
                    await ai_cmd._debug_impl(fake_ctx, content)
                else:
                    # Show debug info
                    embed = discord.Embed(
                        title="🔧 Debug Information",
                        description="Thông tin debug của bot",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="📊 Bot Stats:",
                        value=f"• Ping: {round(self.bot.latency * 1000)}ms\n"
                              f"• Guilds: {len(self.bot.guilds)}\n"
                              f"• Users: {len(self.bot.users)}\n"
                              f"• Commands: {len(self.bot.commands)}",
                        inline=False
                    )
                    await interaction.response.send_message(embed=embed)
                    
            except Exception as e:
                logger.error(f"Error in slash debug: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="preview", description="Preview content")
        async def slash_preview(interaction: discord.Interaction, content: str):
            """Slash command /preview"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .ai_commands import AICommands
                ai_cmd = AICommands(self.bot_instance)
                await ai_cmd._preview_impl(fake_ctx, content)
                    
            except Exception as e:
                logger.error(f"Error in slash preview: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Channel Commands
        @self.bot.tree.command(name="createchannel", description="Tạo channel mới (Admin)")
        async def slash_createchannel(interaction: discord.Interaction, name: str, channel_type: str = "text"):
            """Slash command /createchannel"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể tạo channel!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .channel_commands import ChannelCommands
                channel_cmd = ChannelCommands(self.bot_instance)
                await channel_cmd._create_channel_impl(fake_ctx, name, channel_type)
                    
            except Exception as e:
                logger.error(f"Error in slash createchannel: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="deletechannel", description="Xóa channel (Admin)")
        async def slash_deletechannel(interaction: discord.Interaction, channel: discord.TextChannel):
            """Slash command /deletechannel"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể xóa channel!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .channel_commands import ChannelCommands
                channel_cmd = ChannelCommands(self.bot_instance)
                await channel_cmd._delete_channel_impl(fake_ctx, channel)
                    
            except Exception as e:
                logger.error(f"Error in slash deletechannel: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Emoji Commands
        @self.bot.tree.command(name="addemoji", description="Thêm emoji (Admin)")
        async def slash_addemoji(interaction: discord.Interaction, name: str, url: str):
            """Slash command /addemoji"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể thêm emoji!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .emoji_commands import EmojiCommands
                emoji_cmd = EmojiCommands(self.bot_instance)
                await emoji_cmd._add_emoji_impl(fake_ctx, name, url)
                    
            except Exception as e:
                logger.error(f"Error in slash addemoji: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="removeemoji", description="Xóa emoji (Admin)")
        async def slash_removeemoji(interaction: discord.Interaction, name: str):
            """Slash command /removeemoji"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể xóa emoji!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .emoji_commands import EmojiCommands
                emoji_cmd = EmojiCommands(self.bot_instance)
                await emoji_cmd._remove_emoji_impl(fake_ctx, name)
                    
            except Exception as e:
                logger.error(f"Error in slash removeemoji: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Announce Commands
        @self.bot.tree.command(name="announce", description="Thông báo (Admin)")
        async def slash_announce(interaction: discord.Interaction, 
                                channel: discord.TextChannel, 
                                message: str):
            """Slash command /announce"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể thông báo!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .announce_commands import AnnounceCommands
                announce_cmd = AnnounceCommands(self.bot_instance)
                await announce_cmd._announce_impl(fake_ctx, channel, message)
                    
            except Exception as e:
                logger.error(f"Error in slash announce: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Server Commands
        @self.bot.tree.command(name="serverinfo", description="Thông tin server chi tiết")
        async def slash_serverinfo(interaction: discord.Interaction):
            """Slash command /serverinfo"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .server_commands import ServerCommands
                server_cmd = ServerCommands(self.bot_instance)
                await server_cmd._server_info_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash serverinfo: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="membercount", description="Số lượng thành viên")
        async def slash_membercount(interaction: discord.Interaction):
            """Slash command /membercount"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .server_commands import ServerCommands
                server_cmd = ServerCommands(self.bot_instance)
                await server_cmd._member_count_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash membercount: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Message Commands
        @self.bot.tree.command(name="purge", description="Xóa tin nhắn (Admin)")
        async def slash_purge(interaction: discord.Interaction, amount: int):
            """Slash command /purge"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể xóa tin nhắn!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'channel': interaction.channel,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .message_commands import MessageCommands
                msg_cmd = MessageCommands(self.bot_instance)
                await msg_cmd._purge_impl(fake_ctx, amount)
                    
            except Exception as e:
                logger.error(f"Error in slash purge: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Backup Commands
        @self.bot.tree.command(name="backup", description="Tạo backup (Admin)")
        async def slash_backup(interaction: discord.Interaction):
            """Slash command /backup"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể tạo backup!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .backup_commands import BackupCommands
                backup_cmd = BackupCommands(self.bot_instance)
                await backup_cmd._backup_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash backup: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="backupstatus", description="Trạng thái backup")
        async def slash_backupstatus(interaction: discord.Interaction):
            """Slash command /backupstatus"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .backup_commands import BackupCommands
                backup_cmd = BackupCommands(self.bot_instance)
                await backup_cmd._backup_status_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash backupstatus: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Permission Commands
        @self.bot.tree.command(name="setpermission", description="Cài đặt quyền (Admin)")
        async def slash_setpermission(interaction: discord.Interaction, 
                                     user: discord.Member, 
                                     permission: str, 
                                     value: bool):
            """Slash command /setpermission"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể cài đặt quyền!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .permission_commands import PermissionCommands
                perm_cmd = PermissionCommands(self.bot_instance)
                await perm_cmd._set_permission_impl(fake_ctx, user, permission, value)
                    
            except Exception as e:
                logger.error(f"Error in slash setpermission: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="checkpermission", description="Kiểm tra quyền")
        async def slash_checkpermission(interaction: discord.Interaction, user: discord.Member = None):
            """Slash command /checkpermission"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .permission_commands import PermissionCommands
                perm_cmd = PermissionCommands(self.bot_instance)
                await perm_cmd._check_permission_impl(fake_ctx, user or interaction.user)
                    
            except Exception as e:
                logger.error(f"Error in slash checkpermission: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # DM Management Commands - Đã chuyển sang command /dm mới ở trên
        
        # Chat Commands đã được đăng ký trong chat_commands.py - xóa để tránh trùng lặp
        # Wallet Reload Commands
        @self.bot.tree.command(name="reloadwallet", description="Reload wallet data (Admin)")
        async def slash_reloadwallet(interaction: discord.Interaction):
            """Slash command /reloadwallet"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể reload wallet!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .wallet_reload_commands import WalletReloadCommands
                reload_cmd = WalletReloadCommands(self.bot_instance)
                await reload_cmd._reload_wallet_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash reloadwallet: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Supreme Admin Commands
        @self.bot.tree.command(name="shutdown", description="Tắt bot (Supreme Admin)")
        async def slash_shutdown(interaction: discord.Interaction):
            """Slash command /shutdown"""
            try:
                # Check supreme admin permission
                if interaction.user.id not in self.bot_instance.config.get('supreme_admins', []):
                    await interaction.response.send_message("❌ Chỉ Supreme Admin mới có thể tắt bot!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .supreme_admin_commands import SupremeAdminCommands
                supreme_cmd = SupremeAdminCommands(self.bot_instance)
                await supreme_cmd._shutdown_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash shutdown: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="restart", description="Restart bot (Supreme Admin)")
        async def slash_restart(interaction: discord.Interaction):
            """Slash command /restart"""
            try:
                # Check supreme admin permission
                if interaction.user.id not in self.bot_instance.config.get('supreme_admins', []):
                    await interaction.response.send_message("❌ Chỉ Supreme Admin mới có thể restart bot!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .supreme_admin_commands import SupremeAdminCommands
                supreme_cmd = SupremeAdminCommands(self.bot_instance)
                await supreme_cmd._restart_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash restart: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # GitHub Backup Commands
        @self.bot.tree.command(name="githubbackup", description="Backup to GitHub (Admin)")
        async def slash_githubbackup(interaction: discord.Interaction):
            """Slash command /githubbackup"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể backup GitHub!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .github_backup_commands import GitHubBackupCommands
                github_cmd = GitHubBackupCommands(self.bot_instance)
                await github_cmd._github_backup_impl(fake_ctx)
                    
            except Exception as e:
                logger.error(f"Error in slash githubbackup: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # Moderation Commands
        @self.bot.tree.command(name="kick", description="Kick user (Admin)")
        async def slash_kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Không có lý do"):
            """Slash command /kick"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể kick user!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .moderation_commands import ModerationCommands
                mod_cmd = ModerationCommands(self.bot_instance)
                await mod_cmd._kick_impl(fake_ctx, user, reason)
                    
            except Exception as e:
                logger.error(f"Error in slash kick: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="ban", description="Ban user (Admin)")
        async def slash_ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Không có lý do"):
            """Slash command /ban"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể ban user!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .moderation_commands import ModerationCommands
                mod_cmd = ModerationCommands(self.bot_instance)
                await mod_cmd._ban_impl(fake_ctx, user, reason)
                    
            except Exception as e:
                logger.error(f"Error in slash ban: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        @self.bot.tree.command(name="unban", description="Unban user (Admin)")
        async def slash_unban(interaction: discord.Interaction, user_id: str):
            """Slash command /unban"""
            try:
                # Check admin permission
                if not self.bot_instance.has_warn_permission(interaction.user.id, interaction.user.guild_permissions):
                    await interaction.response.send_message("❌ Chỉ admin mới có thể unban user!", ephemeral=True)
                    return
                
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed, **kwargs: interaction.response.send_message(embed=embed, **kwargs)
                })()
                
                from .moderation_commands import ModerationCommands
                mod_cmd = ModerationCommands(self.bot_instance)
                await mod_cmd._unban_impl(fake_ctx, int(user_id))
                    
            except Exception as e:
                logger.error(f"Error in slash unban: {e}")
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
        
        # GitHub Download Commands
        @self.bot.tree.command(name="downloadfile", description="Tải file từ GitHub private repository")
        async def slash_downloadfile(interaction: discord.Interaction, github_url: str, target_folder: str = None):
            """Slash command /downloadfile"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed=None, **kwargs: interaction.response.send_message(embed=embed, **kwargs) if not interaction.response.is_done() else interaction.followup.send(embed=embed, **kwargs)
                })()
                
                from .github_download_commands import GitHubDownloadCommands
                github_cmd = GitHubDownloadCommands(self.bot_instance)
                await github_cmd.download_file_command(fake_ctx, github_url, target_folder)
                    
            except Exception as e:
                logger.error(f"Error in slash downloadfile: {e}")
                try:
                    await interaction.response.send_message(f"❌ Có lỗi xảy ra: {str(e)}", ephemeral=True)
                except:
                    await interaction.followup.send(f"❌ Có lỗi xảy ra: {str(e)}", ephemeral=True)
        
        @self.bot.tree.command(name="listfiles", description="Liệt kê files trong GitHub repository")
        async def slash_listfiles(interaction: discord.Interaction, github_url: str, folder_path: str = ""):
            """Slash command /listfiles"""
            try:
                fake_ctx = type('obj', (object,), {
                    'author': interaction.user,
                    'guild': interaction.guild,
                    'reply': lambda embed=None, **kwargs: interaction.response.send_message(embed=embed, **kwargs) if not interaction.response.is_done() else interaction.followup.send(embed=embed, **kwargs)
                })()
                
                from .github_download_commands import GitHubDownloadCommands
                github_cmd = GitHubDownloadCommands(self.bot_instance)
                await github_cmd.list_repo_files_command(fake_ctx, github_url, folder_path)
                    
            except Exception as e:
                logger.error(f"Error in slash listfiles: {e}")
                try:
                    await interaction.response.send_message(f"❌ Có lỗi xảy ra: {str(e)}", ephemeral=True)
                except:
                    await interaction.followup.send(f"❌ Có lỗi xảy ra: {str(e)}", ephemeral=True)
    
    async def sync_commands(self):
        """
        Sync slash commands với Discord
        """
        try:
            synced = await self.bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")
            print(f"✅ Successfully synced {len(synced)} slash commands")
            return len(synced)
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
            print(f"❌ Failed to sync slash commands: {e}")
            return 0
    
    async def force_sync_commands(self):
        """
        Force sync slash commands (clear cache first)
        """
        try:
            # Clear command tree first
            self.bot.tree.clear_commands()
            logger.info("Cleared command tree")
            
            # Re-register all commands
            await self.register_commands()
            
            # Sync with Discord
            synced = await self.bot.tree.sync()
            logger.info(f"Force synced {len(synced)} slash command(s)")
            print(f"🔄 Force synced {len(synced)} slash commands")
            return len(synced)
        except Exception as e:
            logger.error(f"Failed to force sync slash commands: {e}")
            print(f"❌ Failed to force sync: {e}")
            return 0
