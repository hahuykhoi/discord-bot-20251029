import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NicknameControlCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.control_file = 'data/nickname_control.json'
        self.controlled_users = {}
        self.load_controlled_users()
        self.setup_commands()
    
    def load_controlled_users(self):
        """Load controlled users from file"""
        try:
            if os.path.exists(self.control_file):
                with open(self.control_file, 'r', encoding='utf-8') as f:
                    self.controlled_users = json.load(f)
                logger.info(f"Loaded {len(self.controlled_users)} controlled users")
            else:
                logger.info("No nickname control file found, creating new")
                self.controlled_users = {}
                self.save_controlled_users()
        except Exception as e:
            logger.error(f"Error loading nickname control data: {e}")
            self.controlled_users = {}
    
    def save_controlled_users(self):
        """Save controlled users to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open(self.control_file, 'w', encoding='utf-8') as f:
                json.dump(self.controlled_users, f, indent=4, ensure_ascii=False)
            logger.info("Nickname control data saved successfully")
        except Exception as e:
            logger.error(f"Error saving nickname control data: {e}")
    
    def setup_commands(self):
        """Setup nickname control commands"""
        
        @self.bot.command(name='nicklock')
        async def nicklock_command(ctx, user: discord.Member = None, *, nickname=None):
            """
            Khóa nickname của user - tự động khôi phục khi họ đổi tên
            
            Usage:
            ;nicklock @user <nickname> - Khóa nickname cố định
            ;nicklock @user remove - Gỡ bỏ khóa
            ;nicklock list - Xem danh sách user bị khóa
            ;nicklock - Hiển thị hướng dẫn
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin mới có thể sử dụng lệnh nicklock!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Hiển thị help nếu không có tham số
            if not user:
                await self.show_help(ctx)
                return
            
            # Xử lý lệnh list
            if isinstance(user, str) and user.lower() == 'list':
                await self.show_controlled_list(ctx)
                return
            
            # Kiểm tra user hợp lệ
            if not isinstance(user, discord.Member):
                embed = discord.Embed(
                    title="❌ User không hợp lệ",
                    description="Vui lòng mention user hợp lệ!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Không thể kiểm soát chính mình
            if user.id == ctx.author.id:
                embed = discord.Embed(
                    title="❌ Không thể tự kiểm soát",
                    description="Bạn không thể kiểm soát nickname của chính mình!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Không thể kiểm soát admin khác
            if self.bot_instance.has_warn_permission(user.id, user.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không thể kiểm soát Admin",
                    description="Không thể kiểm soát nickname của Admin khác!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Xử lý lệnh remove
            if nickname and nickname.lower() == 'remove':
                await self.remove_control(ctx, user)
                return
            
            # Kiểm tra nickname hợp lệ
            if not nickname:
                embed = discord.Embed(
                    title="❌ Thiếu nickname",
                    description="Vui lòng nhập nickname muốn đặt cố định!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value=(
                        "`;nicklock @user <nickname>` - Khóa nickname cố định\n"
                        "`;nicklock @user remove` - Gỡ bỏ khóa"
                    ),
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Kiểm tra độ dài nickname
            if len(nickname) > 32:
                embed = discord.Embed(
                    title="❌ Nickname quá dài",
                    description="Nickname không được vượt quá 32 ký tự!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Thêm user vào danh sách kiểm soát
            await self.add_control(ctx, user, nickname)
    
    async def add_control(self, ctx, user, nickname):
        """Add user to nickname control"""
        try:
            # Lưu nickname hiện tại làm backup
            current_nickname = user.display_name
            
            # Đặt nickname mới
            await user.edit(nick=nickname, reason=f"Nickname control by {ctx.author}")
            
            # Lưu vào database
            user_data = {
                'controlled_nickname': nickname,
                'original_nickname': current_nickname,
                'controlled_by': ctx.author.id,
                'controlled_at': datetime.now().isoformat(),
                'guild_id': ctx.guild.id
            }
            
            self.controlled_users[str(user.id)] = user_data
            self.save_controlled_users()
            
            # Thông báo thành công
            embed = discord.Embed(
                title="✅ Đã thiết lập kiểm soát nickname",
                description=f"User {user.mention} giờ sẽ luôn có nickname: **{nickname}**",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User được kiểm soát",
                value=f"{user.mention} ({user.id})",
                inline=True
            )
            
            embed.add_field(
                name="🏷️ Nickname cố định",
                value=f"**{nickname}**",
                inline=True
            )
            
            embed.add_field(
                name="👮 Được kiểm soát bởi",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.add_field(
                name="🔄 Nickname trước đó",
                value=f"**{current_nickname}**",
                inline=True
            )
            
            embed.add_field(
                name="⚡ Tự động khôi phục",
                value="Nickname sẽ tự động được khôi phục khi user thay đổi",
                inline=False
            )
            
            embed.set_footer(text="Sử dụng ;nicklock @user remove để gỡ bỏ khóa")
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Admin {ctx.author} set nickname control for {user}: {nickname}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Không có quyền",
                description="Bot không có quyền thay đổi nickname của user này!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Giải pháp",
                value="Đảm bảo bot có quyền 'Manage Nicknames' và role bot cao hơn role của user",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Lỗi khi thiết lập kiểm soát",
                description=f"Có lỗi xảy ra: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            logger.error(f"Error setting nickname control: {e}")
    
    async def remove_control(self, ctx, user):
        """Remove user from nickname control"""
        user_id = str(user.id)
        
        if user_id not in self.controlled_users:
            embed = discord.Embed(
                title="⚠️ User không được kiểm soát",
                description=f"User {user.mention} hiện không được kiểm soát nickname!",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Lấy thông tin user
        user_data = self.controlled_users[user_id]
        controlled_nickname = user_data.get('controlled_nickname', 'Unknown')
        
        # Xóa khỏi database
        del self.controlled_users[user_id]
        self.save_controlled_users()
        
        # Thông báo thành công
        embed = discord.Embed(
            title="✅ Đã gỡ bỏ kiểm soát nickname",
            description=f"User {user.mention} không còn bị kiểm soát nickname",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👤 User",
            value=f"{user.mention} ({user.id})",
            inline=True
        )
        
        embed.add_field(
            name="🏷️ Nickname đã kiểm soát",
            value=f"**{controlled_nickname}**",
            inline=True
        )
        
        embed.add_field(
            name="🔓 Trạng thái",
            value="User có thể tự do đổi nickname",
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} removed nickname control for {user}")
    
    async def show_controlled_list(self, ctx):
        """Show list of controlled users"""
        if not self.controlled_users:
            embed = discord.Embed(
                title="📝 Danh sách kiểm soát nickname trống",
                description="Hiện không có user nào được kiểm soát nickname",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;nickcontrol @user <nickname>` để thêm user vào kiểm soát",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        embed = discord.Embed(
            title="📝 Danh sách kiểm soát nickname",
            description=f"Tổng cộng: {len(self.controlled_users)} user",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Hiển thị tối đa 10 user
        count = 0
        for user_id, data in list(self.controlled_users.items())[:10]:
            count += 1
            try:
                user = ctx.guild.get_member(int(user_id))
                if user:
                    user_display = f"{user.mention} ({user.display_name})"
                else:
                    user_display = f"User ID: {user_id} (Không trong server)"
                
                controlled_nickname = data.get('controlled_nickname', 'Unknown')
                controlled_by = data.get('controlled_by', 'Unknown')
                controlled_at = data.get('controlled_at', 'Unknown')
                
                # Parse thời gian
                try:
                    dt = datetime.fromisoformat(controlled_at)
                    time_str = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    time_str = "Unknown"
                
                embed.add_field(
                    name=f"#{count} - {user_display}",
                    value=(
                        f"**Nickname:** {controlled_nickname}\n"
                        f"**Bởi:** <@{controlled_by}>\n"
                        f"**Thời gian:** {time_str}"
                    ),
                    inline=False
                )
                
            except Exception as e:
                logger.error(f"Error displaying controlled user {user_id}: {e}")
        
        if len(self.controlled_users) > 10:
            embed.add_field(
                name="📊 Thống kê",
                value=f"Hiển thị 10/{len(self.controlled_users)} user đầu tiên",
                inline=False
            )
        
        embed.set_footer(text="Sử dụng ;nicklock @user remove để gỡ bỏ khóa")
        await ctx.reply(embed=embed, mention_author=True)
    
    async def show_help(self, ctx):
        """Show help menu"""
        embed = discord.Embed(
            title="🏷️ Nickname Control System",
            description="Kiểm soát nickname của user - tự động khôi phục khi họ đổi tên",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Lệnh quản lý",
            value=(
                "`;nicklock @user <nickname>` - Khóa nickname cố định\n"
                "`;nicklock @user remove` - Gỡ bỏ khóa\n"
                "`;nicklock list` - Xem danh sách user bị khóa"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Tính năng tự động",
            value=(
                "• Tự động khôi phục nickname khi user thay đổi\n"
                "• Hoạt động ngay lập tức khi phát hiện thay đổi\n"
                "• Lưu trữ nickname gốc để backup"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔒 Bảo mật",
            value=(
                "• Chỉ Admin mới có quyền sử dụng\n"
                "• Không thể kiểm soát Admin khác\n"
                "• Không thể tự kiểm soát bản thân"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Ví dụ sử dụng",
            value=(
                "`;nicklock @user Helper Bot` - Khóa nickname cố định\n"
                "`;nicklock @user remove` - Gỡ bỏ khóa\n"
                "`;nicklock list` - Xem danh sách"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Lưu ý",
            value=(
                "• Bot cần quyền 'Manage Nicknames'\n"
                "• Role bot phải cao hơn role của user\n"
                "• Nickname tối đa 32 ký tự"
            ),
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def handle_member_update(self, before, after):
        """Handle member update events to restore controlled nicknames"""
        # Chỉ xử lý thay đổi nickname
        if before.display_name == after.display_name:
            return
        
        user_id = str(after.id)
        
        # Kiểm tra user có được kiểm soát không
        if user_id not in self.controlled_users:
            return
        
        user_data = self.controlled_users[user_id]
        controlled_nickname = user_data.get('controlled_nickname')
        
        # Nếu nickname hiện tại không phải là nickname được kiểm soát
        if after.display_name != controlled_nickname:
            try:
                # Khôi phục nickname
                await after.edit(nick=controlled_nickname, reason="Nickname control - auto restore")
                
                logger.info(f"Auto-restored nickname for {after}: {before.display_name} -> {controlled_nickname}")
                
                # Gửi thông báo cho user (tùy chọn)
                try:
                    embed = discord.Embed(
                        title="🏷️ Nickname đã được khôi phục",
                        description=f"Nickname của bạn đã được tự động khôi phục về: **{controlled_nickname}**",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="📝 Thông tin",
                        value="Nickname của bạn đang được kiểm soát bởi Admin",
                        inline=False
                    )
                    embed.set_footer(text="Liên hệ Admin nếu cần hỗ trợ")
                    
                    await after.send(embed=embed)
                except:
                    # Không thể gửi DM, bỏ qua
                    pass
                    
            except discord.Forbidden:
                logger.warning(f"Cannot restore nickname for {after}: Missing permissions")
            except Exception as e:
                logger.error(f"Error restoring nickname for {after}: {e}")
    
    def register_commands(self):
        """Register all commands"""
        logger.info("Nickname Control commands đã được đăng ký")
