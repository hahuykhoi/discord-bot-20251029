import discord
from discord.ext import commands
import logging
from datetime import datetime
from .base import BaseCommand
from .all_commands_display import create_all_commands_embed

logger = logging.getLogger(__name__)

class GameMenuCommands(BaseCommand):
    """Class chứa lệnh game menu với buttons"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        
    def register_commands(self):
        """Register game menu commands"""
        
        @self.bot.command(name='menu', aliases=['commands', 'cmd'])
        async def menu_command(ctx):
            """Menu đầy đủ với tất cả lệnh của bot - Interactive buttons"""
            try:
                # Import FullMenuView từ full_menu_commands
                from commands.full_menu_commands import FullMenuView
                
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
                        "🛡️ **Moderation** - Lệnh quản lý và kiểm duyệt\n"
                        "🛒 **Shop** - Hệ thống mua bán EXP Rare\n"
                        "🤖 **AI & Utils** - AI commands và tiện ích\n"
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
                        "`;adminmenu` - Menu admin\n"
                        "`;gamemenu` - Menu games\n"
                        "`;shop` - Shop EXP Rare\n"
                        "`;ai <câu hỏi>` - Chat với AI"
                    ),
                    inline=False
                )
                
                embed.set_footer(text=f"Bot Command Center • {datetime.now().strftime('%H:%M')} • Click buttons để explore!")
                
                view = FullMenuView(self.bot_instance)
                await ctx.reply(embed=embed, view=view, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong menu command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {str(e)}", mention_author=True)
        
        @self.bot.command(name='gamemenu')
        async def game_menu_command(ctx):
            """Menu games với buttons - Legacy command"""
            try:
                embed = discord.Embed(
                    title="🎮 Game Menu",
                    description="Menu games cũ - Sử dụng `;menu` để xem menu đầy đủ",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="💡 Lưu ý",
                    value="Sử dụng `;menu` để truy cập menu đầy đủ với tất cả lệnh!",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong gamemenu command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {str(e)}", mention_author=True)

class GameMenuView(discord.ui.View):
    """View chứa các buttons cho game menu"""
    
    def __init__(self, bot_instance, user_id=None):
        super().__init__(timeout=300)  # 5 phút timeout
        self.bot_instance = bot_instance
        self.user_id = user_id
        
        # Chỉ thêm button Admin Menu và Moderation nếu user là admin
        if user_id and not bot_instance.is_admin(user_id):
            # Xóa các button admin cho user thường
            admin_buttons = ['admin_menu', 'moderation']
            for button_id in admin_buttons:
                for item in self.children:
                    if hasattr(item, 'custom_id') and item.custom_id == button_id:
                        self.remove_item(item)
                        break
    
    
    @discord.ui.button(label='🎮 Games', style=discord.ButtonStyle.success, custom_id='games')
    async def games_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho tất cả Games"""
        try:
            embed = discord.Embed(
                title="🎮 Tất cả Games",
                description="Các trò chơi có sẵn trong bot",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🎯 Tài Xỉu:",
                value=(
                    "`;taixiu tai <tiền>` - Cược tài\n"
                    "`;taixiu xiu <tiền>` - Cược xỉu\n"
                    "`;taixiu all` - Cược hết số dư\n"
                    "`;taixiustats` - Thống kê tài xỉu\n"
                ),
                inline=True
            )
            
            embed.add_field(
                name="✏️ Kéo Búa Bao:",
                value=(
                    "`;rps <tiền>` - Chơi RPS\n"
                    "`;rpsstats` - Thống kê RPS\n"
                    "`;rpsleaderboard` - Top RPS\n"
                    "`;rpsmoney` - Số dư RPS"
                ),
                inline=True
            )
            
            embed.add_field(
                name="🎰 Slot Machine:",
                value=(
                    "`;slot <tiền>` - Chơi slot\n"
                    "`;slotstats` - Thống kê slot\n"
                    "`;slotleaderboard` - Top slot\n"
                    "`;slotmoney` - Số dư slot"
                ),
                inline=True
            )
            
            embed.add_field(
                name="🃏 Blackjack:",
                value=(
                    "`;blackjack <tiền>` - Chơi blackjack\n"
                    "`;blackjackstats` - Thống kê blackjack\n"
                    "Tương tác: Buttons (Hit/Stand/Quit)"
                ),
                inline=True
            )
            
            embed.add_field(
                name="🪙 Flip Coin:",
                value=(
                    "`;flipheads/tails <tiền>` - Tung xu\n"
                    "`;flipstats` - Thống kê flip coin\n"
                    "`;flipleaderboard` - Top flip coin"
                ),
                inline=True
            )
            
            
            embed.add_field(
                name="💰 Ví tiền chung:",
                value=(
                    "`;wallet` - Xem số dư\n"
                    "`;wallet top` - Top giàu nhất\n"
                    "`;daily` - Nhận tiền hàng ngày\n"
                    "`;walletreload` - Nhận role + 100k"
                ),
                inline=True
            )
            
            embed.add_field(
                name="💡 Lưu ý:",
                value=(
                    "• Tất cả games dùng chung ví tiền\n"
                    "• Số dư ban đầu: 1,000 xu\n"
                    "• Có thống kê và leaderboard\n"
                    "• Dữ liệu được lưu tự động"
                ),
                inline=False
            )
            
            # Tạo view với buttons để chơi game
            game_view = GamePlayView(self.bot_instance)
            await interaction.response.send_message(embed=embed, view=game_view, ephemeral=True)
        except Exception as e:
            try:
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra khi hiển thị games: {str(e)}",
                    ephemeral=True
                )
            except:
                pass
    
    
    @discord.ui.button(label='💰 Money Tools', style=discord.ButtonStyle.secondary, custom_id='money')
    async def money_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho Money Management Tools"""
        try:
            embed = discord.Embed(
                title="💰 Money Management Tools",
                description="Các công cụ quản lý tiền tệ trong hệ thống",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="💳 Ví tiền chung:",
                value=(
                    "`;wallet` - Xem số dư ví chung\n"
                    "`;wallet top` - Top người giàu nhất\n"
                    "`;walletstats` - Thống kê tiền tệ\n"
                    "`;resetallmoney` - Reset tất cả tiền (Admin)"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎯 Game-specific money:",
                value=(
                    "`;taixiumoney` - Quản lý tiền tài xỉu (Admin)\n"
                    "`;givemoney @user <amount>` - Give tiền (Admin)\n"
                    "`;give @user <amount>` - Give tiền ví chung (Admin)\n"
                    "`;walletreload` - Reload wallet system (Admin)"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎁 Daily & Rewards:",
                value=(
                    "`;daily` - Nhận tiền hàng ngày\n"
                    "`;dailystats` - Thống kê daily\n"
                    "`;dailytop` - Top daily\n"
                    "`;walletreload` - Nhận role Con Bạc + 100k"
                ),
                inline=False
            )
            
            embed.add_field(
                name="💡 Lưu ý:",
                value=(
                    "• Tất cả games dùng chung ví tiền\n"
                    "• Admin có thể give không giới hạn\n"
                    "• Dữ liệu được đồng bộ tự động"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            try:
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra khi hiển thị money tools: {str(e)}",
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label='🛒 Shop', style=discord.ButtonStyle.primary, custom_id='shop')
    async def shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho Shop - Cửa hàng vật phẩm"""
        try:
            embed = discord.Embed(
                title="🛒 Shop - Cửa hàng vật phẩm",
                description="Mua sắm các vật phẩm đặc biệt với xu của bạn!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="⭐ Gói EXP Rare - Cấp Cơ Bản:",
                value=(
                    "1️⃣ **Gói EXP Rare Cơ Bản** - 100 triệu xu\n"
                    "   • Nhận được: 1,000 EXP Rare\n\n"
                    "2️⃣ **Gói EXP Rare Nâng Cao** - 200 triệu xu\n"
                    "   • Nhận được: 2,000 EXP Rare\n\n"
                    "3️⃣ **Gói EXP Rare Siêu Cấp** - 300 triệu xu\n"
                    "   • Nhận được: 3,000 EXP Rare"
                ),
                inline=True
            )
            
            embed.add_field(
                name="🌟 Gói EXP Rare - Cấp Cao:",
                value=(
                    "4️⃣ **Gói EXP Rare Huyền Thoại** - 400 triệu xu\n"
                    "   • Nhận được: 4,000 EXP Rare\n\n"
                    "5️⃣ **Gói EXP Rare Vô Hạn** - 500 triệu xu\n"
                    "   • Nhận được: 5,000 EXP Rare\n\n"
                    "6️⃣ **Gói EXP Rare Thần Thánh** - 600 triệu xu\n"
                    "   • Nhận được: 6,000 EXP Rare"
                ),
                inline=True
            )
            
            embed.add_field(
                name="💫 Gói EXP Rare - Cấp Tối Thượng:",
                value=(
                    "7️⃣ **Gói EXP Rare Vũ Trụ** - 700 triệu xu\n"
                    "   • Nhận được: 7,000 EXP Rare\n\n"
                    "8️⃣ **Gói EXP Rare Siêu Sao** - 800 triệu xu\n"
                    "   • Nhận được: 8,000 EXP Rare\n\n"
                    "9️⃣ **Gói EXP Rare Đỉnh Cao** - 900 triệu xu\n"
                    "   • Nhận được: 9,000 EXP Rare\n\n"
                    "🔟 **Gói EXP Rare Tối Thượng** - 1 tỷ xu\n"
                    "   • Nhận được: 10,000 EXP Rare"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🛍️ Cách mua:",
                value=(
                    "**Đã có thể sử dụng!** ✅\n"
                    "Hệ thống shop EXP Rare đã hoạt động.\n"
                    "Các lệnh có sẵn:\n"
                    "• ;` - Xem shop EXP Rare\n"
                    "• ; exp <số>` - Mua gói EXP (1-10)\n"
                    "• ;` - Xem số EXP Rare hiện có\n"
                    "• ;` - Hoàn thành đơn hàng (Admin)"
                ),
                inline=False
            )
            
            embed.add_field(
                name="💡 Lưu ý quan trọng:",
                value=(
                    "• **Giá tính bằng triệu xu** (100 triệu = 100,000,000 xu)\n"
                    "• **EXP Rare** dùng để nâng cấp nhân vật/kỹ năng\n"
                    "• **Tỷ lệ 1:1** - 1 triệu xu = 10 EXP Rare\n"
                    "• **Gói càng cao** càng có giá trị tốt hơn\n"
                    "• **Không thể hoàn trả** sau khi mua\n"
                    "• Liên hệ admin nếu có vấn đề"
                ),
                inline=False
            )
            
            embed.set_footer(
                text="EXP Rare Shop • 10 gói từ 100 triệu đến 1 tỷ xu • Đã hoạt động!",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            try:
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra khi hiển thị shop: {str(e)}",
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label='📊 Thống Kê', style=discord.ButtonStyle.danger, custom_id='stats')
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho thống kê tổng hợp"""
        embed = discord.Embed(
            title="📊 Thống Kê Game",
            description="Xem thống kê tất cả các trò chơi",
            color=discord.Color.purple()
        )
        
        
        embed.add_field(
            name="✏️ Kéo Búa Bao:",
            value=(
                "`;rpsstats` - Thống kê RPS\n"
                "`;rpsmoney` - Số dư RPS\n"
                "`;rpsleaderboard` - Top RPS"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🎰 Slot Machine:",
            value=(
                "`;slotstats` - Thống kê slot\n"
                "`;slotmoney` - Số dư slot\n"
                "`;slotleaderboard` - Top slot"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🃏 Blackjack:",
            value=(
                "`;blackjackstats` - Xem thống kê blackjack\n"
                "Tương tác: Buttons (Hit/Stand/Quit)"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🎯 Tài Xỉu:",
            value=(
                "`;taixiustats` - Thống kê tài xỉu\n"
                "`;taixiumoney` - Số dư tài xỉu"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🪙 Flip Coin:",
            value=(
                "`;flipstats` - Thống kê flip coin\n"
                "`;flipleaderboard` - Top flip coin"
            ),
            inline=True
        )
        
        embed.add_field(
            name="💳 Ví tiền:",
            value=(
                "`;wallet` - Xem số dư ví chung\n"
                "`;daily` - Nhận tiền hàng ngày\n"
                "`;walletreload` - Nhận role + 100k"
            ),
            inline=True
        )
        
        embed.add_field(
            name="👑 Admin Panel:",
            value=(
                "`;backup` - Hướng dẫn backup\n"
                "`;admin list` - Danh sách admin\n"
                "`;help` - Hướng dẫn tổng quát\n"
                "`;status` - Trạng thái bot"
            ),
            inline=True
        )
        
        embed.add_field(
            name="⚙️ System Tools:",
            value=(
                "`;help` - Hướng dẫn\n"
                "`;status` - Trạng thái bot\n"
                "`;feedback` - Góp ý"
            ),
            inline=True
        )
        
        embed.add_field(
            name="💡 Mẹo:",
            value=(
                "• Chơi có trách nhiệm\n"
                "• Đặt cược hợp lý\n"
                "• Theo dõi thống kê\n"
                "• Tham gia leaderboard"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='🛡️ Moderation', style=discord.ButtonStyle.danger, custom_id='moderation')
    async def moderation_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho tất cả Moderation Tools - chỉ Admin mới thấy được"""
        try:
            # Kiểm tra quyền admin
            if not self.bot_instance.is_admin(interaction.user.id):
                await interaction.response.send_message(
                    "❌ **Không có quyền**\n\n"
                    "Chỉ Admin mới có thể truy cập các công cụ moderation!\n"
                    "Liên hệ Supreme Admin để được cấp quyền.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="🛡️ Moderation Tools - Công cụ kiểm duyệt",
                description="Tất cả hệ thống moderation dành cho Admin",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="🔒 Channel Restriction System",
                value=(
                    "; add @user #channel1 #channel2` - Giới hạn user theo channels\n"
                    "; remove @user` - Bỏ giới hạn channel\n"
                    "; ban @user` - Cấm chat toàn server\n"
                    "; unban @user` - Bỏ cấm chat toàn server\n"
                    "; list` - Xem danh sách bị giới hạn\n"
                    "; check @user` - Kiểm tra trạng thái user"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🚫 Ban System",
                value=(
                    "; <user_id> [lý do]` - Cấm user sử dụng bot (Supreme Admin)\n"
                    "; <user_id> [lý do]` - Bỏ cấm user (Supreme Admin)\n"
                    ";` - Xem danh sách user bị cấm\n"
                    "; [số]` - Lịch sử ban/unban (Supreme Admin)\n"
                    "; <user_id>` - Kiểm tra trạng thái ban"
                ),
                inline=False
            )
            
            # Fire Delete System đã bị vô hiệu hóa
            # embed.add_field(
            #     name="🔥 Fire Delete System",
            #     value=(
            #         "; on` - Bật fire delete cho server\n"
            #         "; off` - Tắt fire delete cho server\n"
            #         "; status` - Xem trạng thái fire delete\n"
            #         "; history [số]` - Lịch sử xóa tin nhắn (Supreme Admin)\n"
            #         "**React emoji 🔥 vào tin nhắn để xóa**"
            #     ),
            #     inline=False
            # )
            
            embed.add_field(
                name="⚡ Auto Delete System",
                value=(
                    "; on @user [lý do]` - Bật auto delete cho user\n"
                    "; off @user [lý do]` - Tắt auto delete cho user\n"
                    "; list` - Xem danh sách user bị auto delete\n"
                    "; history [số]` - Lịch sử auto delete (Supreme Admin)\n"
                    "**Tự động xóa TẤT CẢ tin nhắn của user**"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Warning System",
                value=(
                    "; @user <lý do>` - Cảnh báo user\n"
                    "; @user` - Xem cảnh báo của user\n"
                    "; @user` - Xóa cảnh báo\n"
                    ";` - Xem tất cả cảnh báo"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔇 Mute System",
                value=(
                    "; @user <thời gian> [lý do]` - Mute user\n"
                    "; @user` - Unmute user\n"
                    ";` - Xem danh sách bị mute"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔧 System Tools",
                value=(
                    ";` - Kiểm tra quyền bot (QUAN TRỌNG!)\n"
                    ";` - Menu admin text đầy đủ\n"
                    "; sync` - Backup dữ liệu lên GitHub"
                ),
                inline=False
            )
            
            # Hiển thị quyền
            if self.bot_instance.is_supreme_admin(interaction.user.id):
                user_role = "👑 Supreme Admin - Có thể sử dụng TẤT CẢ lệnh"
            else:
                user_role = "🛡️ Admin - Có thể sử dụng hầu hết lệnh moderation"
            
            embed.add_field(
                name="👤 Quyền của bạn",
                value=user_role,
                inline=False
            )
            
            embed.add_field(
                name="💡 Lưu ý quan trọng",
                value=(
                    "• **Supreme Admin**: Không bao giờ bị ảnh hưởng bởi bất kỳ hệ thống nào\n"
                    "• **Admin**: Không bị Auto Delete, Fire Delete, Channel Restriction\n"
                    "• **Bot cần quyền 'Manage Messages'** để xóa tin nhắn"
                ),
                inline=False
            )
            
            embed.set_footer(
                text=f"Moderation Tools • 6 hệ thống kiểm duyệt • {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Lỗi trong moderation button: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Có lỗi xảy ra. Sử dụng lệnh ;`",
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label='🎵 Media', style=discord.ButtonStyle.secondary, custom_id='media')
    async def media_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho Media & Entertainment"""
        embed = discord.Embed(
            title="🎵 Media & Entertainment",
            description="Các tính năng giải trí và media",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🎵 Âm nhạc:",
            value=(
                ";` - Spotify tools\n"
                ";` - Dừng nhạc\n"
                ";` - Bot join voice channel"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📺 Video & Media:",
            value=(
                ";` - Quản lý video\n"
                ";` - Danh sách video\n"
                "; <link>` - Download TikTok\n"
                ";` - Preview content"
            ),
            inline=True
        )
        
        embed.add_field(
            name="😀 Emoji & Fun:",
            value=(
                ";` - Emoji management\n"
                ";` - Xem bio user\n"
                ";` - Tạo nhóm chat"
            ),
            inline=True
        )
        
        embed.add_field(
            name="💬 Communication:",
            value=(
                ";` - Direct message tools\n"
                ";/cleanupdms` - Quản lý DM\n"
                ";` - Hệ thống feedback\n"
                ";` - Thông báo\n"
                ";` - Chat room"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='🤖 AI & Info', style=discord.ButtonStyle.secondary, custom_id='ai_info')
    async def ai_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho AI & Information Tools"""
        embed = discord.Embed(
            title="🤖 AI & Information Tools", 
            description="Trí tuệ nhân tạo và thông tin hệ thống",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🤖 AI Assistant:",
            value=(
                "; <câu hỏi>` - Hỏi AI\n"
                ";` - Trạng thái AI\n"
                ";` - Chuyển API AI"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📊 Bot Information:",
            value=(
                ";` - Trạng thái bot\n"
                ";` - Thông tin bot\n"
                ";` - Hướng dẫn\n"
                ";` - Debug info"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🌐 Network & API:",
            value=(
                ";` - Kiểm tra ping\n"
                ";` - Thống kê mạng\n"
                ";` - Trạng thái API"
            ),
            inline=True
        )
        
        embed.add_field(
            name="⚙️ System Tools:",
            value=(
                ";` - Bảo trì\n"
                ";` - Cấu hình amen\n"
                ";` - Cấu hình Git\n"
                ";` - Test commands"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='⚙️ System', style=discord.ButtonStyle.secondary, custom_id='system')
    async def system_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button cho System & Channel Tools"""
        embed = discord.Embed(
            title="⚙️ System & Channel Tools", 
            description="Công cụ hệ thống và quản lý kênh",
            color=discord.Color.dark_grey()
        )
        
        embed.add_field(
            name="🏠 Channel Management:",
            value=(
                ";` - Đóng kênh\n"
                ";` - Mở kênh\n"
                ";` - Thiết lập quyền kênh\n"
                ";` - Xóa quyền kênh\n"
                ";` - Danh sách kênh\n"
                ";` - Reset quyền kênh"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 VIP Management:",
            value=(
                ";/viplistChannels` - Danh sách VIP\n"
                ";/vipsendFile` - VIP send tools\n"
                ";/vipsetupTemplate` - VIP setup\n"
                ";/vipdelete/vippurge` - VIP utilities\n"
                ";` - VIP direct message\n"
                ";/vipdeleteChannel` - VIP channels\n"
                ";/vipdeleteCategory` - VIP categories\n"
                ";/vipgiveRole` - VIP roles"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Lưu ý:",
            value=(
                "• VIP commands chỉ dành cho VIP users\n"
                "• Channel commands cần quyền admin\n"
                "• Sử dụng ; <command>` để xem chi tiết"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='📋 Tất cả lệnh', style=discord.ButtonStyle.success, custom_id='all_commands')
    async def all_commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button hiển thị tất cả lệnh của bot dạng text (chỉ riêng người dùng)"""
        try:
            # Tạo embed hiển thị tất cả lệnh
            embed = create_all_commands_embed(interaction.user)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Lỗi trong all_commands_button: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Có lỗi xảy ra khi hiển thị danh sách lệnh!",
                    ephemeral=True
                )
            except:
                pass
    
    async def on_timeout(self):
        """Xử lý khi view timeout"""
        # Disable tất cả buttons
        for item in self.children:
            item.disabled = True

class GamePlayView(discord.ui.View):
    """View chứa các buttons để chơi game trực tiếp"""
    
    def __init__(self, bot_instance):
        super().__init__(timeout=300)  # 5 phút timeout
        self.bot_instance = bot_instance
    
    @discord.ui.button(label='🎯 Tài Xỉu', style=discord.ButtonStyle.success, custom_id='play_taixiu')
    async def play_taixiu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button để chơi Tài Xỉu"""
        try:
            await interaction.response.send_message(
                "🎯 **Tài Xỉu**\n\n"
                "**Cách chơi:**\n"
                "• ; tai <số tiền>` - Cược tài (11-17 điểm)\n"
                "• ; xiu <số tiền>` - Cược xỉu (4-10 điểm)\n"
                "• ; all` - Cược tất cả số dư\n\n"
                "**Ví dụ:** ; tai 100` - Cược 100 xu chọn tài\n\n"
                "**Luật chơi:**\n"
                "Bot sẽ tung 3 xúc xắc, tổng điểm:\n"
                "• **Tài**: 11-17 điểm\n"
                "• **Xỉu**: 4-10 điểm\n"
                "• **Tỷ lệ thắng**: x2",
                ephemeral=True
            )
        except Exception as e:
            try:
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra. Sử dụng lệnh ; tai/xiu <số tiền>`",
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label='✂️ Kéo Búa Bao', style=discord.ButtonStyle.primary, custom_id='play_rps')
    async def play_rps_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button để chơi RPS"""
        try:
            await interaction.response.send_message(
                "🎮 **Kéo Búa Bao (Rock Paper Scissors)**\n\n"
                "**Cách chơi:**\n"
                "• ; rock <số tiền>` - Chọn đá\n"
                "• ; paper <số tiền>` - Chọn giấy\n"
                "• ; scissors <số tiền>` - Chọn kéo\n\n"
                "**Ví dụ:** ; rock 100` - Cược 100 xu chọn đá",
                ephemeral=True
            )
        except Exception as e:
            try:
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra. Sử dụng lệnh ; rock/paper/scissors <số tiền>`",
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label='🎰 Slot Machine', style=discord.ButtonStyle.primary, custom_id='play_slot')
    async def play_slot_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button để chơi Slot Machine"""
        try:
            await interaction.response.send_message(
                "🎰 **Slot Machine**\n\n"
                "**Cách chơi:**\n"
                "• ; <số tiền>` - Quay slot machine\n\n"
                "**Ví dụ:** ; 100` - Cược 100 xu\n\n"
                "**Tỷ lệ thắng:**\n"
                "🍒🍒🍒 - x10\n"
                "🍋🍋🍋 - x5\n"
                "🍊🍊🍊 - x3\n"
                "Hai ký tự giống nhau - x2",
                ephemeral=True
            )
        except Exception as e:
            try:
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra. Sử dụng lệnh ; <số tiền>`",
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label='🪙 Flip Coin', style=discord.ButtonStyle.primary, custom_id='play_flipcoin')
    async def play_flipcoin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button để chơi Flip Coin"""
        try:
            await interaction.response.send_message(
                "🪙 **Flip Coin (Tung Xu)**\n\n"
                "**Cách chơi:**\n"
                "• ; heads <số tiền>` - Cược mặt ngửa\n"
                "• ; tails <số tiền>` - Cược mặt sấp\n\n"
                "**Ví dụ:** ; heads 100` - Cược 100 xu chọn ngửa\n\n"
                "**Tỷ lệ thắng:** x2 (50% cơ hội thắng)",
                ephemeral=True
            )
        except Exception as e:
            try:
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra. Sử dụng lệnh ; heads/tails <số tiền>`",
                    ephemeral=True
                )
            except:
                pass
    
    @discord.ui.button(label='🃏 Blackjack', style=discord.ButtonStyle.danger, custom_id='play_blackjack')
    async def play_blackjack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button hiển thị hướng dẫn Blackjack"""
        embed = discord.Embed(
            title="🃏 Blackjack",
            description="Trò chơi bài 21 điểm kinh điển!",
            color=discord.Color.dark_gold()
        )
        
        embed.add_field(
            name="📋 Cách chơi:",
            value=(
                "**; <số tiền>`** hoặc **; <số tiền>`**\n"
                "; 100` - Đặt cược 100 xu\n"
                "; 500` - Đặt cược 500 xu"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 Tỷ lệ thắng:",
            value=(
                "🃏 **Blackjack**: x2.5\n"
                "✅ **Thắng**: x2\n"
                "🤝 **Hòa**: Hoàn tiền"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Commands:",
            value=(
                ";` - Xem thống kê cá nhân\n"
                ";` - Bảng xếp hạng"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='👑 Admin Menu', style=discord.ButtonStyle.danger, custom_id='admin_menu')
    async def admin_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button Admin Menu - chỉ Admin mới thấy được"""
        try:
            # Kiểm tra quyền admin
            if not self.bot_instance.is_admin(interaction.user.id):
                await interaction.response.send_message(
                    "❌ **Không có quyền**\n\n"
                    "Chỉ Admin mới có thể truy cập menu này!\n"
                    "Liên hệ Supreme Admin để được cấp quyền.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="👑 Admin Menu - Tất cả lệnh Admin",
                description="Danh sách đầy đủ tất cả lệnh dành cho Admin",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🔒 Channel Restriction System",
                value=(
                    "; add @user #channel1 #channel2` - Giới hạn user theo channels\n"
                    "; remove @user` - Bỏ giới hạn channel\n"
                    "; ban @user` - Cấm chat toàn server\n"
                    "; unban @user` - Bỏ cấm chat toàn server\n"
                    "; list` - Xem danh sách bị giới hạn\n"
                    "; check @user` - Kiểm tra trạng thái user"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🚫 Ban System",
                value=(
                    "; <user_id> [lý do]` - Cấm user sử dụng bot (Supreme Admin)\n"
                    "; <user_id> [lý do]` - Bỏ cấm user (Supreme Admin)\n"
                    ";` - Xem danh sách user bị cấm\n"
                    "; [số]` - Lịch sử ban/unban (Supreme Admin)\n"
                    "; <user_id>` - Kiểm tra trạng thái ban"
                ),
                inline=False
            )
            
            # Fire Delete System đã bị vô hiệu hóa
            # embed.add_field(
            #     name="🔥 Fire Delete System",
            #     value=(
            #         "; on` - Bật fire delete cho server\n"
            #         "; off` - Tắt fire delete cho server\n"
            #         "; status` - Xem trạng thái fire delete\n"
            #         "; history [số]` - Lịch sử xóa tin nhắn (Supreme Admin)\n"
            #         "**React emoji 🔥 vào tin nhắn để xóa**"
            #     ),
            #     inline=False
            # )
            
            embed.add_field(
                name="⚡ Auto Delete System",
                value=(
                    "; on @user [lý do]` - Bật auto delete cho user\n"
                    "; off @user [lý do]` - Tắt auto delete cho user\n"
                    "; list` - Xem danh sách user bị auto delete\n"
                    "; history [số]` - Lịch sử auto delete (Supreme Admin)\n"
                    "**Tự động xóa TẤT CẢ tin nhắn của user**"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Warning System",
                value=(
                    "; @user <lý do>` - Cảnh báo user\n"
                    "; @user` - Xem cảnh báo của user\n"
                    "; @user` - Xóa cảnh báo\n"
                    ";` - Xem tất cả cảnh báo"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔇 Mute System",
                value=(
                    "; @user <thời gian> [lý do]` - Mute user\n"
                    "; @user` - Unmute user\n"
                    ";` - Xem danh sách bị mute"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📦 Backup & Data Management",
                value=(
                    "; sync` - Đồng bộ với GitHub (backup trước)\n"
                    "; pull` - Tải code mới từ GitHub\n"
                    "; restore` - Khôi phục dữ liệu từ GitHub\n"
                    "; migrate` - Di chuyển dữ liệu vào data/\n"
                    "; status` - Kiểm tra trạng thái Git\n"
                    "; config` - Xem cấu hình GitHub"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔧 System & Permissions",
                value=(
                    ";` - Kiểm tra quyền bot (QUAN TRỌNG!)\n"
                    ";` - Thông tin bot và server\n"
                    ";` - Kiểm tra độ trễ bot\n"
                    ";` - Menu admin đầy đủ (text)"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎮 Admin Game Commands",
                value=(
                    "; add/remove @user <số tiền>` - Quản lý tiền tài xỉu\n"
                    ";` - Cấp role và tiền cho user\n"
                    "; add/remove @user <số tiền>` - Quản lý ví chung"
                ),
                inline=False
            )
            
            # Hiển thị quyền và thống kê
            if self.bot_instance.is_supreme_admin(interaction.user.id):
                user_role = "👑 Supreme Admin"
                permissions_note = "Có thể sử dụng TẤT CẢ lệnh trên"
            else:
                user_role = "🛡️ Admin"
                permissions_note = "Có thể sử dụng hầu hết lệnh (trừ một số lệnh Supreme Admin)"
            
            embed.add_field(
                name="👤 Quyền của bạn",
                value=f"{user_role}\n{permissions_note}",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Lệnh quan trọng nhất",
                value=(
                    "**;`** - Kiểm tra quyền bot nếu Auto Delete không hoạt động\n"
                    "**;`** - Quản lý chat của users\n"
                    "**;`** - Menu text đầy đủ hơn"
                ),
                inline=False
            )
            
            embed.add_field(
                name="💡 Lưu ý",
                value=(
                    "• **Supreme Admin**: Không bao giờ bị giới hạn bởi bất kỳ hệ thống nào\n"
                    "• **Admin**: Không bị Auto Delete, Fire Delete, Channel Restriction\n"
                    "• **Bot cần quyền 'Manage Messages'** để các tính năng xóa tin nhắn hoạt động"
                ),
                inline=False
            )
            
            embed.set_footer(
                text=f"Admin Menu • {len([f for f in embed.fields if f.name.endswith('System')])} hệ thống moderation • Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Lỗi trong admin menu button: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Có lỗi xảy ra. Sử dụng lệnh ;`",
                    ephemeral=True
                )
            except:
                pass
    
    async def on_timeout(self):
        """Xử lý khi view timeout"""
        # Disable tất cả buttons
        for item in self.children:
            item.disabled = True
