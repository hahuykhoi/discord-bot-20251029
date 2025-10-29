# -*- coding: utf-8 -*-
"""
Ban Commands - Hệ thống cấm user sử dụng bot
Chỉ Supreme Admin mới có quyền ban/unban user
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BanCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.data_folder = 'data'
        self.banned_users_file = os.path.join(self.data_folder, 'banned_users.json')
        
        # Tạo data folder nếu chưa có
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.banned_users = {}  # {user_id: {'reason': str, 'timestamp': str, 'banned_by': int}}
        self.load_banned_users()
        self.setup_commands()
    
    def load_banned_users(self):
        """Tải danh sách user bị ban từ file JSON"""
        try:
            if os.path.exists(self.banned_users_file):
                with open(self.banned_users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    self.banned_users = {int(k): v for k, v in data.get('banned_users', {}).items()}
                logger.info(f"Đã tải {len(self.banned_users)} user bị ban")
            else:
                # Tạo file banned users mặc định
                default_data = {
                    "banned_users": {},
                    "description": "Danh sách users bị cấm sử dụng bot",
                    "ban_history": []
                }
                with open(self.banned_users_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Đã tạo file banned users mới: {self.banned_users_file}")
        except Exception as e:
            logger.error(f"Lỗi khi tải banned users: {e}")
    
    def save_banned_users(self):
        """Lưu danh sách user bị ban vào file JSON"""
        try:
            # Load existing data để giữ lại ban_history
            existing_data = {}
            if os.path.exists(self.banned_users_file):
                with open(self.banned_users_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Convert int keys to string for JSON
            banned_data = {str(k): v for k, v in self.banned_users.items()}
            
            # Update banned_users
            existing_data['banned_users'] = banned_data
            existing_data['description'] = "Danh sách users bị cấm sử dụng bot"
            
            with open(self.banned_users_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu banned users thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu banned users: {e}")
    
    def add_ban_history(self, user_id: int, action: str, admin_id: int, reason: str = ""):
        """Thêm lịch sử ban/unban vào file"""
        try:
            # Load existing data
            existing_data = {}
            if os.path.exists(self.banned_users_file):
                with open(self.banned_users_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Ensure ban_history exists
            if 'ban_history' not in existing_data:
                existing_data['ban_history'] = []
            
            # Add new history entry
            history_entry = {
                'user_id': user_id,
                'action': action,  # 'ban' hoặc 'unban'
                'admin_id': admin_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            existing_data['ban_history'].append(history_entry)
            
            # Keep only last 100 entries để tránh file quá lớn
            if len(existing_data['ban_history']) > 100:
                existing_data['ban_history'] = existing_data['ban_history'][-100:]
            
            # Save back to file
            with open(self.banned_users_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Lỗi khi thêm ban history: {e}")
    
    def is_user_banned(self, user_id: int) -> bool:
        """Kiểm tra xem user có bị ban không"""
        return user_id in self.banned_users
    
    def get_ban_info(self, user_id: int) -> dict:
        """Lấy thông tin ban của user"""
        return self.banned_users.get(user_id, {})
    
    def ban_user(self, user_id: int, reason: str, admin_id: int):
        """Ban user"""
        self.banned_users[user_id] = {
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'banned_by': admin_id
        }
        self.save_banned_users()
        self.add_ban_history(user_id, 'ban', admin_id, reason)
    
    def unban_user(self, user_id: int, admin_id: int, reason: str = ""):
        """Unban user"""
        if user_id in self.banned_users:
            del self.banned_users[user_id]
            self.save_banned_users()
            self.add_ban_history(user_id, 'unban', admin_id, reason)
            return True
        return False
    
    def setup_commands(self):
        """Thiết lập các lệnh ban"""
        
        @self.bot.command(name='ban')
        async def ban_command(ctx, user_id: str = None, *, reason: str = "Không có lý do"):
            """
            Cấm user sử dụng bot
            Chỉ Supreme Admin mới có quyền sử dụng
            
            Usage: ;ban <user_id> [lý do]
            """
            # Kiểm tra quyền Supreme Admin
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Supreme Admin mới có thể ban user!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not user_id:
                embed = discord.Embed(
                    title="❌ Thiếu tham số",
                    description="Vui lòng nhập user ID cần ban!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value="`/ban <user_id> [lý do]`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Parse user ID
            try:
                target_user_id = int(user_id)
            except ValueError:
                embed = discord.Embed(
                    title="❌ User ID không hợp lệ",
                    description="Vui lòng nhập user ID hợp lệ (chỉ số)!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Không thể ban chính mình
            if target_user_id == ctx.author.id:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Bạn không thể ban chính mình!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Không thể ban Supreme Admin
            if self.bot_instance.is_supreme_admin(target_user_id):
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Không thể ban Supreme Admin!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Kiểm tra user đã bị ban chưa
            if self.is_user_banned(target_user_id):
                embed = discord.Embed(
                    title="⚠️ Thông báo",
                    description=f"User `{target_user_id}` đã bị ban rồi!",
                    color=discord.Color.orange()
                )
                
                ban_info = self.get_ban_info(target_user_id)
                if ban_info:
                    embed.add_field(
                        name="📝 Lý do hiện tại",
                        value=ban_info.get('reason', 'Không có lý do'),
                        inline=False
                    )
                
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Ban user
            self.ban_user(target_user_id, reason, ctx.author.id)
            
            # Lấy thông tin user nếu có thể
            try:
                target_user = await self.bot.fetch_user(target_user_id)
                user_info = f"{target_user.display_name} ({target_user.name})"
            except:
                user_info = f"User ID: {target_user_id}"
            
            embed = discord.Embed(
                title="🔨 User đã bị ban",
                description=f"**{user_info}** đã bị cấm sử dụng bot!",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{user_info} (`{target_user_id}`)",
                inline=True
            )
            
            embed.add_field(
                name="📝 Lý do",
                value=reason,
                inline=True
            )
            
            embed.add_field(
                name="👑 Ban bởi",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.add_field(
                name="⚠️ Lưu ý",
                value="User sẽ không thể sử dụng bất kỳ lệnh nào của bot",
                inline=False
            )
            
            embed.set_footer(text="Sử dụng ;unban để bỏ ban")
            await ctx.reply(embed=embed, mention_author=True)
            
            logger.info(f"User {target_user_id} đã bị ban bởi {ctx.author} với lý do: {reason}")
        
        @self.bot.command(name='unban')
        async def unban_command(ctx, user_id: str = None, *, reason: str = "Được tha thứ"):
            """
            Bỏ ban user
            Chỉ Supreme Admin mới có quyền sử dụng
            
            Usage: ;unban <user_id> [lý do]
            """
            # Kiểm tra quyền Supreme Admin
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Supreme Admin mới có thể unban user!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not user_id:
                embed = discord.Embed(
                    title="❌ Thiếu tham số",
                    description="Vui lòng nhập user ID cần unban!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value="`/unban <user_id> [lý do]`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Parse user ID
            try:
                target_user_id = int(user_id)
            except ValueError:
                embed = discord.Embed(
                    title="❌ User ID không hợp lệ",
                    description="Vui lòng nhập user ID hợp lệ (chỉ số)!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Kiểm tra user có bị ban không
            if not self.is_user_banned(target_user_id):
                embed = discord.Embed(
                    title="⚠️ Thông báo",
                    description=f"User `{target_user_id}` không bị ban!",
                    color=discord.Color.orange()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Unban user
            success = self.unban_user(target_user_id, ctx.author.id, reason)
            
            if success:
                # Lấy thông tin user nếu có thể
                try:
                    target_user = await self.bot.fetch_user(target_user_id)
                    user_info = f"{target_user.display_name} ({target_user.name})"
                except:
                    user_info = f"User ID: {target_user_id}"
                
                embed = discord.Embed(
                    title="✅ User đã được unban",
                    description=f"**{user_info}** đã được bỏ ban!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 User",
                    value=f"{user_info} (`{target_user_id}`)",
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Lý do unban",
                    value=reason,
                    inline=True
                )
                
                embed.add_field(
                    name="👑 Unban bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="🎉 Thông báo",
                    value="User có thể sử dụng bot trở lại!",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"User {target_user_id} đã được unban bởi {ctx.author} với lý do: {reason}")
            else:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Có lỗi xảy ra khi unban user!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='banlist')
        async def banlist_command(ctx):
            """
            Xem danh sách user bị ban
            Admin và Supreme Admin có thể sử dụng
            
            Usage: ;banlist
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ admin mới có thể xem danh sách ban!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not self.banned_users:
                embed = discord.Embed(
                    title="📋 Danh sách Ban",
                    description="Hiện tại không có user nào bị ban!",
                    color=discord.Color.green()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            embed = discord.Embed(
                title="🔨 Danh sách User bị Ban",
                description=f"Có **{len(self.banned_users)}** user đang bị ban:",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            # Hiển thị tối đa 10 user để tránh embed quá dài
            user_list = list(self.banned_users.items())[:10]
            user_info_list = []
            
            for user_id, ban_info in user_list:
                try:
                    user = await self.bot.fetch_user(user_id)
                    user_info = f"**{user.display_name}** (`{user_id}`)"
                except:
                    user_info = f"**Unknown User** (`{user_id}`)"
                
                reason = ban_info.get('reason', 'Không có lý do')
                if len(reason) > 50:
                    reason = reason[:50] + "..."
                
                user_info_list.append(f"{user_info}\n*Lý do: {reason}*")
            
            embed.add_field(
                name="👥 Users bị Ban",
                value="\n\n".join(user_info_list) if user_info_list else "Không có user nào",
                inline=False
            )
            
            if len(self.banned_users) > 10:
                embed.add_field(
                    name="⚠️ Lưu ý",
                    value=f"Chỉ hiển thị 10/{len(self.banned_users)} user đầu tiên",
                    inline=False
                )
            
            embed.set_footer(text="Sử dụng ;checkban <user_id> để xem chi tiết")
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='banhistory')
        async def banhistory_command(ctx, limit: int = 10):
            """
            Xem lịch sử ban/unban
            Chỉ Supreme Admin mới có quyền sử dụng
            
            Usage: ;banhistory [số lượng]
            """
            # Kiểm tra quyền Supreme Admin
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Supreme Admin mới có thể xem lịch sử ban!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Giới hạn limit
            limit = max(1, min(limit, 20))  # Từ 1 đến 20
            
            try:
                # Load history từ file
                history_data = []
                if os.path.exists(self.banned_users_file):
                    with open(self.banned_users_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history_data = data.get('ban_history', [])
                
                if not history_data:
                    embed = discord.Embed(
                        title="📋 Lịch sử Ban",
                        description="Chưa có lịch sử ban/unban nào!",
                        color=discord.Color.blue()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Hiển thị entries gần nhất
                recent_history = history_data[-limit:]
                
                embed = discord.Embed(
                    title="📋 Lịch sử Ban/Unban",
                    description=f"**{len(recent_history)}** hoạt động gần nhất:",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                for entry in reversed(recent_history):  # Hiển thị từ mới nhất
                    action_emoji = "🔨" if entry['action'] == 'ban' else "✅"
                    action_text = "BAN" if entry['action'] == 'ban' else "UNBAN"
                    
                    # Lấy thông tin user
                    try:
                        user = await self.bot.fetch_user(entry['user_id'])
                        user_info = f"{user.display_name}"
                    except:
                        user_info = f"Unknown User"
                    
                    # Lấy thông tin admin
                    try:
                        admin = await self.bot.fetch_user(entry['admin_id'])
                        admin_info = f"{admin.display_name}"
                    except:
                        admin_info = f"Unknown Admin"
                    
                    # Format timestamp
                    try:
                        timestamp = datetime.fromisoformat(entry['timestamp'])
                        time_str = timestamp.strftime("%d/%m/%Y %H:%M")
                    except:
                        time_str = "Unknown time"
                    
                    field_value = f"**User:** {user_info} (`{entry['user_id']}`)\n"
                    field_value += f"**By:** {admin_info}\n"
                    if entry.get('reason'):
                        field_value += f"**Reason:** {entry['reason']}\n"
                    field_value += f"**Time:** {time_str}"
                    
                    embed.add_field(
                        name=f"{action_emoji} {action_text}",
                        value=field_value,
                        inline=False
                    )
                
                if len(history_data) > limit:
                    embed.set_footer(text=f"Hiển thị {limit}/{len(history_data)} hoạt động")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description=f"Có lỗi xảy ra khi tải lịch sử: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                logger.error(f"Lỗi trong banhistory: {e}")
        
        @self.bot.command(name='checkban')
        async def checkban_command(ctx, user_id: str = None):
            """
            Kiểm tra trạng thái ban của user
            Admin và Supreme Admin có thể sử dụng
            
            Usage: ;checkban <user_id>
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ admin mới có thể kiểm tra ban status!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not user_id:
                embed = discord.Embed(
                    title="❌ Thiếu tham số",
                    description="Vui lòng nhập user ID cần kiểm tra!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value="`/checkban <user_id>`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Parse user ID
            try:
                target_user_id = int(user_id)
            except ValueError:
                embed = discord.Embed(
                    title="❌ User ID không hợp lệ",
                    description="Vui lòng nhập user ID hợp lệ (chỉ số)!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Lấy thông tin user
            try:
                target_user = await self.bot.fetch_user(target_user_id)
                user_info = f"{target_user.display_name} ({target_user.name})"
            except:
                user_info = f"User ID: {target_user_id}"
            
            # Kiểm tra ban status
            is_banned = self.is_user_banned(target_user_id)
            
            if is_banned:
                ban_info = self.get_ban_info(target_user_id)
                
                embed = discord.Embed(
                    title="🔨 User bị Ban",
                    description=f"**{user_info}** đang bị cấm sử dụng bot!",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 User",
                    value=f"{user_info} (`{target_user_id}`)",
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Lý do",
                    value=ban_info.get('reason', 'Không có lý do'),
                    inline=True
                )
                
                # Thông tin admin ban
                try:
                    banned_by = ban_info.get('banned_by')
                    if banned_by:
                        admin = await self.bot.fetch_user(banned_by)
                        admin_info = f"{admin.display_name}"
                    else:
                        admin_info = "Unknown"
                except:
                    admin_info = "Unknown"
                
                embed.add_field(
                    name="👑 Ban bởi",
                    value=admin_info,
                    inline=True
                )
                
                # Thời gian ban
                ban_time = ban_info.get('timestamp')
                if ban_time:
                    try:
                        timestamp = datetime.fromisoformat(ban_time)
                        embed.add_field(
                            name="⏰ Thời gian ban",
                            value=f"<t:{int(timestamp.timestamp())}:F>",
                            inline=False
                        )
                    except:
                        pass
                
            else:
                embed = discord.Embed(
                    title="✅ User không bị Ban",
                    description=f"**{user_info}** có thể sử dụng bot bình thường!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 User",
                    value=f"{user_info} (`{target_user_id}`)",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Trạng thái",
                    value="✅ Không bị ban",
                    inline=True
                )
            
            await ctx.reply(embed=embed, mention_author=True)
    
    def register_commands(self):
        """Đăng ký commands - được gọi từ bot chính"""
        logger.info("Ban commands đã được đăng ký")
