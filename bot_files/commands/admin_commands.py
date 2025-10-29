"""
Admin management commands
"""
import discord
from discord.ext import commands
import logging
from .base import BaseCommand

logger = logging.getLogger(__name__)

class AdminCommands(BaseCommand):
    """Class chứa các commands quản lý admin"""
    
    def register_commands(self):
        """Register admin management commands"""
        
        @self.bot.command(name='addadmin')
        async def add_admin(ctx, user_id: int):
            """
            Thêm user ID vào danh sách admin
            
            Usage: !addadmin <user_id>
            """
            await self._add_admin_impl(ctx, user_id)
        
        @self.bot.command(name='removeadmin')
        async def remove_admin(ctx, user_id: int):
            """
            Xóa user ID khỏi danh sách admin
            
            Usage: !removeadmin <user_id>
            """
            await self._remove_admin_impl(ctx, user_id)
        
        @self.bot.command(name='listadmin')
        async def list_admin(ctx):
            """
            Hiển thị danh sách admin IDs
            
            Usage: !listadmin
            """
            await self._list_admin_impl(ctx)
        
        @self.bot.command(name='admin')
        async def admin_management(ctx, action: str = None, user_id: int = None):
            """
            Quản lý danh sách admin với subcommands
            
            Usage: 
            /admin add <user_id> - Thêm user thành admin
            /admin remove <user_id> - Xóa user khỏi admin
            /admin list - Xem danh sách admin
            """
            if action is None:
                await self._show_admin_help(ctx)
                return
            
            action = action.lower()
            
            if action == "add":
                if user_id is None:
                    await ctx.reply(f"{ctx.author.mention} ❌ Vui lòng cung cấp User ID!\nUsage: `/admin add <user_id>`", mention_author=True)
                    return
                await self._add_admin_impl(ctx, user_id)
                
            elif action == "remove":
                if user_id is None:
                    await ctx.reply(f"{ctx.author.mention} ❌ Vui lòng cung cấp User ID!\nUsage: `/admin remove <user_id>`", mention_author=True)
                    return
                await self._remove_admin_impl(ctx, user_id)
                
            elif action == "list":
                await self._list_admin_impl(ctx)
            
            elif action == "backup":
                await self._show_backup_help(ctx)
                
            else:
                await self._show_admin_help(ctx)
    
    async def _add_admin_impl(self, ctx, user_id: int):
        """
        Implementation thực tế của addadmin command
        """
        # Kiểm tra quyền: Supreme Admin hoặc server administrator
        if not (self.bot_instance.is_supreme_admin(ctx.author.id) or ctx.author.guild_permissions.administrator):
            await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin hoặc Administrator mới có thể sử dụng lệnh này!", mention_author=True)
            return
        
        if user_id in self.bot_instance.admin_ids:
            await ctx.reply(f"{ctx.author.mention} ❌ User ID `{user_id}` đã có trong danh sách admin!", mention_author=True)
            return
        
        self.bot_instance.admin_ids.add(user_id)  # Set operation O(1)
        self.bot_instance.mark_for_save()  # Batch save
        
        embed = discord.Embed(
            title="✅ Đã thêm Admin",
            description=f"User ID `{user_id}` đã được thêm vào danh sách admin.",
            color=discord.Color.green()
        )
        embed.add_field(name="Quyền được cấp", value="Sử dụng lệnh !warn và !warnings", inline=False)
        embed.add_field(name="Tổng admin", value=f"{len(self.bot_instance.admin_ids)} người", inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin ID {user_id} được thêm bởi {ctx.author} ({ctx.author.id})")
    
    async def _remove_admin_impl(self, ctx, user_id: int):
        """
        Implementation thực tế của removeadmin command
        """
        # Kiểm tra quyền: Supreme Admin hoặc server administrator
        if not (self.bot_instance.is_supreme_admin(ctx.author.id) or ctx.author.guild_permissions.administrator):
            await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin hoặc Administrator mới có thể sử dụng lệnh này!", mention_author=True)
            return
        
        if user_id not in self.bot_instance.admin_ids:
            await ctx.reply(f"{ctx.author.mention} ❌ User ID `{user_id}` không có trong danh sách admin!", mention_author=True)
            return
        
        self.bot_instance.admin_ids.discard(user_id)  # Set operation O(1)
        self.bot_instance.mark_for_save()  # Batch save
        
        embed = discord.Embed(
            title="✅ Đã xóa Admin",
            description=f"User ID `{user_id}` đã được xóa khỏi danh sách admin.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Tổng admin còn lại", value=f"{len(self.bot_instance.admin_ids)} người", inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin ID {user_id} được xóa bởi {ctx.author} ({ctx.author.id})")
    
    async def _list_admin_impl(self, ctx):
        """
        Implementation thực tế của listadmin command
        """
        # Kiểm tra quyền sử dụng dynamic permission system
        if hasattr(self.bot_instance, 'permission_manager'):
            has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'listadmin')
            if not has_permission:
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền xem danh sách admin!", mention_author=True)
                return
        else:
            # Fallback: Kiểm tra quyền admin nếu không có permission system
            if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền xem danh sách admin!", mention_author=True)
                return
        
        if not self.bot_instance.admin_ids:
            embed = discord.Embed(
                title="📋 Danh sách Admin",
                description="Chưa có admin nào được thêm vào danh sách.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="📋 Danh sách Admin",
                description=f"Có **{len(self.bot_instance.admin_ids)}** admin trong danh sách:",
                color=discord.Color.blue()
            )
            
            admin_list = "\n".join([f"• `{admin_id}`" for admin_id in self.bot_instance.admin_ids])
            embed.add_field(name="User IDs", value=admin_list, inline=False)
            embed.add_field(name="Quyền", value="Sử dụng lệnh !warn và !warnings", inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def _show_admin_help(self, ctx):
        """Hiển thị hướng dẫn sử dụng lệnh admin"""
        embed = discord.Embed(
            title="👑 Lệnh Admin Management",
            description="Quản lý danh sách admin của bot",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 Cách sử dụng",
            value=(
                "`/admin add <user_id>` - Thêm user thành admin\n"
                "`/admin remove <user_id>` - Xóa user khỏi admin\n"
                "`/admin list` - Xem danh sách admin\n"
                "`/admin backup` - Hướng dẫn hệ thống backup"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Quyền admin",
            value="• Sử dụng lệnh `/warn` và `/warnings`\n• Quản lý timeout users\n• Các quyền moderation khác",
            inline=False
        )
        
        embed.add_field(
            name="💡 Ví dụ",
            value="`/admin add 1264908798003253314`",
            inline=False
        )
        
        embed.add_field(
            name="🔒 Quyền hạn",
            value="Chỉ Supreme Admin hoặc Server Administrator mới có thể sử dụng",
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def _show_backup_help(self, ctx):
        """Hiển thị hướng dẫn hệ thống backup"""
        # Kiểm tra quyền admin
        if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
            await ctx.reply(f"{ctx.author.mention} ❌ Chỉ admin mới có thể xem hướng dẫn backup!", mention_author=True)
            return
        
        embed = discord.Embed(
            title="🔄 Hệ thống Backup & Sync GitHub",
            description="Hướng dẫn sao lưu và đồng bộ dữ liệu từ GitHub",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 Các lệnh backup:",
            value=(
                "; init` - Khởi tạo Git repository\n"
                "; fix` - Khắc phục Git conflict ⭐\n"
                "; status` - Kiểm tra trạng thái Git\n"
                "; config` - Xem cấu hình GitHub\n"
                "; sync` - Đồng bộ an toàn từ GitHub\n"
                "; pull` - Tải code mới từ GitHub\n"
                "; restore` - Khôi phục hoàn toàn từ GitHub"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Quy trình thiết lập lần đầu:",
            value=(
                "**1.** Cập nhật `config_github.json`\n"
                "**2.** ; init` - Khởi tạo Git repository\n"
                "**3.** ; fix` - Khắc phục conflict (nếu có)\n"
                "**4.** ; status` - Kiểm tra trạng thái"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔄 Sử dụng thường xuyên:",
            value=(
                "• ; status` - Kiểm tra trước khi thực hiện\n"
                "• ; sync` - Đồng bộ an toàn (khuyến nghị)\n"
                "• ; pull` - Chỉ tải code mới\n"
                "• ; restore` - Khôi phục hoàn toàn (cẩn thận!)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Lưu ý quan trọng:",
            value=(
                "• **`init`** - Chỉ chạy lần đầu thiết lập\n"
                "• **`fix`** - Khắc phục conflict với README.md, .gitignore\n"
                "• **`sync`** - Tự động backup trước khi pull (an toàn)\n"
                "• **`restore`** - Ghi đè TẤT CẢ thay đổi local\n"
                "• Luôn kiểm tra `status` trước khi thực hiện"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🚨 Trường hợp khẩn cấp:",
            value=(
                "**Lỗi conflict:** ; fix`\n"
                "**Mất dữ liệu:** ; restore`\n"
                "**Không pull được:** ; status` → ; fix`\n"
                "**Repository lỗi:** ; init` (thiết lập lại)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📁 Files được backup tự động:",
            value=(
                "• `shared_wallet.json` - Ví tiền chung\n"
                "• `taixiu_data.json` - Dữ liệu tài xỉu\n"
                "• `admin.json` - Danh sách admin\n"
                "• `warnings.json` - Cảnh báo\n"
                "• Và các file game khác..."
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: Sử dụng ; sync` thường xuyên để đảm bảo dữ liệu an toàn!")
        
        await ctx.reply(embed=embed, mention_author=True)
