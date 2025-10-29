"""
Supreme Admin management commands - Chỉ có 1 admin tối cao duy nhất
"""
import discord
from discord.ext import commands
import logging
import json
import os
import subprocess
import asyncio
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class SupremeAdminCommands(BaseCommand):
    """Class chứa các commands quản lý Supreme Admin - Administrator tối cao"""
    
    def register_commands(self):
        """Register supreme admin management commands"""
        
        @self.bot.command(name='setsupremeadmin')
        async def set_supreme_admin(ctx, user_id: int = None):
            """
            Đặt Supreme Admin - chỉ có thể thực hiện 1 lần hoặc bởi Supreme Admin hiện tại
            
            Usage: ;setsupremeadmin <user_id>
            """
            await self._set_supreme_admin_impl(ctx, user_id)
        
        @self.bot.command(name='removesupremeadmin')
        async def remove_supreme_admin(ctx):
            """
            Xóa Supreme Admin - chỉ Supreme Admin hiện tại mới có thể thực hiện
            
            Usage: ;removesupremeadmin
            """
            await self._remove_supreme_admin_impl(ctx)
        
        @self.bot.command(name='supremeinfo')
        async def supreme_info(ctx):
            """
            Xem thông tin Supreme Admin hiện tại
            
            Usage: ;supremeinfo
            """
            await self._supreme_info_impl(ctx)
        
        @self.bot.command(name='supremeadmin')
        async def supreme_admin_management(ctx, action: str = None, user_id: int = None):
            """
            Quản lý Supreme Admin với subcommands
            
            Usage: 
            ;supremeadmin set <user_id> - Đặt Supreme Admin
            ;supremeadmin remove - Xóa Supreme Admin
            ;supremeadmin info - Xem thông tin Supreme Admin
            """
            if action is None:
                await self._show_supreme_help(ctx)
                return
            
            action = action.lower()
            
            if action == "set":
                await self._set_supreme_admin_impl(ctx, user_id)
            elif action == "remove":
                await self._remove_supreme_admin_impl(ctx)
            elif action == "info":
                await self._supreme_info_impl(ctx)
            else:
                await self._show_supreme_help(ctx)
        
        @self.bot.command(name='shutdown')
        async def shutdown_bot(ctx):
            """
            Tắt bot bằng cách kill tất cả process Python - CHỈ SUPREME ADMIN
            
            Usage: ;shutdown
            """
            await self._shutdown_bot_impl(ctx)
    
    def load_supreme_admin_config(self) -> dict:
        """Tải cấu hình Supreme Admin từ file"""
        supreme_file = 'data/supreme_admin.json'
        try:
            if os.path.exists(supreme_file):
                with open(supreme_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Tạo file mặc định nếu chưa có
                default_config = {
                    "supreme_admin_id": None,
                    "description": "ID của Administrator tối cao - chỉ có 1 người duy nhất có quyền này",
                    "permissions": [
                        "Quản lý tất cả admin khác",
                        "Sử dụng mọi lệnh của bot", 
                        "Thay đổi cấu hình bot",
                        "Quyền tối cao không thể bị thu hồi"
                    ],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": None
                }
                self.save_supreme_admin_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Lỗi khi tải Supreme Admin config: {e}")
            return {"supreme_admin_id": None}
    
    def save_supreme_admin_config(self, config: dict) -> None:
        """Lưu cấu hình Supreme Admin vào file"""
        supreme_file = 'data/supreme_admin.json'
        try:
            with open(supreme_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu Supreme Admin config thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu Supreme Admin config: {e}")
    
    def get_supreme_admin_id(self) -> int:
        """Lấy ID của Supreme Admin hiện tại"""
        config = self.load_supreme_admin_config()
        return config.get('supreme_admin_id')
    
    def is_supreme_admin(self, user_id: int) -> bool:
        """Kiểm tra xem user có phải là Supreme Admin không"""
        supreme_id = self.get_supreme_admin_id()
        return supreme_id is not None and user_id == supreme_id
    
    async def _set_supreme_admin_impl(self, ctx, user_id: int):
        """Implementation thực tế của set supreme admin command"""
        config = self.load_supreme_admin_config()
        current_supreme_id = config.get('supreme_admin_id')
        
        # Kiểm tra quyền: chỉ có thể set nếu chưa có Supreme Admin hoặc người thực hiện là Supreme Admin hiện tại
        if current_supreme_id is not None and ctx.author.id != current_supreme_id:
            await ctx.reply(
                f"{ctx.author.mention} ❌ **Chỉ Supreme Admin hiện tại mới có thể thay đổi!**\n"
                f"Supreme Admin hiện tại: `{current_supreme_id}`", 
                mention_author=True
            )
            return
        
        if user_id is None:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Vui lòng cung cấp User ID!\n"
                f"Usage: ; set <user_id>`", 
                mention_author=True
            )
            return
        
        # Kiểm tra nếu user_id đã là Supreme Admin
        if current_supreme_id == user_id:
            await ctx.reply(
                f"{ctx.author.mention} ❌ User ID `{user_id}` đã là Supreme Admin!", 
                mention_author=True
            )
            return
        
        # Cập nhật Supreme Admin
        config['supreme_admin_id'] = user_id
        config['last_updated'] = datetime.now().isoformat()
        self.save_supreme_admin_config(config)
        
        # Tạo embed thông báo
        embed = discord.Embed(
            title="👑 Supreme Admin đã được đặt!",
            description=f"**User ID `{user_id}` đã trở thành Supreme Administrator tối cao!**",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🔥 Quyền hạn tối cao",
            value=(
                "• Quản lý tất cả admin khác\n"
                "• Sử dụng mọi lệnh của bot\n" 
                "• Thay đổi cấu hình bot\n"
                "• Quyền không thể bị thu hồi bởi ai khác"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Lưu ý quan trọng",
            value="Chỉ có **1 Supreme Admin duy nhất** tại một thời điểm!",
            inline=False
        )
        
        embed.add_field(
            name="🕐 Thời gian",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        embed.set_footer(text="Supreme Admin system - Quyền tối cao")
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Supreme Admin được đặt: {user_id} bởi {ctx.author} ({ctx.author.id})")
    
    async def _remove_supreme_admin_impl(self, ctx):
        """Implementation thực tế của remove supreme admin command"""
        config = self.load_supreme_admin_config()
        current_supreme_id = config.get('supreme_admin_id')
        
        # Kiểm tra có Supreme Admin không
        if current_supreme_id is None:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Hiện tại không có Supreme Admin nào!", 
                mention_author=True
            )
            return
        
        # Chỉ Supreme Admin hiện tại mới có thể xóa chính mình
        if ctx.author.id != current_supreme_id:
            await ctx.reply(
                f"{ctx.author.mention} ❌ **Chỉ Supreme Admin hiện tại mới có thể xóa chính mình!**\n"
                f"Supreme Admin hiện tại: `{current_supreme_id}`", 
                mention_author=True
            )
            return
        
        # Xóa Supreme Admin
        config['supreme_admin_id'] = None
        config['last_updated'] = datetime.now().isoformat()
        self.save_supreme_admin_config(config)
        
        embed = discord.Embed(
            title="💔 Supreme Admin đã được xóa!",
            description=f"**User ID `{current_supreme_id}` đã không còn là Supreme Admin!**",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="📝 Trạng thái",
            value="Hiện tại không có Supreme Admin nào",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Để đặt Supreme Admin mới",
            value="Sử dụng lệnh ; set <user_id>`",
            inline=False
        )
        
        embed.set_footer(text="Supreme Admin system")
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Supreme Admin {current_supreme_id} đã được xóa bởi chính họ")
    
    async def _supreme_info_impl(self, ctx):
        """Implementation thực tế của supreme info command"""
        config = self.load_supreme_admin_config()
        supreme_id = config.get('supreme_admin_id')
        
        embed = discord.Embed(
            title="👑 Thông tin Supreme Admin",
            color=discord.Color.gold()
        )
        
        if supreme_id is None:
            embed.description = "**Hiện tại không có Supreme Admin nào**"
            embed.add_field(
                name="🔄 Để đặt Supreme Admin",
                value="Sử dụng lệnh ; set <user_id>`",
                inline=False
            )
            embed.color = discord.Color.grey()
        else:
            embed.description = f"**Supreme Admin hiện tại: `{supreme_id}`**"
            
            embed.add_field(
                name="🔥 Quyền hạn tối cao",
                value=(
                    "• Quản lý tất cả admin khác\n"
                    "• Sử dụng mọi lệnh của bot\n"
                    "• Thay đổi cấu hình bot\n" 
                    "• Quyền không thể bị thu hồi"
                ),
                inline=False
            )
            
            # Thêm thông tin thời gian nếu có
            if config.get('last_updated'):
                try:
                    last_updated = datetime.fromisoformat(config['last_updated'])
                    timestamp = int(last_updated.timestamp())
                    embed.add_field(
                        name="🕐 Cập nhật lần cuối",
                        value=f"<t:{timestamp}:F>",
                        inline=True
                    )
                except:
                    pass
        
        embed.add_field(
            name="📊 Thống kê",
            value=f"Tổng admin thường: {len(self.bot_instance.admin_ids)}",
            inline=True
        )
        
        embed.set_footer(text="Supreme Admin system - Chỉ có 1 Supreme Admin duy nhất")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def _show_supreme_help(self, ctx):
        """Hiển thị hướng dẫn sử dụng lệnh supreme admin"""
        embed = discord.Embed(
            title="👑 Supreme Admin Management",
            description="**Quản lý Administrator tối cao - chỉ có 1 người duy nhất**",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📝 Cách sử dụng",
            value=(
                "; set <user_id>` - Đặt Supreme Admin\n"
                "; remove` - Xóa Supreme Admin\n"
                "; info` - Xem thông tin Supreme Admin"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔥 Quyền hạn Supreme Admin",
            value=(
                "• **Quản lý tất cả admin khác**\n"
                "• **Sử dụng mọi lệnh của bot**\n"
                "• **Thay đổi cấu hình bot**\n"
                "• **Quyền tối cao không thể bị thu hồi**"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Quy tắc quan trọng",
            value=(
                "• Chỉ có **1 Supreme Admin** tại một thời điểm\n"
                "• Chỉ Supreme Admin hiện tại mới có thể thay đổi\n"
                "• Nếu chưa có Supreme Admin, ai cũng có thể đặt lần đầu"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Ví dụ",
            value="; set 1264908798003253314`",
            inline=False
        )
        
        embed.set_footer(text="Supreme Admin system - Quyền tối cao tuyệt đối")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def _shutdown_bot_impl(self, ctx):
        """Implementation thực tế của shutdown bot command"""
        # Kiểm tra quyền Supreme Admin
        if not self.is_supreme_admin(ctx.author.id):
            embed = discord.Embed(
                title="❌ Không có quyền truy cập",
                description="**Chỉ Supreme Admin mới có thể tắt bot!**",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🔒 Quyền hạn của bạn:",
                value=f"{'🛡️ Admin' if self.bot_instance.is_admin(ctx.author.id) else '👤 User thường'}",
                inline=True
            )
            
            embed.add_field(
                name="👑 Supreme Admin hiện tại:",
                value=f"`{self.get_supreme_admin_id()}`" if self.get_supreme_admin_id() else "Chưa có",
                inline=True
            )
            
            embed.set_footer(text="Access Denied • Supreme Admin Only")
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Tạo embed xác nhận shutdown
        embed = discord.Embed(
            title="🔴 SHUTDOWN BOT",
            description="**Bạn có chắc chắn muốn tắt bot không?**",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="⚠️ Cảnh báo",
            value=(
                "• Bot sẽ bị tắt hoàn toàn\n"
                "• Tất cả lệnh sẽ ngừng hoạt động\n"
                "• Cần khởi động lại thủ công\n"
                "• Hành động không thể hoàn tác"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 Lệnh sẽ thực hiện",
            value="`taskkill /f /im python.exe`",
            inline=False
        )
        
        embed.add_field(
            name="👑 Được thực hiện bởi",
            value=f"{ctx.author.mention} (Supreme Admin)",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Thời gian",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        embed.set_footer(text="Reply 'SHUTDOWN CONFIRM' trong 30 giây để xác nhận")
        
        await ctx.reply(embed=embed, mention_author=True)
        
        # Chờ xác nhận từ user trong 30 giây
        def check(message):
            return (message.author == ctx.author and 
                   message.channel == ctx.channel and 
                   message.content.upper() == "SHUTDOWN CONFIRM")
        
        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=30.0)
            
            # Gửi thông báo cuối cùng
            final_embed = discord.Embed(
                title="🔴 BOT ĐANG TẮT...",
                description="**Bot sẽ tắt trong 3 giây!**",
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            
            final_embed.add_field(
                name="👑 Được thực hiện bởi",
                value=f"{ctx.author.mention} (Supreme Admin)",
                inline=True
            )
            
            final_embed.add_field(
                name="💀 Trạng thái",
                value="Đang thực hiện lệnh shutdown...",
                inline=True
            )
            
            final_embed.set_footer(text="Goodbye! Bot đã được tắt bởi Supreme Admin")
            
            await ctx.reply(embed=final_embed, mention_author=True)
            
            # Log shutdown action
            logger.critical(f"BOT SHUTDOWN initiated by Supreme Admin {ctx.author} ({ctx.author.id})")
            
            # Thực hiện lệnh shutdown
            try:
                # Chạy lệnh taskkill để tắt tất cả process Python
                result = subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                                      capture_output=True, text=True, timeout=10)
                
                logger.info(f"Shutdown command executed: {result.returncode}")
                if result.stdout:
                    logger.info(f"Shutdown stdout: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Shutdown stderr: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error("Shutdown command timed out")
            except Exception as e:
                logger.error(f"Error executing shutdown command: {e}")
                
                # Gửi thông báo lỗi nếu shutdown thất bại
                error_embed = discord.Embed(
                    title="❌ Lỗi Shutdown",
                    description=f"**Không thể tắt bot: {str(e)}**",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                await ctx.reply(embed=error_embed, mention_author=True)
                
        except asyncio.TimeoutError:
            # Timeout - hủy shutdown
            timeout_embed = discord.Embed(
                title="⏰ Hết thời gian xác nhận",
                description="**Lệnh shutdown đã bị hủy do không xác nhận trong 30 giây**",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            timeout_embed.add_field(
                name="🔄 Để thử lại",
                value="Sử dụng lệnh `;shutdown` và reply `SHUTDOWN CONFIRM`",
                inline=False
            )
            
            timeout_embed.set_footer(text="Shutdown cancelled - Bot vẫn đang hoạt động")
            
            await ctx.reply(embed=timeout_embed, mention_author=True)
            logger.info(f"Shutdown cancelled - timeout by {ctx.author} ({ctx.author.id})")
