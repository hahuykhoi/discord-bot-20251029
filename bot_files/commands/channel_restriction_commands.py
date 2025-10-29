import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChannelRestrictionCommands:
    """Class quản lý giới hạn kênh chat cho user thường"""
    
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.config_file = 'data/channel_restrictions.json'
        self.restrictions = self.load_restrictions()
        
    def load_restrictions(self):
        """Load cấu hình giới hạn kênh"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "allowed_channels": [],  # Danh sách channel ID được phép
                "restricted_users": {},  # User bị giới hạn đặc biệt
                "enabled": True  # Bật/tắt hệ thống
            }
        except Exception as e:
            logger.error(f"Lỗi khi load channel restrictions: {e}")
            return {
                "allowed_channels": [],
                "restricted_users": {},
                "enabled": True
            }
    
    def save_restrictions(self):
        """Lưu cấu hình giới hạn kênh"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.restrictions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save channel restrictions: {e}")
    
    def is_channel_allowed(self, channel_id):
        """Kiểm tra kênh có được phép không"""
        return channel_id in self.restrictions.get("allowed_channels", [])
    
    def can_user_chat(self, user_id, channel_id):
        """Kiểm tra user có thể chat trong kênh này không"""
        # Nếu hệ thống tắt, cho phép tất cả
        if not self.restrictions.get("enabled", True):
            return True
            
        # Admin và Supreme Admin không bị giới hạn
        if self.bot_instance.is_admin(user_id):
            return True
            
        # Kiểm tra kênh có trong danh sách được phép không
        if self.is_channel_allowed(channel_id):
            return True
            
        # User thường không được chat trong kênh không được phép
        return False
    
    async def delete_unauthorized_message(self, message):
        """Xóa tin nhắn không được phép và thông báo"""
        try:
            # Kiểm tra bot có quyền xóa tin nhắn không
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                logger.warning(f"Bot không có quyền xóa tin nhắn trong kênh {message.channel.name}")
                # Chỉ gửi thông báo mà không xóa tin nhắn
                await self.send_restriction_warning(message)
                return
                
            await message.delete()
            
            # Gửi thông báo riêng tư cho user
            embed = discord.Embed(
                title="❌ Tin nhắn bị xóa",
                description="Bạn không có quyền chat trong kênh này!",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🚫 Kênh bị hạn chế:",
                value=f"#{message.channel.name}",
                inline=True
            )
            
            embed.add_field(
                name="📝 Nội dung bị xóa:",
                value=f"```{message.content[:100]}{'...' if len(message.content) > 100 else ''}```",
                inline=False
            )
            
            # Lấy danh sách kênh được phép
            allowed_channels = []
            for channel_id in self.restrictions.get("allowed_channels", []):
                channel = message.guild.get_channel(channel_id)
                if channel:
                    allowed_channels.append(f"#{channel.name}")
            
            if allowed_channels:
                embed.add_field(
                    name="✅ Kênh được phép chat:",
                    value="\n".join(allowed_channels[:10]),  # Giới hạn 10 kênh
                    inline=False
                )
            else:
                embed.add_field(
                    name="ℹ️ Thông tin:",
                    value="Hiện tại chưa có kênh nào được phép cho user thường",
                    inline=False
                )
            
            embed.set_footer(
                text="Chỉ Admin mới có thể chat ở mọi kênh",
                icon_url=message.author.display_avatar.url
            )
            
            try:
                await message.author.send(embed=embed)
            except:
                # Nếu không gửi được DM, gửi trong kênh và xóa sau 10 giây
                warning_msg = await message.channel.send(
                    f"{message.author.mention} ❌ Bạn không có quyền chat trong kênh này!",
                    delete_after=10
                )
            
            logger.info(f"Đã xóa tin nhắn không được phép từ {message.author} trong #{message.channel.name}")
            
        except discord.Forbidden:
            logger.warning(f"Bot không có quyền xóa tin nhắn trong kênh {message.channel.name}")
            # Gửi thông báo mà không xóa tin nhắn
            await self.send_restriction_warning(message)
        except Exception as e:
            logger.error(f"Lỗi khi xóa tin nhắn không được phép: {e}")
    
    async def send_restriction_warning(self, message):
        """Gửi cảnh báo khi bot không thể xóa tin nhắn"""
        try:
            # Tạo embed cảnh báo
            embed = discord.Embed(
                title="⚠️ Cảnh báo giới hạn kênh",
                description="Bạn không có quyền chat trong kênh này!",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🚫 Kênh bị hạn chế:",
                value=f"#{message.channel.name}",
                inline=True
            )
            
            embed.add_field(
                name="⚠️ Lưu ý:",
                value="Bot không có quyền xóa tin nhắn này",
                inline=True
            )
            
            # Lấy danh sách kênh được phép
            allowed_channels = []
            for channel_id in self.restrictions.get("allowed_channels", []):
                channel = message.guild.get_channel(channel_id)
                if channel:
                    allowed_channels.append(f"#{channel.name}")
            
            if allowed_channels:
                embed.add_field(
                    name="✅ Kênh được phép chat:",
                    value="\n".join(allowed_channels[:5]),  # Giới hạn 5 kênh
                    inline=False
                )
            
            embed.set_footer(
                text="Vui lòng chat trong kênh được phép",
                icon_url=message.author.display_avatar.url
            )
            
            # Gửi DM cho user
            try:
                await message.author.send(embed=embed)
            except:
                # Nếu không gửi được DM, gửi trong kênh và xóa sau 15 giây
                if message.channel.permissions_for(message.guild.me).send_messages:
                    warning_msg = await message.channel.send(
                        f"{message.author.mention} ⚠️ Bạn không có quyền chat trong kênh này!",
                        embed=embed,
                        delete_after=15
                    )
            
            logger.info(f"Đã gửi cảnh báo cho {message.author} về giới hạn kênh {message.channel.name}")
            
        except Exception as e:
            logger.error(f"Lỗi khi gửi cảnh báo giới hạn kênh: {e}")
    
    def register_commands(self):
        """Register channel restriction commands"""
        
        @self.bot.command(name='channelrestrict', aliases=['crestrict'])
        async def channel_restrict_command(ctx, action=None, channel: discord.TextChannel = None):
            """Quản lý giới hạn kênh chat"""
            if action == "add" and channel:
                await self.add_allowed_channel(ctx, channel)
            elif action == "remove" and channel:
                await self.remove_allowed_channel(ctx, channel)
            elif action == "list":
                await self.list_allowed_channels(ctx)
            elif action == "toggle":
                await self.toggle_restrictions(ctx)
            elif action == "status":
                await self.show_restriction_status(ctx)
            elif action == "disable":
                await self.disable_restrictions(ctx)
            else:
                await self.show_restriction_help(ctx)
        
        # Không dùng @self.bot.event ở đây vì sẽ conflict với main event handler
        # Thay vào đó, sẽ được gọi từ main on_message handler
    
    async def check_message_permission(self, message):
        """Kiểm tra tin nhắn và xóa nếu không được phép - được gọi từ main on_message handler"""
        try:
            # Bỏ qua bot messages
            if message.author.bot:
                return True
                
            # Bỏ qua DM
            if not message.guild:
                return True
                
            # Bỏ qua commands
            if message.content.startswith(';'):
                return True
                
            # Kiểm tra quyền chat
            if not self.can_user_chat(message.author.id, message.channel.id):
                await self.delete_unauthorized_message(message)
                return False  # Message bị xóa
                
            return True  # Message được phép
            
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra quyền tin nhắn: {e}")
            return True  # Cho phép nếu có lỗi
    
    async def add_allowed_channel(self, ctx, channel):
        """Thêm kênh vào danh sách được phép"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể quản lý giới hạn kênh!", mention_author=True)
            return
        
        if channel.id in self.restrictions["allowed_channels"]:
            await ctx.reply(f"❌ {channel.mention} đã có trong danh sách được phép!", mention_author=True)
            return
        
        self.restrictions["allowed_channels"].append(channel.id)
        self.save_restrictions()
        
        embed = discord.Embed(
            title="✅ Thêm kênh được phép thành công",
            description=f"Đã thêm {channel.mention} vào danh sách kênh được phép chat",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📝 Kênh được thêm:",
            value=f"{channel.mention} (#{channel.name})",
            inline=True
        )
        
        embed.add_field(
            name="📊 Tổng kênh được phép:",
            value=f"{len(self.restrictions['allowed_channels'])} kênh",
            inline=True
        )
        
        embed.set_footer(text="Channel Restriction Management")
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} đã thêm kênh {channel.name} vào danh sách được phép")
    
    async def remove_allowed_channel(self, ctx, channel):
        """Xóa kênh khỏi danh sách được phép"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể quản lý giới hạn kênh!", mention_author=True)
            return
        
        if channel.id not in self.restrictions["allowed_channels"]:
            await ctx.reply(f"❌ {channel.mention} không có trong danh sách được phép!", mention_author=True)
            return
        
        self.restrictions["allowed_channels"].remove(channel.id)
        self.save_restrictions()
        
        embed = discord.Embed(
            title="✅ Xóa kênh được phép thành công",
            description=f"Đã xóa {channel.mention} khỏi danh sách kênh được phép chat",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📝 Kênh được xóa:",
            value=f"{channel.mention} (#{channel.name})",
            inline=True
        )
        
        embed.add_field(
            name="📊 Tổng kênh được phép:",
            value=f"{len(self.restrictions['allowed_channels'])} kênh",
            inline=True
        )
        
        embed.set_footer(text="Channel Restriction Management")
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} đã xóa kênh {channel.name} khỏi danh sách được phép")
    
    async def list_allowed_channels(self, ctx):
        """Liệt kê các kênh được phép"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể xem danh sách kênh được phép!", mention_author=True)
            return
        
        allowed_channels = self.restrictions.get("allowed_channels", [])
        
        embed = discord.Embed(
            title="📋 Danh sách kênh được phép chat",
            description=f"User thường chỉ có thể chat trong {len(allowed_channels)} kênh sau:",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if allowed_channels:
            channel_list = []
            for i, channel_id in enumerate(allowed_channels, 1):
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    channel_list.append(f"{i}. {channel.mention} (#{channel.name})")
                else:
                    channel_list.append(f"{i}. Channel ID: {channel_id} (Đã bị xóa)")
            
            # Chia thành nhiều field nếu quá dài
            for i in range(0, len(channel_list), 10):
                chunk = channel_list[i:i+10]
                embed.add_field(
                    name=f"📝 Kênh được phép ({i+1}-{min(i+10, len(channel_list))}):",
                    value="\n".join(chunk),
                    inline=False
                )
        else:
            embed.add_field(
                name="📝 Trạng thái:",
                value="Chưa có kênh nào được phép cho user thường",
                inline=False
            )
        
        embed.add_field(
            name="ℹ️ Lưu ý:",
            value=(
                "• Admin và Supreme Admin không bị giới hạn\n"
                "• User thường chỉ chat được trong kênh được phép\n"
                "• Tin nhắn vi phạm sẽ bị xóa tự động"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 Quản lý:",
            value=(
                "• ; add #kênh` - Thêm kênh được phép\n"
                "• ; remove #kênh` - Xóa kênh được phép\n"
                "• ; toggle` - Bật/tắt hệ thống\n"
                "• ; status` - Xem trạng thái"
            ),
            inline=False
        )
        
        embed.set_footer(text="Channel Restriction Management")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def toggle_restrictions(self, ctx):
        """Bật/tắt hệ thống giới hạn kênh"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể bật/tắt hệ thống giới hạn kênh!", mention_author=True)
            return
        
        self.restrictions["enabled"] = not self.restrictions.get("enabled", True)
        self.save_restrictions()
        
        status = "BẬT" if self.restrictions["enabled"] else "TẮT"
        color = discord.Color.green() if self.restrictions["enabled"] else discord.Color.red()
        
        embed = discord.Embed(
            title=f"🔄 Đã {status} hệ thống giới hạn kênh",
            description=f"Hệ thống giới hạn kênh chat hiện đang: **{status}**",
            color=color,
            timestamp=datetime.now()
        )
        
        if self.restrictions["enabled"]:
            embed.add_field(
                name="✅ Hệ thống BẬT:",
                value=(
                    "• User thường chỉ chat được trong kênh được phép\n"
                    "• Admin không bị giới hạn\n"
                    "• Tin nhắn vi phạm sẽ bị xóa"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="❌ Hệ thống TẮT:",
                value=(
                    "• Tất cả user có thể chat ở mọi kênh\n"
                    "• Không có giới hạn nào được áp dụng\n"
                    "• Tin nhắn không bị kiểm tra"
                ),
                inline=False
            )
        
        embed.add_field(
            name="📊 Thống kê:",
            value=f"Có {len(self.restrictions.get('allowed_channels', []))} kênh được phép",
            inline=True
        )
        
        embed.set_footer(text="Channel Restriction Management")
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} đã {status.lower()} hệ thống giới hạn kênh")
    
    async def disable_restrictions(self, ctx):
        """Tắt hệ thống giới hạn kênh (khẩn cấp)"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể tắt hệ thống giới hạn kênh!", mention_author=True)
            return
        
        self.restrictions["enabled"] = False
        self.save_restrictions()
        
        embed = discord.Embed(
            title="🚨 Đã TẮT hệ thống giới hạn kênh (Khẩn cấp)",
            description="Hệ thống giới hạn kênh chat đã được tắt khẩn cấp",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="⚠️ Trạng thái:",
            value="**TẮT** - Tất cả user có thể chat ở mọi kênh",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Để bật lại:",
            value="Sử dụng ; toggle` để bật lại hệ thống",
            inline=False
        )
        
        embed.set_footer(text="Emergency Disable - Channel Restriction System")
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.warning(f"Admin {ctx.author} đã TẮT KHẨN CẤP hệ thống giới hạn kênh")
    
    async def show_restriction_status(self, ctx):
        """Hiển thị trạng thái hệ thống giới hạn"""
        embed = discord.Embed(
            title="📊 Trạng thái hệ thống giới hạn kênh",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Trạng thái hệ thống
        enabled = self.restrictions.get("enabled", True)
        status_text = "🟢 **BẬT**" if enabled else "🔴 **TẮT**"
        embed.add_field(
            name="🔄 Trạng thái hệ thống:",
            value=status_text,
            inline=True
        )
        
        # Số kênh được phép
        allowed_count = len(self.restrictions.get("allowed_channels", []))
        embed.add_field(
            name="📝 Kênh được phép:",
            value=f"**{allowed_count}** kênh",
            inline=True
        )
        
        # Quyền của user hiện tại
        if self.bot_instance.is_admin(ctx.author.id):
            user_status = "👑 **Admin - Không giới hạn**"
        else:
            user_status = "👤 **User thường - Bị giới hạn**"
        
        embed.add_field(
            name="👤 Quyền của bạn:",
            value=user_status,
            inline=True
        )
        
        # Thông tin chi tiết
        if enabled:
            embed.add_field(
                name="ℹ️ Cách hoạt động:",
                value=(
                    "• User thường chỉ chat được trong kênh được phép\n"
                    "• Admin và Supreme Admin không bị giới hạn\n"
                    "• Tin nhắn vi phạm sẽ bị xóa và thông báo\n"
                    "• Commands (bắt đầu bằng `;`) không bị giới hạn"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="ℹ️ Hệ thống đang tắt:",
                value="Tất cả user có thể chat ở mọi kênh mà không bị giới hạn",
                inline=False
            )
        
        embed.set_footer(
            text="Sử dụng ;crestrict để xem thêm lệnh quản lý",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def show_restriction_help(self, ctx):
        """Hiển thị hướng dẫn sử dụng"""
        embed = discord.Embed(
            title="🔒 Hệ thống giới hạn kênh chat",
            description="Quản lý quyền chat của user trong các kênh",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        if self.bot_instance.is_admin(ctx.author.id):
            embed.add_field(
                name="🔧 Lệnh quản lý (Admin):",
                value=(
                    "; add #kênh` - Thêm kênh được phép\n"
                    "; remove #kênh` - Xóa kênh được phép\n"
                    "; list` - Xem danh sách kênh được phép\n"
                    "; toggle` - Bật/tắt hệ thống\n"
                    "; status` - Xem trạng thái hệ thống\n"
                    "; disable` - Tắt khẩn cấp hệ thống"
                ),
                inline=False
            )
        
        embed.add_field(
            name="📋 Cách hoạt động:",
            value=(
                "• **User thường:** Chỉ chat được trong kênh được phép\n"
                "• **Admin:** Không bị giới hạn, chat được ở mọi kênh\n"
                "• **Commands:** Không bị giới hạn (bắt đầu bằng `;`)\n"
                "• **Tin nhắn vi phạm:** Bị xóa và thông báo cho user"
            ),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Lưu ý:",
            value=(
                "• Hệ thống chỉ áp dụng cho tin nhắn thường\n"
                "• Bot messages không bị kiểm tra\n"
                "• DM không bị ảnh hưởng\n"
                "• Admin có thể bật/tắt hệ thống bất cứ lúc nào"
            ),
            inline=False
        )
        
        # Hiển thị trạng thái hiện tại
        enabled = self.restrictions.get("enabled", True)
        status_text = "🟢 BẬT" if enabled else "🔴 TẮT"
        allowed_count = len(self.restrictions.get("allowed_channels", []))
        
        embed.add_field(
            name="📊 Trạng thái hiện tại:",
            value=f"Hệ thống: {status_text} | Kênh được phép: {allowed_count}",
            inline=False
        )
        
        embed.set_footer(
            text="Channel Restriction System",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
