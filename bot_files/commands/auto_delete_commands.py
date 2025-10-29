# -*- coding: utf-8 -*-
"""
Auto Delete Commands - Hệ thống tự động xóa tin nhắn của user
Chỉ admin mới có quyền sử dụng tính năng này
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AutoDeleteCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.data_folder = 'data'
        self.auto_delete_file = os.path.join(self.data_folder, 'auto_delete_config.json')
        
        # Tạo data folder nếu chưa có
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.auto_delete_users = {}  # {guild_id: {user_id: {'enabled': True, 'added_by': admin_id, 'timestamp': datetime}}}
        self.auto_fire_emoji = True  # Tự động thêm emoji 🔥
        self.load_auto_delete_config()
    
    def load_auto_delete_config(self):
        """Tải cấu hình auto delete từ file JSON"""
        try:
            if os.path.exists(self.auto_delete_file):
                with open(self.auto_delete_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    for guild_id_str, users in data.get('auto_delete_users', {}).items():
                        guild_id = int(guild_id_str)
                        self.auto_delete_users[guild_id] = {}
                        for user_id_str, user_data in users.items():
                            user_id = int(user_id_str)
                            self.auto_delete_users[guild_id][user_id] = user_data
                
                total_users = sum(len(users) for users in self.auto_delete_users.values())
                logger.info(f"Đã tải {total_users} user trong auto delete từ {len(self.auto_delete_users)} guild")
            else:
                # Tạo file config mặc định
                default_data = {
                    "auto_delete_users": {},
                    "description": "Danh sách users bị tự động xóa tin nhắn theo guild",
                    "delete_history": []
                }
                with open(self.auto_delete_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Đã tạo file auto delete config mới: {self.auto_delete_file}")
        except Exception as e:
            logger.error(f"Lỗi khi tải auto delete config: {e}")
    
    def save_auto_delete_config(self):
        """Lưu cấu hình auto delete vào file JSON"""
        try:
            # Load existing data để giữ lại delete_history
            existing_data = {}
            if os.path.exists(self.auto_delete_file):
                with open(self.auto_delete_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Convert int keys to string for JSON
            auto_delete_data = {}
            for guild_id, users in self.auto_delete_users.items():
                auto_delete_data[str(guild_id)] = {}
                for user_id, user_data in users.items():
                    auto_delete_data[str(guild_id)][str(user_id)] = user_data
            
            # Update auto_delete_users
            existing_data['auto_delete_users'] = auto_delete_data
            existing_data['description'] = "Danh sách users bị tự động xóa tin nhắn theo guild"
            
            with open(self.auto_delete_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu auto delete config thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu auto delete config: {e}")
    
    def add_delete_history(self, guild_id: int, user_id: int, action: str, admin_id: int, reason: str = ""):
        """Thêm lịch sử auto delete vào file"""
        try:
            # Load existing data
            existing_data = {}
            if os.path.exists(self.auto_delete_file):
                with open(self.auto_delete_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Ensure delete_history exists
            if 'delete_history' not in existing_data:
                existing_data['delete_history'] = []
            
            # Add new history entry
            history_entry = {
                'guild_id': guild_id,
                'user_id': user_id,
                'action': action,  # 'add' hoặc 'remove'
                'admin_id': admin_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            existing_data['delete_history'].append(history_entry)
            
            # Keep only last 100 entries để tránh file quá lớn
            if len(existing_data['delete_history']) > 100:
                existing_data['delete_history'] = existing_data['delete_history'][-100:]
            
            # Save back to file
            with open(self.auto_delete_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Lỗi khi thêm auto delete history: {e}")
    
    def is_user_auto_deleted(self, guild_id: int, user_id: int) -> bool:
        """Kiểm tra xem user có bị auto delete không"""
        if guild_id not in self.auto_delete_users:
            return False
        if user_id not in self.auto_delete_users[guild_id]:
            return False
        return self.auto_delete_users[guild_id][user_id].get('enabled', False)
    
    def add_auto_delete_user(self, guild_id: int, user_id: int, admin_id: int):
        """Thêm user vào danh sách auto delete"""
        if guild_id not in self.auto_delete_users:
            self.auto_delete_users[guild_id] = {}
        
        self.auto_delete_users[guild_id][user_id] = {
            'enabled': True,
            'added_by': admin_id,
            'timestamp': datetime.now().isoformat()
        }
        self.save_auto_delete_config()
        self.add_delete_history(guild_id, user_id, 'add', admin_id)
    
    def remove_auto_delete_user(self, guild_id: int, user_id: int, admin_id: int):
        """Xóa user khỏi danh sách auto delete"""
        if guild_id in self.auto_delete_users and user_id in self.auto_delete_users[guild_id]:
            del self.auto_delete_users[guild_id][user_id]
            
            # Xóa guild nếu không còn user nào
            if not self.auto_delete_users[guild_id]:
                del self.auto_delete_users[guild_id]
            
            self.save_auto_delete_config()
            self.add_delete_history(guild_id, user_id, 'remove', admin_id)
            return True
        return False
    
    async def handle_auto_delete_message(self, message):
        """Xử lý auto delete message - được gọi từ main bot event"""
        try:
            # Bỏ qua nếu không phải trong guild
            if not message.guild:
                return
            
            # Bỏ qua tin nhắn từ bot
            if message.author.bot:
                return
            
            # Bỏ qua tin nhắn từ admin (để admin có thể dùng lệnh)
            if self.bot_instance.has_warn_permission(message.author.id, message.author.guild_permissions):
                return
            
            guild_id = message.guild.id
            user_id = message.author.id
            
            # Kiểm tra user có bị auto delete không
            if self.is_user_auto_deleted(guild_id, user_id):
                try:
                    # Thêm emoji 🔥 trước khi xóa (nếu tính năng được bật)
                    if self.auto_fire_emoji:
                        try:
                            await message.add_reaction("🔥")
                            logger.info(f"Auto Delete: Đã thêm emoji 🔥 vào tin nhắn của user {user_id}")
                            # Đợi một chút để admin có thể thấy emoji
                            import asyncio
                            await asyncio.sleep(0.3)
                        except:
                            pass  # Không quan trọng nếu không thêm được emoji
                    
                    # Xóa tin nhắn
                    await message.delete()
                    logger.info(f"Auto Delete: Đã xóa tin nhắn của user {user_id} trong guild {guild_id}")
                except discord.Forbidden:
                    logger.warning(f"Auto Delete: Không có quyền xóa tin nhắn của user {user_id} trong guild {guild_id}")
                    # Gửi thông báo cho admin về việc thiếu quyền
                    try:
                        # Tìm admin để thông báo
                        for member in message.guild.members:
                            if self.bot_instance.has_warn_permission(member.id, member.guild_permissions):
                                embed = discord.Embed(
                                    title="⚠️ Bot thiếu quyền Auto Delete",
                                    description="Bot không thể xóa tin nhắn do thiếu quyền!",
                                    color=discord.Color.orange()
                                )
                                embed.add_field(
                                    name="🔧 Cách khắc phục nhanh:",
                                    value=(
                                        "1. **Server Settings** > **Roles**\n"
                                        "2. Tìm role của bot\n"
                                        "3. Bật quyền **Manage Messages** (chỉ cần quyền này!)\n"
                                        "4. Auto Delete sẽ hoạt động ngay"
                                    ),
                                    inline=False
                                )
                                embed.add_field(
                                    name="👤 User bị Auto Delete:",
                                    value=f"<@{user_id}> (ID: {user_id})",
                                    inline=False
                                )
                                try:
                                    await member.send(embed=embed)
                                    break
                                except:
                                    continue
                    except:
                        pass
                except discord.NotFound:
                    logger.warning(f"Auto Delete: Tin nhắn của user {user_id} đã bị xóa trước đó")
                except Exception as e:
                    logger.error(f"Auto Delete: Lỗi khi xóa tin nhắn của user {user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Lỗi trong handle_auto_delete_message: {e}")
    
    def register_commands(self):
        """Thiết lập các lệnh auto delete"""
        
        @self.bot.command(name='checkperms')
        async def check_permissions_command(ctx):
            """Kiểm tra quyền của bot cho các tính năng moderation"""
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ admin mới có thể kiểm tra permissions!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            bot_member = ctx.guild.get_member(self.bot.user.id)
            if not bot_member:
                await ctx.reply("❌ Không thể tìm thấy bot trong server!", mention_author=True)
                return
            
            permissions = bot_member.guild_permissions
            
            embed = discord.Embed(
                title="🔍 Kiểm tra Permissions Bot",
                description="Trạng thái quyền cho các tính năng moderation",
                color=discord.Color.blue()
            )
            
            # Kiểm tra các quyền cần thiết
            perms_check = {
                "Manage Messages": permissions.manage_messages,
                "Read Message History": permissions.read_message_history,
                "Send Messages": permissions.send_messages,
                "Embed Links": permissions.embed_links,
                "Add Reactions": permissions.add_reactions,
                "Use External Emojis": permissions.use_external_emojis,
                "Manage Roles": permissions.manage_roles,
                "Kick Members": permissions.kick_members,
                "Ban Members": permissions.ban_members
            }
            
            # Phân loại permissions
            essential_perms = ["Manage Messages", "Read Message History", "Send Messages", "Embed Links"]
            moderation_perms = ["Manage Roles", "Kick Members", "Ban Members"]
            optional_perms = ["Add Reactions", "Use External Emojis"]
            
            # Essential permissions
            essential_status = []
            for perm in essential_perms:
                status = "✅" if perms_check[perm] else "❌"
                essential_status.append(f"{status} {perm}")
            
            embed.add_field(
                name="🔥 Quyền thiết yếu (Auto Delete, Fire Delete)",
                value="\n".join(essential_status),
                inline=False
            )
            
            # Moderation permissions
            mod_status = []
            for perm in moderation_perms:
                status = "✅" if perms_check[perm] else "❌"
                mod_status.append(f"{status} {perm}")
            
            embed.add_field(
                name="🛡️ Quyền moderation (Mute, Kick, Ban)",
                value="\n".join(mod_status),
                inline=False
            )
            
            # Optional permissions
            opt_status = []
            for perm in optional_perms:
                status = "✅" if perms_check[perm] else "❌"
                opt_status.append(f"{status} {perm}")
            
            embed.add_field(
                name="⭐ Quyền tùy chọn",
                value="\n".join(opt_status),
                inline=False
            )
            
            # Tổng kết - chỉ tập trung vào Manage Messages
            manage_messages = perms_check["Manage Messages"]
            if not manage_messages:
                embed.add_field(
                    name="❌ QUAN TRỌNG - Thiếu quyền xóa tin nhắn",
                    value="**Manage Messages** - Auto Delete và Fire Delete không hoạt động!\n"
                          "🔧 **Khắc phục**: Server Settings > Roles > Bot Role > Bật 'Manage Messages'",
                    inline=False
                )
                embed.color = discord.Color.red()
            else:
                embed.add_field(
                    name="✅ Quyền xóa tin nhắn OK",
                    value="**Manage Messages** đã được cấp - Auto Delete và Fire Delete hoạt động bình thường!",
                    inline=False
                )
                embed.color = discord.Color.green()
                
            # Kiểm tra các quyền khác (không quan trọng bằng)
            other_missing = [p for p in essential_perms[1:] if not perms_check[p]]  # Bỏ qua Manage Messages
            if other_missing:
                embed.add_field(
                    name="⚠️ Quyền khác (không quan trọng bằng)",
                    value=f"Thiếu: **{', '.join(other_missing)}**\n"
                          "Bot vẫn hoạt động được nhưng một số tính năng có thể bị hạn chế",
                    inline=False
                )
            
            embed.add_field(
                name="🔧 Cách cấp quyền nhanh nhất",
                value=(
                    "1. **Server Settings** > **Roles**\n"
                    "2. Tìm role của bot\n"
                    "3. Bật quyền **'Manage Messages'** (chỉ cần quyền này!)\n"
                    "4. Auto Delete và Fire Delete sẽ hoạt động ngay"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Bot: {bot_member.display_name} • Role cao nhất: {bot_member.top_role.name}")
            
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='xoa')
        async def auto_delete_command(ctx, action: str = None, target: str = None, *, reason: str = "Không có lý do"):
            """
            Quản lý tính năng Auto Delete
            Chỉ admin mới có quyền sử dụng
            
            Usage: 
            - ;xoa on @user [lý do] - Bật auto delete cho user
            - ;xoa on <user_id> [lý do] - Bật auto delete cho user ID
            - ;xoa off @user [lý do] - Tắt auto delete cho user
            - ;xoa off <user_id> [lý do] - Tắt auto delete cho user ID
            - ;xoa list - Xem danh sách user bị auto delete
            - ;xoa history [số lượng] - Xem lịch sử auto delete
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ admin mới có thể sử dụng lệnh auto delete!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not action:
                # Hiển thị hướng dẫn
                embed = discord.Embed(
                    title="🗑️ Auto Delete System",
                    description="Hệ thống tự động xóa tin nhắn của user",
                    color=discord.Color.orange()
                )
                
                embed.add_field(
                    name="📝 Cách sử dụng",
                    value="`/xoa on @user [lý do]` - Bật auto delete\n"
                          "`/xoa off @user [lý do]` - Tắt auto delete\n"
                          "`/xoa remove <user_id>` - Xóa user khỏi danh sách\n"
                          "`/xoa list` - Xem danh sách\n"
                          "`/xoa history [số]` - Xem lịch sử\n"
                          "`/xoa fireemoji on/off` - Bật/tắt emoji 🔥 toàn cục\n"
                          "`/xoa fireemoji <user_id>` - Bật auto delete + emoji 🔥 cho user",
                    inline=False
                )
                
                embed.add_field(
                    name="🔄 Cách hoạt động",
                    value="• Tất cả tin nhắn của user sẽ bị xóa tự động\n"
                          "• Chỉ admin mới có quyền quản lý\n"
                          "• Tin nhắn của admin không bị xóa\n"
                          "• Lưu lịch sử tất cả hoạt động",
                    inline=False
                )
                
                # Đếm số user đang bị auto delete trong server này
                guild_users = self.auto_delete_users.get(ctx.guild.id, {})
                active_count = len([u for u in guild_users.values() if u.get('enabled', False)])
                
                embed.add_field(
                    name="📊 Trạng thái hiện tại",
                    value=f"**{active_count}** user đang bị auto delete",
                    inline=True
                )
                
                embed.set_footer(text="Chỉ admin mới có thể sử dụng lệnh này")
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if action.lower() == 'on':
                # Bật auto delete cho user
                if not target:
                    embed = discord.Embed(
                        title="❌ Thiếu tham số",
                        description="Vui lòng chỉ định user cần bật auto delete!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="💡 Cách sử dụng",
                        value="`/xoa on @user [lý do]`\n`/xoa on <user_id> [lý do]`",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Xử lý target (mention hoặc user ID)
                target_user = None
                target_user_id = None
                
                # Kiểm tra mention
                if ctx.message.mentions:
                    target_user = ctx.message.mentions[0]
                    target_user_id = target_user.id
                else:
                    # Thử parse user ID
                    try:
                        target_user_id = int(target)
                        try:
                            target_user = await self.bot.fetch_user(target_user_id)
                        except:
                            target_user = None
                    except ValueError:
                        embed = discord.Embed(
                            title="❌ User không hợp lệ",
                            description="Vui lòng mention user hoặc nhập user ID hợp lệ!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                
                # Không thể auto delete chính mình
                if target_user_id == ctx.author.id:
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description="Bạn không thể bật auto delete cho chính mình!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Không thể auto delete admin khác
                if target_user:
                    member = ctx.guild.get_member(target_user_id)
                    if member and self.bot_instance.has_warn_permission(target_user_id, member.guild_permissions):
                        embed = discord.Embed(
                            title="❌ Lỗi",
                            description="Không thể bật auto delete cho admin khác!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                
                # Kiểm tra user đã bị auto delete chưa
                if self.is_user_auto_deleted(ctx.guild.id, target_user_id):
                    embed = discord.Embed(
                        title="⚠️ Thông báo",
                        description=f"User này đã bị auto delete rồi!",
                        color=discord.Color.orange()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Thêm user vào auto delete
                self.add_auto_delete_user(ctx.guild.id, target_user_id, ctx.author.id)
                
                # Lấy thông tin user
                user_info = target_user.display_name if target_user else f"User ID: {target_user_id}"
                
                embed = discord.Embed(
                    title="🗑️ Auto Delete đã BẬT",
                    description=f"**{user_info}** sẽ bị xóa tin nhắn tự động!",
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
                    name="👑 Bật bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="⚠️ Lưu ý",
                    value="• Tất cả tin nhắn của user sẽ bị xóa tự động\n"
                          "• Sử dụng `/xoa off @user` để tắt",
                    inline=False
                )
                embed.set_footer(text="Auto Delete đã được kích hoạt")
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"Auto Delete ON: User {target_user_id} bởi {ctx.author} trong guild {ctx.guild.id}")
                
                # Xử lý target (mention hoặc user ID)
                target_user = None
                target_user_id = None
                
                # Kiểm tra mention
                if ctx.message.mentions:
                    target_user = ctx.message.mentions[0]
                    target_user_id = target_user.id
                else:
                    # Thử parse user ID
                    try:
                        target_user_id = int(target)
                        try:
                            target_user = await self.bot.fetch_user(target_user_id)
                        except:
                            target_user = None
                    except ValueError:
                        embed = discord.Embed(
                            title="❌ User không hợp lệ",
                            description="Vui lòng mention user hoặc nhập user ID hợp lệ!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                
                # Kiểm tra user có bị auto delete không
                if not self.is_user_auto_deleted(ctx.guild.id, target_user_id):
                    embed = discord.Embed(
                        title="⚠️ Thông báo",
                        description=f"User này không bị auto delete!",
                        color=discord.Color.orange()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Xóa user khỏi auto delete
                success = self.remove_auto_delete_user(ctx.guild.id, target_user_id, ctx.author.id)
                
                if success:
                    # Lấy thông tin user
                    user_info = target_user.display_name if target_user else f"User ID: {target_user_id}"
                    
                    embed = discord.Embed(
                        title="✅ Auto Delete đã TẮT",
                        description=f"**{user_info}** không còn bị xóa tin nhắn tự động!",
                        color=discord.Color.green(),
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
                        name="👑 Tắt bởi",
                        value=ctx.author.mention,
                        inline=True
                    )
                    
                    embed.set_footer(text="Auto Delete đã được vô hiệu hóa")
                    await ctx.reply(embed=embed, mention_author=True)
                    
                    logger.info(f"Auto Delete OFF: User {target_user_id} bởi {ctx.author} trong guild {ctx.guild.id}")
                else:
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description="Có lỗi xảy ra khi tắt auto delete!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                
            elif action.lower() == 'list':
                # Xem danh sách user bị auto delete
                guild_users = self.auto_delete_users.get(ctx.guild.id, {})
                active_users = {uid: data for uid, data in guild_users.items() if data.get('enabled', False)}
                
                if not active_users:
                    embed = discord.Embed(
                        title="📋 Danh sách Auto Delete",
                        description="Hiện tại không có user nào bị auto delete!",
                        color=discord.Color.green()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                embed = discord.Embed(
                    title="🗑️ Danh sách Auto Delete",
                    description=f"Có **{len(active_users)}** user đang bị auto delete:",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                # Hiển thị tối đa 10 user để tránh embed quá dài
                user_list = list(active_users.items())[:10]
                user_info_list = []
                
                for user_id, user_data in user_list:
                    try:
                        user = await self.bot.fetch_user(user_id)
                        user_info = f"**{user.display_name}** (`{user_id}`)"
                    except:
                        user_info = f"**Unknown User** (`{user_id}`)"
                    
                    # Thêm thông tin admin đã thêm
                    try:
                        admin = await self.bot.fetch_user(user_data.get('added_by', 0))
                        admin_info = f" - *Bởi: {admin.display_name}*"
                    except:
                        admin_info = ""
                    
                    user_info_list.append(user_info + admin_info)
                
                embed.add_field(
                    name="👥 Users bị Auto Delete",
                    value="\n".join(user_info_list) if user_info_list else "Không có user nào",
                    inline=False
                )
                
                if len(active_users) > 10:
                    embed.add_field(
                        name="⚠️ Lưu ý",
                        value=f"Chỉ hiển thị 10/{len(active_users)} user đầu tiên",
                        inline=False
                    )
                
                embed.set_footer(text="Sử dụng ;xoa history để xem lịch sử")
                await ctx.reply(embed=embed, mention_author=True)
                
            elif action.lower() == 'history':
                # Xem lịch sử (chỉ Supreme Admin)
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể xem lịch sử Auto Delete!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                try:
                    # Parse limit
                    limit = 10
                    if target:
                        try:
                            limit = max(1, min(int(target), 20))  # Từ 1 đến 20
                        except ValueError:
                            pass
                    
                    # Load history từ file
                    history_data = []
                    if os.path.exists(self.auto_delete_file):
                        with open(self.auto_delete_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            history_data = data.get('delete_history', [])
                    
                    # Filter theo guild hiện tại
                    guild_history = [h for h in history_data if h.get('guild_id') == ctx.guild.id]
                    
                    if not guild_history:
                        embed = discord.Embed(
                            title="📋 Lịch sử Auto Delete",
                            description="Chưa có lịch sử auto delete nào trong server này!",
                            color=discord.Color.blue()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                    
                    # Hiển thị entries gần nhất
                    recent_history = guild_history[-limit:]
                    
                    embed = discord.Embed(
                        title="📋 Lịch sử Auto Delete",
                        description=f"**{len(recent_history)}** hoạt động gần nhất:",
                        color=discord.Color.blue(),
                        timestamp=datetime.now()
                    )
                    
                    for entry in reversed(recent_history):  # Hiển thị từ mới nhất
                        action_emoji = "🗑️" if entry['action'] == 'add' else "✅"
                        action_text = "BẬT" if entry['action'] == 'add' else "TẮT"
                        
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
                            name=f"{action_emoji} {action_text} Auto Delete",
                            value=field_value,
                            inline=False
                        )
                    
                    if len(guild_history) > limit:
                        embed.set_footer(text=f"Hiển thị {limit}/{len(guild_history)} hoạt động")
                    
                    await ctx.reply(embed=embed, mention_author=True)
                    
                except Exception as e:
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description=f"Có lỗi xảy ra khi tải lịch sử: {str(e)}",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    logger.error(f"Lỗi trong auto delete history: {e}")
                
            elif action.lower() == 'remove':
                # Xóa user khỏi danh sách auto delete
                if not target:
                    embed = discord.Embed(
                        title="❌ Thiếu thông tin",
                        description="Vui lòng cung cấp User ID cần xóa!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="💡 Cách sử dụng",
                        value="`/xoa remove <user_id>`",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Parse user ID
                try:
                    target_user_id = int(target)
                except ValueError:
                    embed = discord.Embed(
                        title="❌ User ID không hợp lệ",
                        description="Vui lòng cung cấp User ID hợp lệ (chỉ số)!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="📝 Ví dụ",
                        value="`/xoa remove 123456789`",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra user có trong danh sách auto delete không
                if not self.is_user_auto_deleted(ctx.guild.id, target_user_id):
                    embed = discord.Embed(
                        title="⚠️ User không có trong danh sách",
                        description=f"User ID `{target_user_id}` không có trong danh sách Auto Delete!",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="💡 Kiểm tra danh sách",
                        value="`/xoa list` - Xem tất cả user bị Auto Delete",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Xóa user khỏi danh sách
                self.remove_auto_delete_user(ctx.guild.id, target_user_id, ctx.author.id)
                
                # Lấy thông tin user
                try:
                    target_user = await self.bot.fetch_user(target_user_id)
                    user_display = f"{target_user.display_name} ({target_user_id})"
                except:
                    user_display = f"User ID: {target_user_id}"
                
                embed = discord.Embed(
                    title="✅ Đã xóa khỏi Auto Delete",
                    description=f"Đã xóa **{user_display}** khỏi danh sách Auto Delete",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🔄 Kết quả",
                    value=(
                        "• User có thể gửi tin nhắn bình thường\n"
                        "• Tin nhắn không còn bị xóa tự động\n"
                        "• Không còn emoji 🔥 tự động"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="👤 Được thực hiện bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                embed.set_footer(text="User đã được gỡ khỏi Auto Delete")
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"Auto Delete REMOVE: User {target_user_id} bởi {ctx.author} trong guild {ctx.guild.id}")
                
            elif action.lower() == 'fireemoji':
                # Xử lý các tùy chọn fireemoji
                if target and target.lower() in ['on', 'off']:
                    # Bật/tắt tự động thêm emoji 🔥 toàn cục
                    old_status = self.auto_fire_emoji
                    self.auto_fire_emoji = (target.lower() == 'on')
                    embed = discord.Embed(
                        title="🔥 Auto Fire Emoji",
                        description=f"Tự động thêm emoji 🔥 đã được **{'BẬT' if self.auto_fire_emoji else 'TẮT'}**",
                        color=discord.Color.orange() if self.auto_fire_emoji else discord.Color.gray()
                    )
                    
                    embed.add_field(
                        name="🔧 Cách hoạt động",
                        value=(
                            "• **BẬT**: Tự động thêm emoji 🔥 vào tin nhắn trước khi xóa\n"
                            "• **TẮT**: Chỉ xóa tin nhắn không thêm emoji\n"
                            "• Admin có thể thấy emoji trước khi tin nhắn bị xóa"
                        ),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📝 Lệnh",
                        value=(
                            "`/xoa fireemoji on` - Bật toàn cục\n"
                            "`/xoa fireemoji off` - Tắt toàn cục\n"
                            "`/xoa fireemoji <user_id>` - Bật auto delete + fire emoji cho user"
                        ),
                        inline=False
                    )
                    
                    await ctx.reply(embed=embed, mention_author=True)
                    logger.info(f"Auto Fire Emoji: {old_status} -> {self.auto_fire_emoji} bởi {ctx.author}")
                
                elif target and target.isdigit():
                    # Bật auto delete + fire emoji cho user cụ thể
                    target_user_id = int(target)
                    
                    # Kiểm tra không thể tự auto delete chính mình
                    if target_user_id == ctx.author.id:
                        embed = discord.Embed(
                            title="❌ Không thể tự auto delete",
                            description="Bạn không thể bật auto delete cho chính mình!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                    
                    # Kiểm tra không thể auto delete admin khác
                    if self.bot_instance.is_admin(target_user_id):
                        embed = discord.Embed(
                            title="❌ Không thể auto delete admin",
                            description="Không thể bật auto delete cho admin khác!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                    
                    # Kiểm tra user đã bị auto delete chưa
                    if self.is_user_auto_deleted(ctx.guild.id, target_user_id):
                        embed = discord.Embed(
                            title="⚠️ User đã bị Auto Delete",
                            description=f"User <@{target_user_id}> đã bị auto delete rồi!",
                            color=discord.Color.orange()
                        )
                        embed.add_field(
                            name="💡 Lưu ý",
                            value="Fire emoji sẽ tự động được thêm vào tin nhắn của user này",
                            inline=False
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                    
                    # Bật auto delete cho user
                    self.add_auto_delete_user(ctx.guild.id, target_user_id, ctx.author.id)
                    
                    # Lấy thông tin user
                    try:
                        target_user = await self.bot.fetch_user(target_user_id)
                        user_display = f"{target_user.display_name} ({target_user_id})"
                    except:
                        user_display = f"User ID: {target_user_id}"
                    
                    embed = discord.Embed(
                        title="🔥 Auto Delete + Fire Emoji",
                        description=f"Đã bật **Auto Delete + Fire Emoji** cho {user_display}",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="🔥 Cách hoạt động",
                        value=(
                            "• Tất cả tin nhắn của user sẽ có emoji 🔥 tự động\n"
                            "• Tin nhắn sẽ bị xóa sau 0.3 giây\n"
                            "• Admin có thể thấy emoji trước khi tin nhắn biến mất"
                        ),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="🛑 Tắt Auto Delete",
                        value=f"`/xoa off {target_user_id}`",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="👤 Được thực hiện bởi",
                        value=ctx.author.mention,
                        inline=True
                    )
                    
                    embed.set_footer(text="Auto Delete + Fire Emoji đã được kích hoạt")
                    await ctx.reply(embed=embed, mention_author=True)
                    
                    logger.info(f"Auto Delete + Fire Emoji ON: User {target_user_id} bởi {ctx.author} trong guild {ctx.guild.id}")
                
                else:
                    # Hiển thị trạng thái và hướng dẫn
                    embed = discord.Embed(
                        title="🔥 Auto Fire Emoji - Hướng dẫn",
                        description=f"Trạng thái toàn cục: **{'BẬT' if self.auto_fire_emoji else 'TẮT'}**",
                        color=discord.Color.orange() if self.auto_fire_emoji else discord.Color.gray()
                    )
                    
                    embed.add_field(
                        name="💡 Mô tả",
                        value=(
                            "Tự động thêm emoji 🔥 vào tin nhắn của user bị Auto Delete\n"
                            "trước khi xóa để admin có thể thấy."
                        ),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="🔧 Lệnh điều khiển",
                        value=(
                            "`/xoa fireemoji on` - Bật toàn cục\n"
                            "`/xoa fireemoji off` - Tắt toàn cục\n"
                            "`/xoa fireemoji <user_id>` - Bật auto delete + fire emoji cho user\n"
                            "`/xoa fireemoji` - Xem hướng dẫn này"
                        ),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📝 Ví dụ",
                        value=(
                            "`/xoa fireemoji 123456789` - Bật cho user ID\n"
                            "User đó sẽ có emoji 🔥 trên mọi tin nhắn trước khi bị xóa"
                        ),
                        inline=False
                    )
                    
                    await ctx.reply(embed=embed, mention_author=True)
                
            else:
                embed = discord.Embed(
                    title="❌ Action không hợp lệ",
                    description=f"Action `{action}` không được hỗ trợ!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Actions hợp lệ",
                    value="`on`, `off`, `list`, `history`, `remove`, `fireemoji`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        logger.info("Auto Delete commands đã được đăng ký")
