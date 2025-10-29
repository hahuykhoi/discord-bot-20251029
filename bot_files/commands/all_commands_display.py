# -*- coding: utf-8 -*-
"""
All Commands Display - Hiển thị tất cả lệnh dạng text
"""

import discord
from datetime import datetime

def create_all_commands_embed(user) -> discord.Embed:
    """
    Tạo embed hiển thị tất cả lệnh của bot dạng text
    
    Args:
        user: User yêu cầu
        
    Returns:
        discord.Embed: Embed chứa tất cả lệnh
    """
    embed = discord.Embed(
        title="📋 Tất cả lệnh của Bot",
        description="Danh sách đầy đủ tất cả lệnh có sẵn trong bot",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # Games & Giải trí
    embed.add_field(
        name="🎮 Games & Giải trí:",
        value=(
            "**🎲 Tài Xỉu:**\n"
            "`;taixiu tai <tiền>` - Cược tài\n"
            "`;taixiu xiu <tiền>` - Cược xỉu\n"
            "`;taixiu all` - Cược hết số dư\n"
            "`;taixiustats` - Thống kê tài xỉu\n\n"
            "**✂️ Kéo Búa Bao:**\n"
            "`;rps <tiền>` - Chơi RPS (buttons)\n"
            "`;rpsstats` - Thống kê RPS\n"
            "`;rpsleaderboard` - Top RPS\n\n"
            "**🎰 Slot Machine:**\n"
            "`;slot <tiền>` - Quay slot\n"
            "`;slotstats` - Thống kê slot\n"
            "`;slotleaderboard` - Top slot\n\n"
            "**🃏 Blackjack:**\n"
            "`;blackjack <tiền>` - Chơi blackjack\n"
            "`;blackjackstats` - Thống kê blackjack\n\n"
            "**🪙 Flip Coin:**\n"
            "`;flip heads/tails <tiền>` - Tung xu\n"
            "`;flipstats` - Thống kê flip\n"
            "`;flipleaderboard` - Top flip"
        ),
        inline=False
    )
    
    # Weekly Leaderboard & Competition
    embed.add_field(
        name="🏆 Weekly Leaderboard & Competition:",
        value=(
            "`;weeklytop` / `;bangdua` - Bảng đua hàng tuần\n"
            "`;myleaderboard` / `;hangtoi` - Thứ hạng cá nhân\n"
            "`;weeklyhistory` / `;lichsutop` - Lịch sử các tuần\n"
            "`;resetweekly` - Reset tuần và trao thưởng (Admin)\n\n"
            "**🏅 Phần thưởng Weekly:**\n"
            "🥇 TOP 1: 2,000 EXP Rare\n"
            "🥈 TOP 2: 1,000 EXP Rare\n"
            "🥉 TOP 3: 500 EXP Rare"
        ),
        inline=False
    )
    
    # Tiền tệ & Ví
    embed.add_field(
        name="💰 Tiền tệ & Ví:",
        value=(
            "`;wallet` - Xem số dư ví chung\n"
            "`;wallet top` - Top người giàu nhất\n"
            "`;daily` - Nhận tiền hàng ngày\n"
            "`;dailystats` - Thống kê daily\n"
            "`;dailytop` - Top daily\n"
            "`;walletreload` - Nhận role Con Bạc + 100k\n\n"
            "**💡 Lưu ý Ví chung:**\n"
            "• Tất cả games dùng chung ví tiền\n"
            "• Số dư ban đầu: 1,000 xu\n"
            "• Dữ liệu được lưu tự động"
        ),
        inline=False
    )
    
    # Admin & Moderation
    embed.add_field(
        name="👑 Admin & Moderation:",
        value=(
            ";admin add/remove/list` - Quản lý admin\n"
            ";supremeadmin set/remove/info` - Supreme admin\n"
            ";warn @user <lý do>` - Cảnh báo user\n"
            ";warnings @user` - Xem cảnh báo\n"
            ";mute @user <time> <lý do>` - Mute user\n"
            ";unmute @user` - Unmute user\n"
            ";muteinfo [@user]` - Thông tin mute\n"
            ";checkpermissions` - Quản lý quyền\n"
            ";priority add/remove` - Priority users\n"
            ";adminmenu` - Menu admin tổng hợp"
        ),
        inline=False
    )
    
    # Channel & Permissions
    embed.add_field(
        name="🏠 Channel & Permissions:",
        value=(
            ";channelpermission add/remove` - Quyền kênh\n"
            ";channelpermission reset` - Reset kênh\n"
            ";channelrestrict add/remove` - Giới hạn kênh\n"
            ";maintenance open/close` - Đóng/mở bot\n"
            ";maintenance status` - Trạng thái bảo trì\n"
            ";firedelete on/off` - Xóa tin nhắn bằng 🔥\n"
            ";xoa on/off @user` - Auto delete user"
        ),
        inline=False
    )
    
    # AI & Bot Info
    embed.add_field(
        name="🤖 AI & Bot Info:",
        value=(
            ";ai <câu hỏi>` - Hỏi AI\n"
            ";debug <link>` - Debug Python code với AI\n"
            ";preview <link>` - Preview code với AI\n"
            "@bot <tin nhắn>` - Chat với AI (mention bot)\n"
            ";status` - Trạng thái bot (CPU, RAM, ping)\n"
            ";nhom` - Giới thiệu về bot creator\n"
            ";help` - Hướng dẫn sử dụng bot\n"
            ";ping` - Kiểm tra bot hoạt động\n"
            ";serverinfo` - Xem thông tin chi tiết server"
        ),
        inline=False
    )
    
    # Network & API
    embed.add_field(
        name="🌐 Network & API:",
        value=(
            ";network` - Chẩn đoán kết nối và ping\n"
            ";networkstats` - Thống kê network chi tiết\n"
            ";tiktok <username>` - Thông tin TikTok\n"
            ";github <username>` - Thông tin GitHub\n"
            ";apistatus` - Trạng thái API Gemini (admin)\n"
            ";nextapi` - Chuyển API tiếp theo (admin)"
        ),
        inline=False
    )
    
    # AFK & Communication
    embed.add_field(
        name="💤 AFK & Communication:",
        value=(
            ";afk [lý do]` - Đặt trạng thái AFK\n"
            ";unafk` - Bỏ trạng thái AFK\n"
            ";afklist` - Danh sách users AFK\n"
            ";dm <user_id>` hoặc ;dm @user <nội dung>` - Gửi DM\n"
            ";send <channel_id> <nội dung>` - Gửi tin nhắn\n"
            ";feedback <nội dung>` - Gửi feedback\n"
            ";announce <nội dung>` - Thông báo (Admin)\n"
            ";react <message_id>` - Thêm emoji reaction\n"
            ";bye <nội dung>` - Tin nhắn bye tự động"
        ),
        inline=False
    )
    
    # Media & System
    embed.add_field(
        name="🎵 Media & System:",
        value=(
            ";spotify <url>` - Hiển thị nhạc Spotify (admin)\n"
            ";stopmusic` - Dừng trạng thái nhạc (admin)\n"
            ";join` - Bot join voice channel\n"
            ";video <tên>` - Gửi video\n"
            ";video add <URL> <tên>` - Tải video (admin)\n"
            ";videolist` - Danh sách video\n"
            ";setstatus <nội dung>` - Cập nhật status bot (admin)\n"
            ";shop` - EXP Rare Shop\n"
            ";buy exp <số>` - Mua gói EXP"
        ),
        inline=False
    )
    
    # Special Systems
    embed.add_field(
        name="⚡ Special Systems:",
        value=(
            "**🎯 Game Balance:**\n"
            "`;unluck add/remove @user` - Unlucky system (Admin)\n"
            "`;give @user <xu>` - Give tiền (Admin: không giới hạn, User: 36M/ngày)\n"
            "`;resetuserdata` - Reset tất cả xu (Supreme Admin)\n\n"
            "**🚫 Moderation:**\n"
            "`;ban/unban <user_id>` - Ban system (Supreme Admin)\n"
            "`;xoa on/off @user` - Auto delete tin nhắn (Admin)\n"
            "`;firedelete on/off` - Xóa tin nhắn bằng 🔥 (Admin)\n"
            "`;channelrestrict add/remove #kênh` - Giới hạn kênh chat (Admin)"
        ),
        inline=False
    )
    
    # Backup & System Tools
    embed.add_field(
        name="🔄 Backup & System:",
        value=(
            ";backup init/fix/status/sync/restore` - Git backup\n"
            ";gitconfig` - Cấu hình Git\n"
            ";reload [module]` - Reload modules (Supreme)\n"
            ";modules` - Danh sách modules\n"
            ";viewdms [số]` - Xem DM (Supreme)\n"
            ";cleandms` - Xóa DM cũ (Supreme)\n"
            ";feedbackstats` - Thống kê feedback (Supreme)"
        ),
        inline=False
    )
    
    # Admin Money Tools
    embed.add_field(
        name="💎 Admin Money Tools:",
        value=(
            ";givemoney @user <amount>` - Give tiền cá nhân\n"
            ";give @user <amount>` - Give ví chung\n"
            ";resetallmoney` - Reset tất cả tiền\n"
            ";taixiumoney` - Quản lý tiền tài xỉu\n"
            ";walletreload` - Reload wallet system\n"
            ";checkshoppermissions` - Kiểm tra quyền shop"
        ),
        inline=False
    )
    
    # GetKey System
    embed.add_field(
        name="🔑 GetKey System:",
        value=(
            ";getkey` - Tạo link vượt link4m\n"
            ";checkkey <key>` - Check key và nhận 500k xu\n"
            "**💰 Phần thưởng:** 500,000 xu khi check key thành công\n"
            "**⚠️ Chống bypass:** Hệ thống phát hiện bypass tự động\n"
            "**🔢 Giới hạn:** Tối đa 5 lần/user (2.5M xu)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💡 Lưu ý:",
        value=(
            "• **Prefix:** Tất cả lệnh bắt đầu bằng `;`\n"
            "• **Rate Limiting:** 1 lệnh/3s cho mỗi user\n"
            "• **Admin/Supreme Admin:** Bypass rate limiting\n"
            "• **AFK System:** Tự động bỏ AFK khi gửi tin nhắn\n"
            "• **Games:** Tất cả dùng chung ví tiền, có hệ thống cân bằng\n"
            "• **Weekly Leaderboard:** Top 1: 2k, Top 2: 1k, Top 3: 500 EXP Rare\n"
            "• **Unluck System:** Admin có thể làm user 100% thua vĩnh viễn\n"
            "• **Game Balance:** User ≥100M xu có 30% thắng, <100M xu được hỗ trợ 100%\n"
            "• **Menu:** Gõ `;adminmenu` để xem menu admin tương tác"
        ),
        inline=False
    )
    
    embed.set_footer(
        text=f"Yêu cầu bởi {user.display_name} • Tổng cộng hơn 80+ lệnh",
        icon_url=user.display_avatar.url
    )
    
    return embed
