# -*- coding: utf-8 -*-
"""
Permission Commands - Quản lý quyền cho các lệnh
"""
import discord
from discord.ext import commands
import logging
import json
import os
from .base import BaseCommand

logger = logging.getLogger(__name__)

class PermissionCommands(BaseCommand):
    """Class chứa các commands quản lý quyền"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.permissions_file = "data/command_permissions.json"
        self.command_permissions = self.load_permissions()
    
    def load_permissions(self):
        """Load permissions từ file"""
        try:
            if os.path.exists(self.permissions_file):
                with open(self.permissions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Default permissions cho một số lệnh quan trọng
                default_perms = {
                    "setsupremeadmin": "supreme_admin",
                    "removesupremeadmin": "supreme_admin",
                    "addadmin": "supreme_admin",
                    "removeadmin": "supreme_admin",
                    "addpriority": "admin",
                    "removepriority": "admin",
                    "reload": "admin",
                    "debug": "admin",
                    "cleanupdms": "supreme_admin",
                    "vipban": "admin",
                    "vipkick": "admin",
                    "vipunban": "admin",
                    "warn": "admin",
                    "mute": "admin",
                    "unmute": "admin"
                }
                self.save_permissions(default_perms)
                return default_perms
        except Exception as e:
            logger.error(f"Lỗi khi load permissions: {e}")
            return {}
    
    def save_permissions(self, permissions=None):
        """Save permissions vào file"""
        try:
            perms_to_save = permissions or self.command_permissions
            with open(self.permissions_file, 'w', encoding='utf-8') as f:
                json.dump(perms_to_save, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã lưu {len(perms_to_save)} command permissions")
        except Exception as e:
            logger.error(f"Lỗi khi save permissions: {e}")
    
    def get_command_permission(self, command_name):
        """Lấy permission level của command"""
        return self.command_permissions.get(command_name, "user")  # Default: user
    
    def set_command_permission(self, command_name, permission_level):
        """Set permission level cho command"""
        valid_levels = ["supreme_admin", "admin", "user"]
        if permission_level not in valid_levels:
            return False, f"Permission level không hợp lệ. Chỉ chấp nhận: {', '.join(valid_levels)}"
        
        self.command_permissions[command_name] = permission_level
        self.save_permissions()
        return True, f"Đã set permission '{permission_level}' cho lệnh '{command_name}'"
    
    def check_command_permission(self, ctx, command_name):
        """Kiểm tra user có quyền sử dụng command không"""
        required_level = self.get_command_permission(command_name)
        user_id = ctx.author.id
        
        # Supreme Admin có quyền tất cả
        if hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and user_id == self.bot_instance.supreme_admin_id:
            return True, "supreme_admin"
        
        # Admin có quyền admin và user
        if hasattr(self.bot_instance, 'admin_ids') and user_id in self.bot_instance.admin_ids:
            if required_level in ["admin", "user"]:
                return True, "admin"
            else:
                return False, f"Lệnh này chỉ dành cho Supreme Admin"
        
        # User chỉ có quyền user
        if required_level == "user":
            return True, "user"
        else:
            return False, f"Lệnh này chỉ dành cho {required_level.replace('_', ' ').title()}"
    
    def register_commands(self):
        """Register permission commands"""
        
        @self.bot.command(name='quyen')
        async def set_permission(ctx, command_name: str = None, permission_level: str = None):
            """
            Thiết lập quyền cho lệnh
            Chỉ Supreme Admin mới có thể sử dụng
            
            Usage: 
            ;quyen <tên_lệnh> <supreme_admin|admin|user>
            ;quyen emoji user
            ;quyen reload admin
            """
            # Chỉ Supreme Admin mới được set permissions
            # Kiểm tra Supreme Admin sử dụng bot_instance thay vì bot
            if not (hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id):
                error_embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Supreme Admin mới có thể thiết lập quyền cho lệnh!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            if not command_name or not permission_level:
                # Hiển thị help và danh sách permissions hiện tại
                embed = discord.Embed(
                    title="🔐 Quản lý quyền lệnh",
                    description="Thiết lập quyền sử dụng cho từng lệnh",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Cách sử dụng",
                    value="; <tên_lệnh> <permission_level>`",
                    inline=False
                )
                embed.add_field(
                    name="Permission Levels",
                    value=(
                        "• `supreme_admin` - Chỉ Supreme Admin\n"
                        "• `admin` - Admin và Supreme Admin\n"
                        "• `user` - Tất cả user"
                    ),
                    inline=False
                )
                embed.add_field(
                    name="Ví dụ",
                    value=(
                        "; emoji user` - Cho phép tất cả user dùng emoji\n"
                        "; reload admin` - Chỉ admin được reload\n"
                        "; debug supreme_admin` - Chỉ Supreme Admin"
                    ),
                    inline=False
                )
                
                # Hiển thị một số permissions hiện tại
                current_perms = []
                for cmd, perm in list(self.command_permissions.items())[:10]:
                    current_perms.append(f"`{cmd}`: {perm}")
                
                if current_perms:
                    embed.add_field(
                        name="Permissions hiện tại (10 đầu)",
                        value="\n".join(current_perms),
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Thống kê",
                    value=f"Đang quản lý {len(self.command_permissions)} lệnh",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Kiểm tra command có tồn tại không
            all_commands = [cmd.name for cmd in self.bot.commands] + [alias for cmd in self.bot.commands for alias in cmd.aliases]
            if command_name not in all_commands:
                error_embed = discord.Embed(
                    title="❌ Lệnh không tồn tại",
                    description=f"Không tìm thấy lệnh `{command_name}`",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="💡 Gợi ý",
                    value="Sử dụng ;` để xem danh sách lệnh có sẵn",
                    inline=False
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            # Set permission
            success, message = self.set_command_permission(command_name, permission_level)
            
            if success:
                success_embed = discord.Embed(
                    title="✅ Đã cập nhật quyền",
                    description=message,
                    color=discord.Color.green()
                )
                success_embed.add_field(
                    name="📋 Chi tiết",
                    value=(
                        f"**Lệnh:** `{command_name}`\n"
                        f"**Permission:** `{permission_level}`\n"
                        f"**Có hiệu lực:** Ngay lập tức"
                    ),
                    inline=False
                )
                
                # Giải thích ai có thể dùng
                if permission_level == "supreme_admin":
                    who_can_use = "Chỉ Supreme Admin"
                elif permission_level == "admin":
                    who_can_use = "Admin và Supreme Admin"
                else:
                    who_can_use = "Tất cả user"
                
                success_embed.add_field(
                    name="👥 Ai có thể sử dụng",
                    value=who_can_use,
                    inline=False
                )
                
                await ctx.reply(embed=success_embed, mention_author=True)
            else:
                error_embed = discord.Embed(
                    title="❌ Lỗi",
                    description=message,
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed, mention_author=True)
        
        @self.bot.command(name='listquyen', aliases=['permissions'])
        async def list_permissions(ctx, page: int = 1):
            """
            Xem danh sách quyền của các lệnh
            
            Usage: ;listquyen [page]
            """
            # Chỉ admin trở lên mới xem được
            is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
            is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
            if not (is_admin or is_supreme):
                error_embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin trở lên mới có thể xem danh sách quyền!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            if not self.command_permissions:
                embed = discord.Embed(
                    title="📋 Danh sách quyền lệnh",
                    description="Chưa có lệnh nào được thiết lập quyền",
                    color=discord.Color.orange()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Phân trang
            items_per_page = 15
            total_items = len(self.command_permissions)
            total_pages = (total_items + items_per_page - 1) // items_per_page
            
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages
            
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            # Sắp xếp theo permission level và tên lệnh
            sorted_perms = sorted(self.command_permissions.items(), 
                                key=lambda x: (x[1], x[0]))
            page_items = sorted_perms[start_idx:end_idx]
            
            embed = discord.Embed(
                title="🔐 Danh sách quyền lệnh",
                description=f"Trang {page}/{total_pages} - Tổng {total_items} lệnh",
                color=discord.Color.blue()
            )
            
            # Group by permission level
            supreme_admin_cmds = []
            admin_cmds = []
            user_cmds = []
            
            for cmd, perm in page_items:
                if perm == "supreme_admin":
                    supreme_admin_cmds.append(cmd)
                elif perm == "admin":
                    admin_cmds.append(cmd)
                else:
                    user_cmds.append(cmd)
            
            if supreme_admin_cmds:
                embed.add_field(
                    name="👑 Supreme Admin Only",
                    value=", ".join([f"`{cmd}`" for cmd in supreme_admin_cmds]),
                    inline=False
                )
            
            if admin_cmds:
                embed.add_field(
                    name="🛡️ Admin+",
                    value=", ".join([f"`{cmd}`" for cmd in admin_cmds]),
                    inline=False
                )
            
            if user_cmds:
                embed.add_field(
                    name="👤 All Users",
                    value=", ".join([f"`{cmd}`" for cmd in user_cmds]),
                    inline=False
                )
            
            if total_pages > 1:
                embed.add_field(
                    name="📄 Navigation",
                    value=f"Sử dụng ; {page+1}` để xem trang tiếp theo" if page < total_pages else "Đây là trang cuối",
                    inline=False
                )
            
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='checkquyen')
        async def check_permission(ctx, command_name: str = None):
            """
            Kiểm tra quyền của một lệnh cụ thể
            
            Usage: ;checkquyen <tên_lệnh>
            """
            if not command_name:
                error_embed = discord.Embed(
                    title="❌ Thiếu tham số",
                    description="Vui lòng cung cấp tên lệnh cần kiểm tra!",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Cách sử dụng",
                    value="; <tên_lệnh>`\n**Ví dụ:** ; emoji`",
                    inline=False
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            permission_level = self.get_command_permission(command_name)
            has_permission, user_level = self.check_command_permission(ctx, command_name)
            
            embed = discord.Embed(
                title=f"🔍 Kiểm tra quyền: `{command_name}`",
                color=discord.Color.green() if has_permission else discord.Color.red()
            )
            
            embed.add_field(
                name="📋 Thông tin lệnh",
                value=(
                    f"**Lệnh:** `{command_name}`\n"
                    f"**Yêu cầu quyền:** `{permission_level}`\n"
                    f"**Quyền của bạn:** `{user_level}`"
                ),
                inline=False
            )
            
            embed.add_field(
                name="✅ Kết quả" if has_permission else "❌ Kết quả",
                value="Bạn có thể sử dụng lệnh này" if has_permission else "Bạn không có quyền sử dụng lệnh này",
                inline=False
            )
            
            # Giải thích permission levels
            if permission_level == "supreme_admin":
                who_can_use = "Chỉ Supreme Admin"
            elif permission_level == "admin":
                who_can_use = "Admin và Supreme Admin"
            else:
                who_can_use = "Tất cả user"
            
            embed.add_field(
                name="👥 Ai có thể sử dụng",
                value=who_can_use,
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
