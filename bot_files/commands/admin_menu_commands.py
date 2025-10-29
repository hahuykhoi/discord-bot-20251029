# -*- coding: utf-8 -*-
"""
Admin Menu Commands - Menu riêng cho Admin với các lệnh moderation
"""
import discord
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminMenuCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
    
    def register_commands(self):
        """Register admin menu commands"""
        
        @self.bot.command(name='adminmenu', aliases=['amenu'])
        async def admin_menu_command(ctx):
            """Menu admin với các lệnh moderation - chỉ Admin mới thấy được"""
            try:
                # Kiểm tra quyền admin
                if not self.bot_instance.is_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Admin mới có thể sử dụng menu này!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                embed = discord.Embed(
                    title="📋 Tất cả lệnh của Bot",
                    description="Danh sách đầy đủ tất cả lệnh có sẵn trong bot",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🎮 Games & Giải trí",
                    value=(
                        "**🎲 Tài Xỉu:**\n"
                        "`;taixiu tai <tiền>` - Cược tài\n"
                        "`;taixiu xiu <tiền>` - Cược xỉu\n"
                        "`;taixiustats` - Thống kê tài xỉu\n"
                        "**✂️ Kéo Búa Bao:**\n"
                        "`;rps <tiền>` - Chơi RPS (buttons)\n"
                        "**🎰 Slot Machine:**\n"
                        "`;slot <tiền>` - Quay slot\n"
                        "**🃏 Blackjack:**\n"
                        "`;blackjack <tiền>` - Chơi blackjack\n"
                        "**🪙 Flip Coin:**\n"
                        "`;flip heads/tails <tiền>` - Tung xu"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🏆 Weekly Leaderboard & Competition",
                    value=(
                        "`;weeklytop` / `;bangdua` - Bảng đua hàng tuần\n"
                        "`;myleaderboard` / `;hangtoi` - Thứ hạng cá nhân\n"
                        "`;weeklyhistory` / `;lichsutop` - Lịch sử các tuần\n"
                        "`;resetweekly` - Reset tuần và trao thưởng (Admin)\n"
                        "**🏅 Phần thưởng Weekly:**\n"
                        "🥇 TOP 1: 2,000 EXP Rare\n"
                        "🥈 TOP 2: 1,000 EXP Rare\n"
                        "🥉 TOP 3: 500 EXP Rare"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="💰 Tiền tệ & Ví",
                    value=(
                        "`;wallet` - Xem số dư ví chung\n"
                        "`;wallet top` - Top người giàu nhất\n"
                        "`;daily` - Nhận tiền hàng ngày\n"
                        "`;dailystats` - Thống kê daily\n"
                        "`;walletreload` - Nhận role Con Bạc + 100k\n"
                        "**💡 Lưu ý Ví chung:**\n"
                        "• Tất cả games dùng chung ví tiền\n"
                        "• Số dư ban đầu: 1,000 xu"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="👑 Admin & Moderation",
                    value=(
                        "`;admin` - Quản lý admin\n"
                        "`;supremeadmin` - Supreme admin\n"
                        "`;warn @user <lý do>` - Cảnh báo user\n"
                        "`;warnings @user` - Xem cảnh báo\n"
                        "`;mute @user <time> <lý do>` - Mute user\n"
                        "`;unmute @user` - Unmute user\n"
                        "`;checkpermissions` - Quản lý quyền\n"
                        "`;protectnick add/remove <nickname>` - Bảo vệ nickname admin (AI-Powered)\n"
                        "`;adminmenu` / `;amenu` - Menu admin tổng hợp"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🤖 AI & Bot Info",
                    value=(
                        "`;ai <câu hỏi>` - Hỏi AI\n"
                        "`;debug <link>` - Debug Python code với AI\n"
                        "`;preview <link>` - Preview code với AI\n"
                        "@bot <tin nhắn>` - Chat với AI (mention bot)\n"
                        "`;status` - Trạng thái bot (CPU, RAM, ping)\n"
                        "`;nhom` - Giới thiệu về bot creator\n"
                        "`;help` - Hướng dẫn sử dụng bot\n"
                        "`;ping` - Kiểm tra bot hoạt động"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🌐 Network & API",
                    value=(
                        "`;network` - Chẩn đoán kết nối và ping\n"
                        "`;networkstats` - Thống kê network chi tiết\n"
                        "`;tiktok <username>` - Thông tin TikTok\n"
                        "`;github <username>` - Thông tin GitHub\n"
                        "`;apistatus` - Trạng thái API Gemini (admin)\n"
                        "`;nextapi` - Chuyển API tiếp theo (admin)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="💤 AFK & Communication",
                    value=(
                        "`;afk [lý do]` - Đặt trạng thái AFK\n"
                        "`;unafk` - Bỏ trạng thái AFK\n"
                        "`;afklist` - Danh sách users AFK\n"
                        "`;dm @user <nội dung>` - Gửi DM\n"
                        "`;send <channel_id> <nội dung>` - Gửi tin nhắn\n"
                        "`;feedback <nội dung>` - Gửi feedback\n"
                        "`;announce <nội dung>` - Thông báo (Admin)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🎵 Media & System",
                    value=(
                        "`;spotify <url>` - Hiển thị nhạc Spotify (admin)\n"
                        "`;stopmusic` - Dừng trạng thái nhạc (admin)\n"
                        "`;join` - Bot join voice channel\n"
                        "`;video <tên>` - Gửi video\n"
                        "`;videolist` - Danh sách video\n"
                        "`;setstatus <nội dung>` - Cập nhật status bot (admin)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🤖 AI-Powered Protection",
                    value=(
                        "**🛡️ Admin Nickname Protection:**\n"
                        "`;protectnick add <nickname>` - Bảo vệ nickname admin\n"
                        "`;protectnick remove <nickname>` - Gỡ bỏ bảo vệ\n"
                        "`;protectnick list` - Xem danh sách được bảo vệ\n"
                        "**🔍 AI Detection Features:**\n"
                        "• Phát hiện biến thể Unicode (𝐂𝐥𝐚𝐮𝐝𝐞, Ċłαυđē)\n"
                        "• Phát hiện leet speak (C|@ud3, Cl4ude)\n"
                        "• Tự động khôi phục nickname cũ\n"
                        "• Tích hợp Gemini AI + Basic Detection"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="⚡ Special Systems",
                    value=(
                        "**🎯 Game Balance:**\n"
                        "`;unluck @user` - Unlucky system (Admin)\n"
                        "`;give @user <xu>` - Give tiền (Admin)\n"
                        "`;resetuserdata` - Reset tất cả xu (Supreme Admin)\n"
                        "**🚫 Moderation:**\n"
                        "`;ban <user_id>` / `;unban <user_id>` - Ban system (Supreme Admin)\n"
                        "`;xoa @user` - Auto delete tin nhắn (Admin)\n"
                        "`;purge <số>` / `;purge all` - Xóa tin nhắn hàng loạt (Admin)\n"
                        "`;antiabuse` - Hệ thống chống xúc phạm bot (Admin)\n"
                        "`;firedelete` - Xóa tin nhắn bằng 🔥 (Admin)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🎉 Giveaway System (Slash Commands)",
                    value=(
                        "**🎁 Tạo Giveaway:**\n"
                        "`/giveaway <winners> <duration> <prize>` - Tạo giveaway mới (Admin)\n"
                        "`/giveaway_list` - Xem danh sách giveaway đang diễn ra\n"
                        "**🚫 Blacklist:**\n"
                        "`/giveaway_blacklist @user` - Cấm user tham gia (Admin)\n"
                        "`/giveaway_unblacklist @user` - Gỡ cấm user (Admin)\n"
                        "**🎯 Tham gia:** Nhấn nút 🎉 để tham gia, 👥 để xem người tham gia"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🔄 Backup & System",
                    value=(
                        "`;backup` - Git backup system\n"
                        "`;gitconfig` - Cấu hình Git\n"
                        "`;reload` - Reload modules (Supreme)\n"
                        "`;modules` - Danh sách modules\n"
                        "`;viewdms` - Xem DM (Supreme)\n"
                        "`;cleandms` - Xóa DM cũ (Supreme)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🎭 Quản lý Biệt danh (Admin)",
                    value=(
                        "`;nicklock @user <tên>` - Khóa nickname tự động\n"
                        "`;protectnick add <tên>` - Bảo vệ nickname admin\n"
                        "`;protectnick list` - Xem danh sách bảo vệ\n"
                        "`;setnick @user <biệt danh>` - Đổi tên 1 lần\n"
                        "**⚡ Tự động khôi phục khi user copy tên admin**"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🤖 Multi-Bot System (Admin)",
                    value=(
                        "`;multibot list` - Xem danh sách bot\n"
                        "`;sendall <channel_id> [số] <msg>` - Gửi tin nhắn\n"
                        "`;dmall <user_id> [số] <msg>` - Gửi DM\n"
                        "`;setupbot <tên>` - Đổi tên tất cả bot\n"
                        "**📡 Quản lý và sử dụng nhiều bot Discord**"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Lưu ý quan trọng",
                    value=(
                        "• **Prefix**: Tất cả lệnh bắt đầu bằng `;`\n"
                        "• **Rate Limiting**: 1 lệnh/3s cho mỗi user\n"
                        "• **Admin/Supreme Admin**: Bypass rate limiting\n"
                        "• **Games**: Tất cả dùng chung ví tiền, có hệ thống cân bằng\n"
                        "• **Weekly Leaderboard**: Top 1: 2k, Top 2: 1k, Top 3: 500 EXP Rare\n"
                        "• **Unluck System**: Admin có thể làm user 100% thua vĩnh viễn\n"
                        "• **Game Balance**: User ≥600M xu khó thắng hơn, <600M xu được hỗ trợ\n"
                        "• **Menu**: Gõ `;adminmenu` để xem menu admin tương tác"
                    ),
                    inline=False
                )
                
                # Hiển thị quyền của user hiện tại
                if self.bot_instance.is_supreme_admin(ctx.author.id):
                    user_role = "👑 Supreme Admin"
                    role_color = discord.Color.red()
                elif self.bot_instance.is_admin(ctx.author.id):
                    user_role = "🛡️ Admin"
                    role_color = discord.Color.orange()
                else:
                    user_role = "👥 User"
                    role_color = discord.Color.blue()
                
                embed.add_field(
                    name="👤 Quyền của bạn",
                    value=f"{user_role}",
                    inline=True
                )
                
                embed.add_field(
                    name="🔑 Đặc quyền",
                    value=(
                        "• **Supreme Admin**: Tất cả lệnh, không bị giới hạn\n"
                        "• **Admin**: Hầu hết lệnh moderation + đổi tên user\n"
                        "• **User**: Chỉ lệnh cơ bản, không đổi tên được"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🎭 Lệnh đổi tên - Quyền Admin",
                    value=(
                        "`;nickcontrol` - Kiểm soát biệt danh cố định\n"
                        "`;setnick` - Đổi biệt danh một lần\n"
                        "**Bot cần quyền:** Manage Nicknames"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🔄 Reset System - Supreme Admin",
                    value=(
                        "`;resetuser [@user]` - Reset toàn bộ dữ liệu 1 user\n"
                        "`;resetall` - Reset toàn bộ hệ thống (Supreme Admin)\n"
                        "`;resetgames [@user]` - Reset chỉ lịch sử games (Admin)\n"
                        "`;resetmoney [@user]` - Reset chỉ tiền (Admin)\n"
                        "`;resetstats` - Xem thống kê trước khi reset (Admin)"
                    ),
                    inline=False
                )
                
                embed.set_footer(
                    text=f"Tổng cộng hơn 80+ lệnh • AI-Powered Protection • Requested by {ctx.author.display_name} • {datetime.now().strftime('%H:%M')}",
                    icon_url=ctx.author.display_avatar.url
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong admin menu command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi hiển thị menu admin!",
                    mention_author=True
                )
        
        
        @self.bot.command(name='nickmenu')
        async def nickname_menu_command(ctx):
            """Menu chi tiết về các lệnh đổi tên - Chỉ Admin"""
            try:
                # Kiểm tra quyền admin
                if not self.bot_instance.is_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Admin mới có thể xem menu này!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                embed = discord.Embed(
                    title="🎭 Menu Quản lý Biệt danh",
                    description="Hướng dẫn chi tiết các lệnh đổi tên dành cho Admin",
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🔒 Kiểm soát Biệt danh Cố định",
                    value=(
                        "`;nickcontrol set @user <biệt danh>` - Đặt tên cố định\n"
                        "`;nickcontrol remove @user` - Bỏ kiểm soát\n"
                        "`;nickcontrol list` - Xem danh sách kiểm soát\n"
                        "`;nickcontrol status @user` - Xem trạng thái\n"
                        "**⚡ Tự động khôi phục NGAY LẬP TỨC khi user đổi tên**"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="✏️ Đổi tên Thường",
                    value=(
                        "`;setnick @user <biệt danh>` - Đổi tên một lần\n"
                        "**💡 User có thể tự đổi lại sau này**"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Ví dụ sử dụng",
                    value=(
                        "**Kiểm soát cố định:**\n"
                        "`;nickcontrol set @user 🎭 Tên Cố Định`\n"
                        "→ User không thể đổi tên khác\n\n"
                        "**Đổi tên thường:**\n"
                        "`;setnick @user 👑 Tên Tạm Thời`\n"
                        "→ User có thể đổi lại sau"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="⚙️ Yêu cầu hệ thống",
                    value=(
                        "• **Quyền Admin**: Trong danh sách admin bot\n"
                        "• **Bot Permission**: Manage Nicknames\n"
                        "• **Giới hạn**: Không đổi được user có role cao hơn bot"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🔍 So sánh 2 loại lệnh",
                    value=(
                        "**`;nickcontrol`**: Kiểm soát chặt chẽ, tự động khôi phục\n"
                        "**`;setnick`**: Đổi tên đơn giản, user tự do sau đó\n"
                        "**Khuyến nghị**: Dùng nickcontrol cho user cần kiểm soát"
                    ),
                    inline=False
                )
                
                # Hiển thị quyền của user hiện tại
                if self.bot_instance.is_supreme_admin(ctx.author.id):
                    user_role = "👑 Supreme Admin"
                elif self.bot_instance.is_admin(ctx.author.id):
                    user_role = "🛡️ Admin"
                else:
                    user_role = "👥 User"
                
                embed.add_field(
                    name="👤 Quyền của bạn",
                    value=f"{user_role} - Có thể sử dụng tất cả lệnh đổi tên",
                    inline=True
                )
                
                embed.set_footer(
                    text=f"Nickname Menu • Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong nickname menu command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi hiển thị menu nickname!",
                    mention_author=True
                )
