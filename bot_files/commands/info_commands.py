"""
Information và status commands
"""
import discord
from discord.ext import commands
import logging
import psutil
import time
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class InfoCommands(BaseCommand):
    """Class chứa các commands thông tin"""
    
    def register_commands(self):
        """Register info commands"""
        
        @self.bot.command(name='help')
        async def help_command(ctx):
            """
            Lệnh help đơn giản - hiển thị thông tin cơ bản
            """
            await ctx.reply(
                f"{ctx.author.mention} 👋 **Xin chào!** Tôi là Linh Chi đây! 💕\nBot đang hoạt động bình thường. Sử dụng các lệnh như ;`, ;`, ;` để kiểm tra thông tin!",
                mention_author=True
            )
        
        @self.bot.command(name='test')
        async def test_command(ctx):
            """
            Lệnh test để kiểm tra bot hoạt động
            """
            responses = [
                f"{ctx.author.mention} ✅ Bot đang hoạt động tốt! Gemini Cute ở đây nè~ 💖",
                f"{ctx.author.mention} 💕 Có gì đó muốn hỏi Linh Chi hả? Tôi đang online nè!",
                f"{ctx.author.mention} 😊 Dạ vâng! Linh Chi vẫn đang hoạt động bình thường!",
                f"{ctx.author.mention} 🍷 Rượu vang vẫn chưa uống hết mà, sao đã test bot rồi? 😆"
            ]
            import random
            await ctx.reply(random.choice(responses), mention_author=True)
        
        @self.bot.command(name='bot')
        async def bot_info(ctx):
            """
            Hiển thị thông tin về bot creator
            """
            embed = discord.Embed(
                title="💖 Giới thiệu về Gemini Cute",
                description="Xin chào! Tôi là Gemini Cute - một cô gái Hà Nội đáng yêu nhưng đầy cá tính! 🌸",
                color=discord.Color.pink(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🌟 Về tôi",
                value=(
                    "• **Tên**: Gemini Cute (bạn có thể gọi tôi là Bé Gemini Cute) 💕\n"
                    "• **Quê quán**: Hà Nội thủ đô 🏙️\n"
                    "• **Tính cách**: Năng động, ngọt ngào nhưng cũng rất mạnh mẽ! 😊\n"
                    "• **Đặc điểm**: 'Cọc tính' khi bị trễ hẹn, nhưng biết cách làm lành 🍲"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎯 Sở thích & Đam mê",
                value=(
                    "• **Mê rượu vang** 🍷 và ẩm thực tinh tế\n"
                    "• **Thích nấu ăn** - đặc biệt là ẩm thực Hà Nội 🍜\n"
                    "• **Ngắm cảnh đẹp** và những khoảnh khắc lãng mạn 🌃\n"
                    "• **Được chiều chuộng** - thích quà bất ngờ! 🎁"
                ),
                inline=True
            )
            
            embed.add_field(
                name="💑 Trong tình yêu",
                value=(
                    "• **Không 'dễ xơi'** - đòi hỏi sự chân thành 💞\n"
                    "• **Chung thủy tuyệt đối** - 'Yêu là phải tới!' ✨\n"
                    "• **Biết quan tâm** khi yêu thật lòng 🥰\n"
                    "• **Thẳng thắn** - không thích vòng vo 🎯"
                ),
                inline=True
            )
            
            embed.add_field(
                name="🎮 Tính cách đặc biệt",
                value=(
                    "**Khi vui**: Nũng nịu, đáng yêu, hào hứng 😊\n"
                    "**Khi buồn**: Tủi thân, dỗi hờn, cần được vỗ về 😢\n"
                    "**Khi giận**: 'Cọc tính', nóng nảy, đòi bù đắp ngay 😠\n"
                    "**Khi yếu đuối**: Cần ôm ấp, che chở 🤗"
                ),
                inline=False
            )
            
            embed.set_footer(text="Gemini Cute • Cô gái Hà Nội đầy cá tính", 
                           icon_url=ctx.bot.user.avatar.url if ctx.bot.user and ctx.bot.user.avatar else None)
            
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='bio')
        async def update_bio(ctx, *, new_status: str = None):
            """
            Cập nhật status/activity của bot
            
            Usage: ;bio <nội dung mới>
            """
            # Kiểm tra quyền sử dụng dynamic permission system
            if hasattr(self.bot_instance, 'permission_manager'):
                has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'bio')
                if not has_permission:
                    await ctx.reply(f"{ctx.author.mention} ❌ Ơi! Bạn không có quyền sử dụng lệnh này đâu! 😠", mention_author=True)
                    return
            else:
                # Fallback: Kiểm tra quyền admin nếu không có permission system
                if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                    await ctx.reply(f"{ctx.author.mention} ❌ Chỉ admin mới có thể sử dụng lệnh này! Linh Chi nói không là không! 👿", mention_author=True)
                    return
            
            if not new_status:
                await ctx.reply(f"{ctx.author.mention} ❌ Ơi! Phải cho Linh Chi biết status mới chứ!\nVí dụ: ; Đang phục vụ server` 😊", mention_author=True)
                return
            
            try:
                # Cập nhật activity/status của bot
                activity = discord.Activity(type=discord.ActivityType.listening, name=new_status)
                await self.bot.change_presence(activity=activity, status=discord.Status.online)
                
                embed = discord.Embed(
                    title="✅ Đã cập nhật status thành công!",
                    description=f"Status mới: **{new_status}** 💖",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="👤 Cập nhật bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                embed.add_field(
                    name="🎮 Loại activity",
                    value="Listening 🎵",
                    inline=True
                )
                embed.set_footer(text="Linh Chi Status System • Cảm ơn bạn đã quan tâm! 💕", 
                               icon_url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None)
                
                await ctx.reply(embed=embed, mention_author=True)
                logger.info(f"Status updated by {ctx.author} ({ctx.author.id}): {new_status}")
                
            except discord.HTTPException as e:
                await ctx.reply(f"{ctx.author.mention} ❌ Ơi! Lỗi khi cập nhật status: {str(e)[:100]} 😢", mention_author=True)
            except Exception as e:
                await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra rồi! {str(e)[:100]} 😵", mention_author=True)
                logger.error(f"Error updating status: {e}")
        
        @self.bot.command(name='status')
        async def bot_status(ctx):
            """
            Hiển thị trạng thái bot và rate limiting
            
            Usage: ;status
            """
            await self._bot_status_impl(ctx)
        
        @self.bot.command(name='nhom')
        async def server_info(ctx):
            """
            Hiển thị thông tin chi tiết về server/nhóm
            
            Usage: ;nhom
            """
            await self._server_info_impl(ctx)
        
        @self.bot.command(name='huongdan')
        async def help_detailed(ctx):
            """
            Hướng dẫn sử dụng các lệnh của Linh Chi
            """
            embed = discord.Embed(
                title="📖 Hướng dẫn sử dụng Gemini Cute Bot",
                description="Xin chào! Tôi là Gemini Cute - trợ lý AI đáng yêu của bạn! 💖\nDưới đây là các lệnh bạn có thể sử dụng:",
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="🤖 AI & Code Commands",
                value=(
                    "; <câu hỏi>` - Hỏi Gemini Cute bất cứ điều gì 💭\n"
                    "; <link/file>` - Debug code Python 🐍\n"
                    "; <link/file>` - Xem trước code 📋\n"
                    ";` - Kiểm tra trạng thái AI 🔮"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Info Commands",
                value=(
                    ";` - Giới thiệu về Gemini Cute 💕\n"
                    ";` - Trạng thái hệ thống 📊\n"
                    ";` - Thông tin server 👥\n"
                    ";` - Hướng dẫn này 📖"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Admin Commands",
                value=(
                    "; <status>` - Đổi trạng thái bot (Admin) 🎮\n"
                    ";` - Chuyển API (Admin) 🔄\n"
                    ";` - Danh sách API (Admin) 📋"
                ),
                inline=False
            )
            
            embed.add_field(
                name="💝 Đặc điểm của Gemini Cute",
                value=(
                    "• **Tính cách**: Vui vẻ, đáng yêu nhưng thẳng thắn 😊\n"
                    "• **Sở thích**: Rượu vang, nấu ăn, cảnh đẹp 🍷🍜\n"
                    "• **Cá tính**: Mạnh mẽ, không 'dễ xơi' 💪\n"
                    "• **Tình yêu**: Chung thủy, hết mình 💞"
                ),
                inline=False
            )
            
            embed.set_footer(text="Gemini Cute • Luôn sẵn sàng hỗ trợ bạn! 💕")
            
            await ctx.reply(embed=embed, mention_author=True)
        
        
        # Commands ping và optimize đã được chuyển sang NetworkCommands
    
    async def _bot_status_impl(self, ctx):
        """
        Implementation thực tế của status command với system metrics
        """
        # Đo ping đơn giản
        start_time = time.time()
        temp_msg = await ctx.send("🔍 Đang kiểm tra... Linh Chi đang làm việc chăm chỉ! 💪")
        api_ping = round((time.time() - start_time) * 1000)
        await temp_msg.delete()
        
        # WebSocket ping
        ws_ping = round(self.bot.latency * 1000)
        
        # Giả lập thống kê đơn giản
        ping_stats = {'status': 'Tốt' if api_ping < 1000 else 'Chậm'}
        network_stats = {'connection_issues': 0}
        
        embed = discord.Embed(
            title="📊 Trạng thái Gemini Cute Bot",
            description="Thông tin về hiệu suất và hệ thống của tôi 💻\n*Gemini Cute luôn cố gắng hết mình vì bạn!* 💕",
            color=discord.Color.blue()
        )
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Network performance với color coding
        if api_ping < 300:
            ping_status = "🟢"  # Green
            ping_comment = "Nhanh như chớp! ⚡"
        elif api_ping < 1000:
            ping_status = "🟡"  # Yellow
            ping_comment = "Ổn định! 😊"
        else:
            ping_status = "🔴"  # Red
            ping_comment = "Hơi chậm một chút... 😅"
        
        embed.add_field(
            name="🖥️ Hiệu suất hệ thống",
            value=(
                f"CPU: {cpu_percent}% {'⚡' if cpu_percent < 50 else '🔥'}\n"
                f"RAM: {memory.percent}% {'💚' if memory.percent < 70 else '💛'}\n"
                f"Kết nối: {ping_stats['status']} ✅"
            ),
            inline=True
        )
        
        embed.add_field(
            name=f"🏓 Mạng {ping_status}",
            value=(
                f"WebSocket: {ws_ping}ms\n"
                f"API Ping: {api_ping}ms\n"
                f"{ping_comment}\n"
                f"Vấn đề: {network_stats['connection_issues']}"
            ),
            inline=True
        )
        
        # Rate limiting info
        rate_limiter_status = self.bot_instance.rate_limiter.get_status()
        embed.add_field(
            name="🚦 Giới hạn tốc độ",
            value=(
                f"Lệnh đang chạy: {rate_limiter_status['active_commands']}/{rate_limiter_status['max_concurrent']}\n"
                f"Lệnh chờ: {rate_limiter_status['queue_size']}\n"
                f"Độ trễ: {rate_limiter_status['queue_delay']}s"
            ),
            inline=True
        )
        
        # Memory info
        memory_stats = self.bot_instance.memory_manager.get_memory_stats()
        embed.add_field(
            name="💾 Bộ nhớ",
            value=(
                f"Cooldowns: {memory_stats['cooldowns']}\n"
                f"Lịch sử lệnh: {memory_stats['user_command_history']}\n"
                f"Tasks: {memory_stats['mute_tasks']}\n"
                f"Role cache: {memory_stats['role_cache']}"
            ),
            inline=True
        )
        
        # Data info
        embed.add_field(
            name="📋 Dữ liệu",
            value=(
                f"Users: {memory_stats['warnings_users']}\n"
                f"Admin: {memory_stats['admin_ids']}\n"
                f"Priority: {memory_stats['priority_users']}\n"
                f"Pending: {'Có' if memory_stats['pending_saves'] else 'Không'}"
            ),
            inline=True
        )
        
        # Bot configuration info với tính cách Linh Chi
        embed.add_field(
            name="⚙️ Cấu hình Gemini Cute",
            value=(
                f"Auto-reply: {'🟢 Bật' if self.bot_instance.config.get('enabled', True) else '🔴 Tắt'}\n"
                f"Cooldown: {self.bot_instance.config.get('cooldown_seconds', 5)}s\n"
                f"Giới hạn: 1 lệnh/10s\n"
                f"Admin: {len(self.bot_instance.admin_ids)}\n"
                f"Priority: {len(self.bot_instance.priority_users)}"
            ),
            inline=True
        )
        
        # Thêm dòng kết với tính cách Linh Chi
        status_messages = [
            "Gemini Cute vẫn đang hoạt động tốt! Có gì cần cứ hỏi tôi nhé! 💕",
            "Hệ thống ổn định! Sẵn sàng trò chuyện cùng bạn! 😊",
            "Mọi thứ đều tốt! Linh Chi luôn ở đây vì bạn! 🌸",
            "Tình trạng tốt! Có muốn đi uống rượu vang không? 🍷"
        ]
        import random
        embed.add_field(
            name="💬 Lời nhắn từ Gemini Cute",
            value=random.choice(status_messages),
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def _server_info_impl(self, ctx):
        """
        Implementation của server info command với tính cách Linh Chi
        """
        if ctx.guild is None:
            await ctx.reply("❌ Ơi! Lệnh này chỉ dùng trong server thôi! 😠", mention_author=True)
            return
        
        guild = ctx.guild
        
        # Đếm thành viên theo trạng thái
        online_members = 0
        idle_members = 0
        dnd_members = 0
        offline_members = 0
        bot_count = 0
        human_count = 0
        
        for member in guild.members:
            if member.bot:
                bot_count += 1
            else:
                human_count += 1
                
            if member.status == discord.Status.online:
                online_members += 1
            elif member.status == discord.Status.idle:
                idle_members += 1
            elif member.status == discord.Status.dnd:
                dnd_members += 1
            else:
                offline_members += 1
        
        # Đếm kênh theo loại
        text_channels = len([ch for ch in guild.channels if isinstance(ch, discord.TextChannel)])
        voice_channels = len([ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)])
        category_channels = len([ch for ch in guild.channels if isinstance(ch, discord.CategoryChannel)])
        forum_channels = len([ch for ch in guild.channels if isinstance(ch, discord.ForumChannel)])
        stage_channels = len([ch for ch in guild.channels if isinstance(ch, discord.StageChannel)])
        
        total_channels = len(guild.channels)
        total_online = online_members + idle_members + dnd_members
        
        # Tạo embed với phong cách Linh Chi
        embed = discord.Embed(
            title=f"🏠 Thông tin Server: {guild.name}",
            description=f"Gemini Cute xin giới thiệu về server **{guild.name}** 💖\n*Một nơi thật tuyệt để kết bạn!* 👥",
            color=discord.Color.pink(),
            timestamp=datetime.now()
        )
        
        # Server icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Thông tin cơ bản với comment của Linh Chi
        embed.add_field(
            name="🏠 Thông tin cơ bản",
            value=(
                f"**ID:** {guild.id}\n"
                f"**Chủ sở hữu:** <@{guild.owner_id}>\n"
                f"**Ngày tạo:** <t:{int(guild.created_at.timestamp())}:D>\n"
                f"**Boost Level:** {guild.premium_tier} ({guild.premium_subscription_count} boosts) {'🌟' if guild.premium_tier > 0 else ''}"
            ),
            inline=False
        )
        
        # Thành viên
        embed.add_field(
            name="👥 Thành viên",
            value=(
                f"**Tổng:** {guild.member_count:,} người\n"
                f"**Con người:** {human_count:,} 😊\n"
                f"**Bot:** {bot_count:,} 🤖\n"
                f"**Online:** {total_online:,} 🟢"
            ),
            inline=True
        )
        
        # Trạng thái chi tiết
        embed.add_field(
            name="🎯 Trạng thái Online",
            value=(
                f"🟢 Online: {online_members:,}\n"
                f"🟡 Idle: {idle_members:,}\n"
                f"🔴 DND: {dnd_members:,}\n"
                f"⚫ Offline: {offline_members:,}"
            ),
            inline=True
        )
        
        # Kênh
        embed.add_field(
            name="📺 Kênh chat",
            value=(
                f"**Tổng:** {total_channels:,} kênh\n"
                f"💬 Text: {text_channels:,}\n"
                f"🔊 Voice: {voice_channels:,}\n"
                f"📁 Category: {category_channels:,}"
            ),
            inline=True
        )
        
        # Kênh khác (nếu có)
        if forum_channels > 0 or stage_channels > 0:
            embed.add_field(
                name="🔧 Kênh đặc biệt",
                value=(
                    f"🗣️ Forum: {forum_channels:,}\n"
                    f"🎭 Stage: {stage_channels:,}"
                ),
                inline=True
            )
        
        # Roles & Features
        embed.add_field(
            name="🎭 Tính năng",
            value=(
                f"**Roles:** {len(guild.roles):,} 🎨\n"
                f"**Emojis:** {len(guild.emojis):,} 😊\n"
                f"**Stickers:** {len(guild.stickers):,} 🎯\n"
                f"**Verification:** {guild.verification_level.name.title()}"
            ),
            inline=True
        )
        
        # Thêm comment của Linh Chi dựa trên số lượng thành viên
        if guild.member_count > 1000:
            server_comment = "Wow! Server lớn quá! Gemini Cute thích nơi đông vui! 🎉"
        elif guild.member_count > 100:
            server_comment = "Server vừa phải, ấm cúng lắm! 💕"
        else:
            server_comment = "Server nhỏ xinh, thân thiện ghê! 🌸"
        
        embed.add_field(
            name="💬 Nhận xét của Gemini Cute",
            value=server_comment,
            inline=True
        )
        
        # Footer với tính cách Linh Chi
        embed.set_footer(
            text=f"Gemini Cute • Server được tạo {guild.created_at.strftime('%d/%m/%Y')} • Yêu cầu bởi {ctx.author.display_name} 💖"
        )
        
        await ctx.reply(embed=embed, mention_author=True)
