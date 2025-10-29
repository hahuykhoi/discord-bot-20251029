import discord
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CompleteMenuCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
    
    def register_commands(self):
        """Register complete menu command"""
        
        @self.bot.command(name='allmenu', aliases=['fullcommands'])
        async def complete_menu_command(ctx):
            """Menu tổng hợp tất cả lệnh - Hiển thị theo quyền hạn"""
            
            # Kiểm tra quyền hạn
            user_id = ctx.author.id
            is_supreme_admin = self.bot_instance.is_supreme_admin(user_id)
            is_admin = self.bot_instance.is_admin(user_id)
            
            # Xác định role hiển thị
            if is_supreme_admin:
                role_name = "Supreme Admin"
                role_color = discord.Color.gold()
                role_emoji = "👑"
            elif is_admin:
                role_name = "Admin"
                role_color = discord.Color.blue()
                role_emoji = "🛡️"
            else:
                role_name = "User"
                role_color = discord.Color.green()
                role_emoji = "👤"
            
            # Tạo embed chính
            dm_info = "💬 **Admin có thể sử dụng tất cả lệnh qua DM**" if is_admin else "💬 **User thường chỉ có thể dùng lệnh trong server**"
            
            embed = discord.Embed(
                title=f"🎮 MENU TỔNG HỢP - {role_emoji} {role_name.upper()}",
                description=f"**Tất cả lệnh có thể sử dụng với quyền {role_name}**\n"
                           f"Prefix: `;` • Total commands: **{self.count_available_commands(is_supreme_admin, is_admin)}**\n"
                           f"{dm_info}",
                color=role_color,
                timestamp=datetime.now()
            )
            
            # 1. GAME & ECONOMY COMMANDS
            embed.add_field(
                name="🎮 GAME & ECONOMY",
                value=(
                    "**`;balance`** - Xem số xu hiện có\n"
                    "   💡 *Hiển thị số xu trong tài khoản*\n\n"
                    
                    "**`;daily`** - Nhận xu hàng ngày\n"
                    "   💰 *Nhận 50k-200k xu mỗi ngày (cooldown 24h)*\n\n"
                    
                    "**`;flip <số xu>`** - Tung xu may rủi\n"
                    "   🎲 *Ví dụ: `;flip 10000` - Thắng x2, thua mất hết*\n\n"
                    
                    "**`;blackjack <số xu>`** - Chơi blackjack\n"
                    "   🃏 *Ví dụ: `;blackjack 5000` - Đánh bài với bot*\n\n"
                    
                    "**`;leaderboard`** - Bảng xếp hạng\n"
                    "   🏆 *Top 10 người giàu nhất server*\n\n"
                    
                    "**`;unluck`** - Kiểm tra trạng thái xui xẻo\n"
                    "   🍀 *Xem có bị admin đánh dấu xui không*"
                ),
                inline=False
            )
            
            # 2. GETKEY SYSTEM
            embed.add_field(
                name="🔑 GETKEY SYSTEM",
                value=(
                    "**`;getkey`** - Tạo link vượt link4m\n"
                    "   🔗 *Tạo link kiếm xu, gửi qua DM*\n\n"
                    
                    "**`;checkkey <key>`** - Check key nhận xu\n"
                    "   💰 *Ví dụ: `;checkkey mttoolsrv-abc123`*\n"
                    "   💎 *Nhận 500,000 xu khi thành công*\n\n"
                    
                    "**📊 Thông tin:**\n"
                    "   🔢 *Giới hạn: 5 lần/user (tối đa 2.5M xu)*\n"
                    "   🚫 *Cảnh báo: Nghiêm cấm bypass = cấm 1h*\n"
                    "   ⏰ *Không giới hạn thời gian sử dụng*"
                ),
                inline=False
            )
            
            # 3. SHOP SYSTEM
            embed.add_field(
                name="🛒 SHOP SYSTEM",
                value=(
                    "**`;shop`** - Xem cửa hàng sản phẩm số\n"
                    "   🏪 *Hiển thị tất cả sản phẩm có sẵn*\n\n"
                    
                    "**`;buy gmail`** - Mua Gmail 1 tuần\n"
                    "   📧 *Giá: 1,000,000 xu*\n"
                    "   ⏰ *Thời hạn sử dụng: 1 tuần*\n\n"
                    
                    "**`;buy tiktok`** - Mua TikTok account\n"
                    "   📱 *Giá: 1,000,000 xu*\n"
                    "   ✨ *Tài khoản đã tạo sẵn, chất lượng cao*\n\n"
                    
                    "**📋 Thông tin:**\n"
                    "   🔒 *Giao hàng: Tự động qua DM riêng tư*\n"
                    "   💳 *Thanh toán: Trừ xu từ tài khoản*\n"
                    "   📦 *Kho hàng: Cập nhật liên tục*"
                ),
                inline=False
            )
            
            # 4. SOCIAL & UTILITY
            embed.add_field(
                name="💬 SOCIAL & UTILITY",
                value=(
                    "**`;afk [lý do]`** - Bật chế độ AFK\n"
                    "   😴 *Ví dụ: `;afk đi ăn` - Bot sẽ thông báo khi có người tag*\n\n"
                    
                    "**`;afklist`** - Xem danh sách AFK\n"
                    "   📋 *Hiển thị tất cả người đang AFK*\n\n"
                    
                    "**`;nickname <tên mới>`** - Đổi nickname\n"
                    "   🏷️ *Ví dụ: `;nickname Tên Mới` - Đổi tên hiển thị*\n\n"
                    
                    "**`;github <link>`** - Download từ GitHub\n"
                    "   📥 *Ví dụ: `;github https://github.com/user/repo`*\n\n"
                    
                    "**`;menu`** - Menu này\n"
                    "   📖 *Aliases: commands, cmd, allmenu*"
                ),
                inline=False
            )
            
            # 5. ADMIN COMMANDS (chỉ hiển thị cho admin)
            if is_admin:
                embed.add_field(
                    name="🛡️ ADMIN COMMANDS",
                    value=(
                        "**`;adminmenu`** - Menu admin chi tiết\n"
                        "   📋 *Hiển thị tất cả lệnh admin phân loại*\n\n"
                        
                        "**`;give @user <xu>`** - Tặng xu cho user\n"
                        "   💰 *Ví dụ: `;give @user 100000`*\n\n"
                        
                        "**`;unluck add/remove @user`** - Quản lý xui xẻo\n"
                        "   🍀 *Ví dụ: `;unluck add @user lý do`*\n\n"
                        
                        "**`;shop hanghoa`** - Quản lý kho hàng\n"
                        "   📦 *Xem kho, thêm sản phẩm (text/file)*\n\n"
                        
                        "**`;pendingorders`** - Xem đơn hàng chờ\n"
                        "   📋 *Danh sách đơn hàng cần xử lý*\n\n"
                        
                        "**`;bye <nội dung>`** - Tin nhắn tạm biệt\n"
                        "   👋 *Thiết lập auto-reply khi user rời server*\n\n"
                        
                        "**`;reply <user_id> <nội dung>`** - Auto-reply\n"
                        "   🤖 *Tự động reply khi user nhắn tin*"
                    ),
                    inline=False
                )
            
            # 6. SUPREME ADMIN COMMANDS (chỉ hiển thị cho supreme admin)
            if is_supreme_admin:
                embed.add_field(
                    name="👑 SUPREME ADMIN COMMANDS",
                    value=(
                        "**`;ban <user_id> [lý do]`** - Ban user\n"
                        "   🔨 *Ví dụ: `;ban 123456789 spam`*\n\n"
                        
                        "**`;unban <user_id>`** - Unban user\n"
                        "   ✅ *Ví dụ: `;unban 123456789`*\n\n"
                        
                        "**`;resetuserdata`** - Reset dữ liệu user\n"
                        "   🗑️ *Xóa toàn bộ dữ liệu game của tất cả user*\n\n"
                        
                        "**`;reload [module]`** - Reload bot modules\n"
                        "   🔄 *Ví dụ: `;reload shop` hoặc `;reload` (all)*\n\n"
                        
                        "**`;banhistory [số]`** - Xem lịch sử ban\n"
                        "   📚 *Ví dụ: `;banhistory 10` - 10 ban gần nhất*\n\n"
                        
                        "**`;backup sync/migrate/restore`** - Quản lý backup\n"
                        "   💾 *Sao lưu và khôi phục dữ liệu bot*"
                    ),
                    inline=False
                )
            
            # 7. MODERATION (cho admin)
            if is_admin:
                embed.add_field(
                    name="🔨 MODERATION",
                    value=(
                        "**`;warn @user <lý do>`** - Cảnh cáo user\n"
                        "   ⚠️ *Ví dụ: `;warn @user spam tin nhắn`*\n\n"
                        
                        "**`;mute @user <thời gian>`** - Mute user\n"
                        "   🔇 *Ví dụ: `;mute @user 10m lý do`*\n\n"
                        
                        "**`;channelrestrict add @user #channel`** - Hạn chế kênh\n"
                        "   🚫 *Cấm user vào kênh cụ thể*\n\n"
                        
                        "**`;firedelete on/off`** - Bật/tắt xóa bằng 🔥\n"
                        "   🔥 *React 🔥 vào tin nhắn để xóa*\n\n"
                        
                        "**`;xoa on/off @user`** - Auto delete tin nhắn\n"
                        "   🗑️ *Tự động xóa tin nhắn của user*"
                    ),
                    inline=False
                )
            
            # 8. SYSTEM INFO
            embed.add_field(
                name="⚙️ SYSTEM INFO",
                value=(
                    "**`;status`** - Trạng thái bot\n"
                    "   📊 *Hiển thị uptime, memory, ping*\n\n"
                    
                    "**`;checkpermissions`** - Kiểm tra quyền hạn\n"
                    "   🔍 *Xem quyền hạn của bạn trong bot*\n\n"
                    
                    "**`;nhom`** - Xem nhóm quyền\n"
                    "   👥 *Danh sách Admin và Supreme Admin*\n\n"
                    
                    f"**📋 Thông tin hệ thống:**\n"
                    f"   🔄 *Rate Limit: 1 lệnh/3s (Admin bypass)*\n"
                    f"   📊 *Your Role: {role_emoji} {role_name}*\n"
                    f"   🎯 *Available Commands: {self.count_available_commands(is_supreme_admin, is_admin)}*\n"
                    f"   💬 *DM Support: {'Có (Admin)' if is_admin else 'Không (User thường)'}*"
                ),
                inline=False
            )
            
            # Footer với thông tin chi tiết
            dm_status = "DM: Admin Only" if not is_admin else "DM: Full Access"
            embed.set_footer(
                text=f"Bot Menu System • Role: {role_name} • {dm_status} • Total: {self.count_available_commands(is_supreme_admin, is_admin)} commands",
                icon_url=ctx.author.display_avatar.url
            )
            
            # Thumbnail theo role
            if is_supreme_admin:
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/741090906504290334.png")
            elif is_admin:
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/741090906504290334.png")
            
            # Author
            embed.set_author(
                name=f"{ctx.author.display_name} - Command Menu",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=embed, mention_author=True)
    
    def count_available_commands(self, is_supreme_admin, is_admin):
        """Đếm số lệnh có thể sử dụng theo quyền hạn"""
        base_commands = 20  # Game, GetKey, Shop, Social commands
        
        if is_supreme_admin:
            return base_commands + 16 + 8  # Admin + Supreme Admin commands (thêm reply)
        elif is_admin:
            return base_commands + 16  # Admin commands (thêm reply)
        else:
            return base_commands  # Chỉ user commands
