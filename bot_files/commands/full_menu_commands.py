# -*- coding: utf-8 -*-
"""
Full Menu Commands - Menu đầy đủ với tất cả lệnh của bot
"""
import discord
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FullMenuView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=300)
        self.bot_instance = bot_instance
    
    @discord.ui.button(label="🎮 Games", style=discord.ButtonStyle.primary, emoji="🎮")
    async def games_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 Games & Giải Trí",
            description="Tất cả games có sẵn trong bot",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎲 Tài Xỉu",
            value=(
                "`;taixiu tai <tiền>` - Cược tài\n"
                "`;taixiu xiu <tiền>` - Cược xỉu\n"
                "`;taixiustats [@user]` - Thống kê\n"
                "`;give @user <tiền>` - Tặng tiền\n"
                "`;balance [@user]` - Xem số dư"
            ),
            inline=True
        )
        
        embed.add_field(
            name="✂️ Rock Paper Scissors",
            value=(
                "`;rps <tiền>` - Chơi RPS\n"
                "`;rpsstats [@user]` - Thống kê RPS\n"
                "**Dùng buttons để chọn**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🎰 Slot Machine",
            value=(
                "`;slot <tiền>` - Quay slot\n"
                "`;slotstats [@user]` - Thống kê slot\n"
                "**Lưu ý:** Game thuần may rủi"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🃏 Blackjack",
            value=(
                "`;blackjack <tiền>` - Chơi blackjack\n"
                "`;bjstats [@user]` - Thống kê BJ\n"
                "**Dùng buttons:** Hit/Stand/Double"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🪙 Flip Coin",
            value=(
                "`;flip heads <tiền>` - Cược ngửa\n"
                "`;flip tails <tiền>` - Cược sấp\n"
                "`;flipstats [@user]` - Thống kê flip"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🏆 Weekly Leaderboard",
            value=(
                "`;weeklytop` / `;bangdua` - Bảng đua\n"
                "`;myleaderboard` / `;hangtoi` - Rank cá nhân\n"
                "`;weeklyhistory` - Lịch sử tuần\n"
                "`;resetweekly` - Reset tuần (Admin)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎣 Fishing System",
            value=(
                "`;cauca` / `;fishing` - Câu cá\n"
                "`;sell [cá] [số]` - Bán cá\n"
                "`;kho` / `;inventory` - Xem kho cá\n"
                "`;topfish` - BXH câu cá"
            ),
            inline=True
        )
        
        embed.add_field(
            name="💰 Wallet System",
            value=(
                "`;wallet` - Menu ví tiền\n"
                "`;daily` - Nhận thưởng hàng ngày\n"
                "`;walletreload` - Reload ví (Admin)\n"
                "`;wallettop` - Top giàu nhất"
            ),
            inline=True
        )
        
        embed.set_footer(text="Game Balance: ≥100M xu = 30% thắng • Unluck system: 0% thắng vĩnh viễn • Fishing: 5min cooldown")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="👑 Admin Panel", style=discord.ButtonStyle.danger, emoji="👑")
    async def admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hiển thị lệnh Admin và Supreme Admin"""
        # Kiểm tra quyền hạn
        user_id = interaction.user.id
        is_supreme_admin = self.bot_instance.is_supreme_admin(user_id)
        is_admin = self.bot_instance.is_admin(user_id)
        
        if not is_admin and not is_supreme_admin:
            # User thường không có quyền xem
            embed = discord.Embed(
                title="❌ Không có quyền truy cập",
                description="Chỉ Admin và Supreme Admin mới có thể xem menu này!",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🔒 Quyền hạn của bạn:",
                value="👤 **User thường**",
                inline=True
            )
            
            embed.add_field(
                name="📋 Để xem lệnh của bạn:",
                value="Sử dụng các nút khác trong menu",
                inline=True
            )
            
            embed.set_footer(text="Access Denied • Admin Only")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        # Xác định role hiển thị
        if is_supreme_admin:
            role_name = "Supreme Admin"
            role_color = discord.Color.gold()
            role_emoji = "👑"
        else:
            role_name = "Admin"
            role_color = discord.Color.blue()
            role_emoji = "🛡️"
        
        embed = discord.Embed(
            title=f"👑 ADMIN PANEL - {role_emoji} {role_name.upper()}",
            description=f"**Tất cả lệnh quản trị và moderation dành cho {role_name}**\n"
                       f"💬 **Admin có thể sử dụng tất cả lệnh qua DM**",
            color=role_color,
            timestamp=datetime.now()
        )
        
        # 1. ADMIN COMMANDS
        embed.add_field(
            name="🛡️ ADMIN COMMANDS",
            value=(
                "**`;adminmenu`** - Menu admin chi tiết\n"
                "**`;give @user <xu>`** - Tặng xu cho user\n"
                "**`;unluck add/remove @user`** - Quản lý xui xẻo\n"
                "**`;shop hanghoa`** - Quản lý kho hàng\n"
                "**`;pendingorders`** - Xem đơn hàng chờ\n"
                "**`;bye <nội dung>`** - Tin nhắn tạm biệt\n"
                "**`;reply <user_id> <nội dung>`** - Auto-reply"
            ),
            inline=True
        )
        
        # 2. MODERATION COMMANDS
        embed.add_field(
            name="🔨 MODERATION",
            value=(
                "**`;purge <số>`** - Xóa tin nhắn hàng loạt\n"
                "**`;purgeuser @user <số>`** - Xóa tin nhắn của user\n"
                "**`;xoa on/off @user`** - Auto delete tin nhắn\n"
                "**`;channelrestrict add @user #channel`** - Hạn chế kênh\n"
                "**`;antiabuse on/off`** - Hệ thống chống xúc phạm\n"
                "**`;antiabuse stats`** - Thống kê vi phạm"
            ),
            inline=True
        )
        
        # 3. BAN SYSTEM (cho tất cả admin)
        embed.add_field(
            name="🚫 BAN SYSTEM",
            value=(
                "**`;banlist`** - Danh sách user bị ban\n"
                "**`;checkban <user_id>`** - Kiểm tra trạng thái ban\n" +
                ("**`;ban <user_id> [lý do]`** - Ban user\n"
                "**`;unban <user_id> [lý do]`** - Unban user\n"
                "**`;banhistory [số]`** - Lịch sử ban" if is_supreme_admin else 
                "**Chỉ Supreme Admin:** Ban/Unban users")
            ),
            inline=True
        )
        
        # 4. SUPREME ADMIN COMMANDS (chỉ hiển thị cho supreme admin)
        if is_supreme_admin:
            embed.add_field(
                name="👑 SUPREME ADMIN ONLY",
                value=(
                    "**`;resetuserdata`** - Reset dữ liệu user\n"
                    "**`;resetexp`** - Reset tất cả EXP Rare\n"
                    "**`;reload [module]`** - Reload bot modules\n"
                    "**`;backup sync/migrate/restore`** - Quản lý backup\n"
                    "**`;shutdown`** - Tắt bot hoàn toàn (Nguy hiểm!)"
                ),
                inline=False
            )
        
        # 5. SYSTEM MANAGEMENT
        embed.add_field(
            name="⚙️ SYSTEM INFO",
            value=(
                "**`;status`** - Trạng thái bot\n"
                "**`;checkpermissions`** - Kiểm tra quyền hạn\n"
                "**`;nhom`** - Xem nhóm quyền\n"
                f"**Your Role:** {role_emoji} {role_name}\n"
                f"**DM Support:** Full Access"
            ),
            inline=True
        )
        
        embed.set_footer(
            text=f"👑 Admin Panel • {role_name} • All Commands Available • DM Supported",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🛒 Shop", style=discord.ButtonStyle.success, emoji="🛒")
    async def shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛒 Shop System",
            description="Hệ thống mua bán EXP Rare",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👤 User Commands",
            value=(
                "`;shop` - Xem shop EXP Rare\n"
                "`;buy exp <số>` - Mua gói EXP (1-10)\n"
                "`;exprare [@user]` - Xem EXP Rare\n"
                "**Chỉ dùng trong kênh shop**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="👑 Admin Commands",
            value=(
                "`;setshop [#kênh]` - Cấu hình kênh shop\n"
                "`;shopconfig` - Xem cấu hình shop\n"
                "`;stop` - Hoàn thành đơn hàng (trong order)\n"
                "`;refund [lý do]` - Hoàn tiền (trong order)\n"
                "`;giveexp @user <số>` - Trao EXP thủ công"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🎭 Role Management",
            value=(
                "`;role add @Role` - Thêm role truy cập order\n"
                "`;role remove @Role` - Xóa role\n"
                "`;role list` - Xem danh sách role\n"
                "**Quyền:** Admin+"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📦 Gói EXP Rare",
            value=(
                "**Gói 1:** 100M xu → 1,000 EXP\n"
                "**Gói 5:** 500M xu → 5,000 EXP\n"
                "**Gói 10:** 1B xu → 10,000 EXP\n"
                "**Điều kiện:** Chơi ≥10 ván, cược ≥10M"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔧 System Commands",
            value=(
                "`;checkshoppermissions` - Kiểm tra quyền bot\n"
                "`;resetexp` - Reset tất cả EXP (Supreme Admin)\n"
                "**Bot cần quyền:** Manage Channels"
            ),
            inline=True
        )
        
        embed.set_footer(text="Shop System • Kênh riêng cho mua bán • Order channels private")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🤖 AI & Utils", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def ai_utils_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🤖 AI & Utilities",
            description="AI commands và tiện ích khác",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🧠 AI Commands",
            value=(
                "`;ask <câu hỏi>` - Chat với AI\n"
                "Mention bot + câu hỏi\n"
                "Reply tin nhắn bot\n"
                "**Model:** Gemini Pro"
            ),
            inline=True
        )
        
        embed.add_field(
            name="😴 AFK System",
            value=(
                "`;afk [lý do]` - Đặt trạng thái AFK\n"
                "`;unafk` - Bỏ AFK thủ công\n"
                "`;afklist` - Danh sách AFK\n"
                "**Auto unAFK** khi chat"
            ),
            inline=True
        )
        
        embed.add_field(
            name="👋 Bye System",
            value=(
                "`;bye <nội dung>` - Đặt tin nhắn bye (Admin)\n"
                "`;bye off` - Tắt bye system (Admin)\n"
                "`;byelist` - Xem danh sách bye (Admin)\n"
                "**Auto bye** khi user leave"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🎭 Nickname System",
            value=(
                "`;nickcontrol` - Menu kiểm soát nickname (Admin)\n"
                "`;setnick @user <tên>` - Đổi nickname (Admin)\n"
                "**Bot cần quyền:** Manage Nicknames"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📊 Info Commands",
            value=(
                "`;info` - Thông tin bot\n"
                "`;ping` - Kiểm tra ping\n"
                "`;status` - Trạng thái hệ thống\n"
                "`;uptime` - Thời gian hoạt động"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔧 System Commands",
            value=(
                "`;reload [module]` - Reload module (Supreme Admin)\n"
                "`;backup sync/migrate/status` - Backup system\n"
                "`;checkpermissions` - Kiểm tra quyền bot\n"
                "`;purge <số>` - Xóa tin nhắn hàng loạt\n"
                "`;purgeuser @user <số>` - Xóa tin nhắn user"
            ),
            inline=True
        )
        
        embed.set_footer(text="AI System • Utilities • System Management")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🛡️ Anti-Abuse", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def anti_abuse_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛡️ Anti-Abuse System",
            description="Hệ thống chống xúc phạm tự động",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="⚡ Cách hoạt động",
            value=(
                "• Phát hiện khi user tag bot + chửi bới\n"
                "• Phát hiện khi dùng lệnh `;ask` + chửi bới\n"
                "• Tự động xóa tin nhắn xúc phạm\n"
                "• Tự động reply: \"Đỡ ngu hơn m là được\"\n"
                "• Phản hồi ngay lập tức mỗi lần vi phạm\n"
                "• Thống kê vi phạm chi tiết"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👑 Admin Commands",
            value=(
                "`;antiabuse` - Menu hướng dẫn\n"
                "`;antiabuse status` - Xem trạng thái hệ thống\n"
                "`;antiabuse on/off` - Bật/tắt hệ thống\n"
                "`;antiabuse stats` - Thống kê vi phạm\n"
                "`;antiabuse test <text>` - Test phát hiện"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔍 Database từ xúc phạm",
            value=(
                "**Tiếng Việt:** ngu, ngốc, khùng, điên, đần...\n"
                "**Tiếng Anh:** stupid, idiot, dumb, shit...\n"
                "**Viết tắt:** wtf, stfu, dmm, vcl...\n"
                "**Tổng cộng:** 60+ từ xúc phạm"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📊 Thống kê",
            value=(
                "• Tổng số lần phát hiện\n"
                "• Top violators (user vi phạm nhiều)\n"
                "• Vi phạm gần đây với timestamp\n"
                "• Từ xúc phạm được phát hiện\n"
                "• Lưu trữ trong data/anti_abuse_data.json"
            ),
            inline=False
        )
        
        embed.set_footer(text="🛡️ Anti-Abuse System • Bảo vệ bot khỏi xúc phạm • Admin only")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🔄 Reset", style=discord.ButtonStyle.danger, emoji="🔄")
    async def reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔄 Reset System",
            description="Hệ thống reset lịch sử chơi và tài sản",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👑 Supreme Admin Only",
            value=(
                "`;resetuser [@user]` - Reset toàn bộ dữ liệu 1 user\n"
                "`;resetall` - Reset toàn bộ hệ thống\n"
                "**⚠️ CỰC KỲ NGUY HIỂM - KHÔNG THỂ HOÀN TÁC**"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛡️ Admin Commands",
            value=(
                "`;resetgames [@user]` - Reset chỉ lịch sử games\n"
                "`;resetmoney [@user]` - Reset chỉ tiền\n"
                "`;resetstats` - Xem thống kê trước khi reset"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📊 Files Được Reset",
            value=(
                "• **Shared Wallet** - Số dư tiền\n"
                "• **Game Data** - Tài xỉu, RPS, Slot, BJ, Flip\n"
                "• **System Data** - Daily, Shop, Leaderboard\n"
                "• **Backup** - Tự động backup khi reset all"
            ),
            inline=True
        )
        
        embed.add_field(
            name="⚠️ Xác Nhận Bắt Buộc",
            value=(
                "**Reset User:** Reply `CONFIRM` trong 30s\n"
                "**Reset All:** Reply `RESET ALL CONFIRM` trong 60s\n"
                "**Timeout:** Tự động hủy nếu không xác nhận"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔒 Bảo Mật",
            value=(
                "• **Không thể hoàn tác** - Dữ liệu xóa vĩnh viễn\n"
                "• **Backup tự động** - Chỉ cho reset all\n"
                "• **Logging đầy đủ** - Theo dõi mọi hoạt động"
            ),
            inline=True
        )
        
        embed.set_footer(text="⚠️ SỬ DỤNG CẨN THẬN - HÀNH ĐỘNG KHÔNG THỂ HOÀN TÁC")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📋 All Commands", style=discord.ButtonStyle.secondary, emoji="📋")
    async def all_commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📋 Tất Cả Lệnh Bot",
            description="Danh sách đầy đủ mọi lệnh có trong bot",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎮 Games (15+ lệnh)",
            value=(
                "`;taixiu`, `;rps`, `;slot`, `;blackjack`, `;flip`\n"
                "`;weeklytop`, `;daily`, `;wallet`, `;balance`\n"
                "**+ Stats commands cho từng game**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🛡️ Moderation (25+ lệnh)",
            value=(
                "`;ban`, `;unban`, `;unluck`, `;purge`\n"
                "`;xoa`, `;channelrestrict`, `;antiabuse`\n"
                "**+ Management và history commands**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🛒 Shop System (10+ lệnh)",
            value=(
                "`;shop`, `;buy`, `;setshop`, `;role`\n"
                "`;stop`, `;refund`, `;giveexp`\n"
                "**+ Configuration commands**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🤖 AI & Utils (20+ lệnh)",
            value=(
                "`;ask`, `;afk`, `;bye`, `;purge`\n"
                "`;info`, `;ping`, `;reload`, `;backup`\n"
                "**+ System management commands**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔄 Reset System (5 lệnh)",
            value=(
                "`;resetuser`, `;resetall`, `;resetgames`\n"
                "`;resetmoney`, `;resetstats`\n"
                "**⚠️ Cực kỳ nguy hiểm**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📊 Tổng Cộng",
            value=(
                "**80+ lệnh** tích hợp trong bot\n"
                "**6 categories** chính\n"
                "**Multiple permission levels**\n"
                "**Interactive buttons & embeds**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔑 Permission Levels",
            value=(
                "👑 **Supreme Admin** - Tất cả lệnh\n"
                "🛡️ **Admin** - Hầu hết lệnh moderation\n"
                "👥 **User** - Games và basic commands"
            ),
            inline=False
        )
        
        embed.set_footer(text="Sử dụng buttons để xem chi tiết từng category • Total: 80+ commands")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🏠 Home", style=discord.ButtonStyle.success, emoji="🏠")
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏠 Bot Command Center",
            description="Chào mừng đến với menu lệnh đầy đủ của bot!",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📋 Hướng Dẫn Sử Dụng",
            value=(
                "🎮 **Games** - Tất cả games và giải trí\n"
                "👑 **Admin Panel** - Lệnh quản lý và moderation\n"
                "🛒 **Shop** - Hệ thống mua bán EXP Rare\n"
                "🤖 **AI & Utils** - AI commands và tiện ích\n"
                "🛡️ **Anti-Abuse** - Hệ thống chống xúc phạm\n"
                "🔄 **Reset** - Hệ thống reset dữ liệu\n"
                "📋 **All Commands** - Tổng quan tất cả lệnh"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👤 Quyền Của Bạn",
            value=(
                f"**Role:** {'👑 Supreme Admin' if self.bot_instance.is_supreme_admin(interaction.user.id) else '🛡️ Admin' if self.bot_instance.is_admin(interaction.user.id) else '👥 User'}\n"
                f"**Có thể dùng:** {'Tất cả lệnh' if self.bot_instance.is_supreme_admin(interaction.user.id) else 'Hầu hết lệnh' if self.bot_instance.is_admin(interaction.user.id) else 'Lệnh cơ bản'}"
            ),
            inline=True
        )
        
        embed.add_field(
            name="💡 Lưu Ý",
            value=(
                "• **Prefix:** Tất cả lệnh bắt đầu bằng `;`\n"
                "• **Rate Limit:** 1 lệnh/3s (Admin bypass)\n"
                "• **Interactive:** Sử dụng buttons để điều hướng\n"
                "• **Help:** Gõ `;help <lệnh>` để xem chi tiết"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🎯 Quick Access",
            value=(
                "`;fullmenu` - Menu đầy đủ này\n"
                "`;weeklytop` - Bảng xếp hạng tuần\n"
                "`;cauca` - Câu cá kiếm tiền\n"
                "`;ask <câu hỏi>` - Chat với AI\n"
                "`;antiabuse` - Hệ thống chống xúc phạm"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Bot Command Center • {datetime.now().strftime('%H:%M')} • Click buttons để explore!")
        await interaction.response.edit_message(embed=embed, view=self)

class FullMenuCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
    
    def register_commands(self):
        """Register full menu commands"""
        
        @self.bot.command(name='fullmenu')
        async def full_menu_command(ctx):
            """Menu đầy đủ với tất cả lệnh của bot"""
            try:
                embed = discord.Embed(
                    title="🏠 Bot Command Center",
                    description="Chào mừng đến với menu lệnh đầy đủ của bot!",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📋 Hướng Dẫn Sử Dụng",
                    value=(
                        "🎮 **Games** - Tất cả games và giải trí\n"
                        "👑 **Admin Panel** - Lệnh quản lý và moderation\n"
                        "🛒 **Shop** - Hệ thống mua bán EXP Rare\n"
                        "🤖 **AI & Utils** - AI commands và tiện ích\n"
                        "🛡️ **Anti-Abuse** - Hệ thống chống xúc phạm\n"
                        "🔄 **Reset** - Hệ thống reset dữ liệu\n"
                        "📋 **All Commands** - Tổng quan tất cả lệnh"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="👤 Quyền Của Bạn",
                    value=(
                        f"**Role:** {'👑 Supreme Admin' if self.bot_instance.is_supreme_admin(ctx.author.id) else '🛡️ Admin' if self.bot_instance.is_admin(ctx.author.id) else '👥 User'}\n"
                        f"**Có thể dùng:** {'Tất cả lệnh' if self.bot_instance.is_supreme_admin(ctx.author.id) else 'Hầu hết lệnh' if self.bot_instance.is_admin(ctx.author.id) else 'Lệnh cơ bản'}"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="💡 Lưu Ý",
                    value=(
                        "• **Prefix:** Tất cả lệnh bắt đầu bằng `;`\n"
                        "• **Rate Limit:** 1 lệnh/3s (Admin bypass)\n"
                        "• **Interactive:** Sử dụng buttons để điều hướng\n"
                        "• **Help:** Gõ `;help <lệnh>` để xem chi tiết"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Quick Access",
                    value=(
                        "`;fullmenu` - Menu đầy đủ này\n"
                        "`;weeklytop` - Bảng xếp hạng tuần\n"
                        "`;cauca` - Câu cá kiếm tiền\n"
                        "`;ask <câu hỏi>` - Chat với AI\n"
                        "`;antiabuse` - Hệ thống chống xúc phạm"
                    ),
                    inline=False
                )
                
                embed.set_footer(text=f"Bot Command Center • {datetime.now().strftime('%H:%M')} • Click buttons để explore!")
                
                view = FullMenuView(self.bot_instance)
                await ctx.reply(embed=embed, view=view, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong full menu command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {str(e)}", mention_author=True)
        
        # Alias commands
        @self.bot.command(name='allmenu')
        async def all_menu_alias(ctx):
            """Alias cho fullmenu"""
            await full_menu_command(ctx)
        
        @self.bot.command(name='commandcenter')
        async def command_center_alias(ctx):
            """Alias cho fullmenu"""
            await full_menu_command(ctx)
        
        # Lệnh menu đã tồn tại trong game_menu_commands.py
