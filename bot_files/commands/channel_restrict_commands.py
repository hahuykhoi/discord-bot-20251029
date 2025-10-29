# -*- coding: utf-8 -*-
"""
Channel Restriction Commands - Giới hạn chat channel cho users
Supreme Admin có thể chat mọi nơi, users bị giới hạn chỉ chat được ở channel được phép
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChannelRestrictCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.data_folder = 'data'
        self.channel_restrict_file = os.path.join(self.data_folder, 'channel_restrictions.json')
        
        # Tạo data folder nếu chưa có
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            
        self.channel_restrictions = {}  # {guild_id: {user_id: [allowed_channel_ids], 'global_restricted_users': [user_ids]}}
        self.load_channel_restrictions()
    
    def load_channel_restrictions(self):
        """Tải cấu hình giới hạn channel từ file JSON"""
        try:
            if os.path.exists(self.channel_restrict_file):
                with open(self.channel_restrict_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    self.channel_restrictions = {}
                    for guild_id, guild_data in data.items():
                        guild_id_int = int(guild_id)
                        self.channel_restrictions[guild_id_int] = {}
                        
                        for key, value in guild_data.items():
                            if key == 'global_restricted_users':
                                self.channel_restrictions[guild_id_int][key] = [int(uid) for uid in value]
                            else:
                                user_id_int = int(key)
                                self.channel_restrictions[guild_id_int][user_id_int] = [int(cid) for cid in value]
                                
                logger.info(f"Đã tải {len(self.channel_restrictions)} guild channel restrictions")
            else:
                self.channel_restrictions = {}
                logger.info("Chưa có file channel restrictions, tạo mới")
        except Exception as e:
            logger.error(f"Lỗi khi tải channel restrictions: {e}")
            self.channel_restrictions = {}
    
    def save_channel_restrictions(self):
        """Lưu cấu hình giới hạn channel vào file JSON"""
        try:
            # Convert int keys to string for JSON
            data_to_save = {}
            for guild_id, guild_data in self.channel_restrictions.items():
                guild_data_str = {}
                for key, value in guild_data.items():
                    if key == 'global_restricted_users':
                        guild_data_str[key] = [str(uid) for uid in value]
                    else:
                        guild_data_str[str(key)] = [str(cid) for cid in value]
                data_to_save[str(guild_id)] = guild_data_str
            
            with open(self.channel_restrict_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu channel restrictions")
        except Exception as e:
            logger.error(f"Lỗi khi lưu channel restrictions: {e}")
    
    def is_user_channel_restricted(self, guild_id: int, user_id: int, channel_id: int) -> bool:
        """Kiểm tra user có bị giới hạn channel không"""
        try:
            # Supreme Admin không bị giới hạn
            if user_id == self.bot_instance.supreme_admin_id:
                return False
            
            # Admin không bị giới hạn
            if self.bot_instance.is_admin(user_id):
                return False
            
            guild_data = self.channel_restrictions.get(guild_id, {})
            
            # Kiểm tra user có trong danh sách bị giới hạn không
            if user_id in guild_data:
                allowed_channels = guild_data[user_id]
                return channel_id not in allowed_channels
            
            # Kiểm tra global restriction
            global_restricted = guild_data.get('global_restricted_users', [])
            if user_id in global_restricted:
                return True  # Bị cấm chat toàn bộ server
            
            return False  # Không bị giới hạn
            
        except Exception as e:
            logger.error(f"Lỗi kiểm tra channel restriction: {e}")
            return False
    
    def add_channel_restriction(self, guild_id: int, user_id: int, allowed_channels: list):
        """Thêm giới hạn channel cho user"""
        if guild_id not in self.channel_restrictions:
            self.channel_restrictions[guild_id] = {}
        
        self.channel_restrictions[guild_id][user_id] = allowed_channels
        self.save_channel_restrictions()
    
    def remove_channel_restriction(self, guild_id: int, user_id: int):
        """Bỏ giới hạn channel cho user"""
        if guild_id in self.channel_restrictions and user_id in self.channel_restrictions[guild_id]:
            del self.channel_restrictions[guild_id][user_id]
            self.save_channel_restrictions()
            return True
        return False
    
    def add_global_restriction(self, guild_id: int, user_id: int):
        """Cấm user chat toàn bộ server"""
        if guild_id not in self.channel_restrictions:
            self.channel_restrictions[guild_id] = {}
        
        if 'global_restricted_users' not in self.channel_restrictions[guild_id]:
            self.channel_restrictions[guild_id]['global_restricted_users'] = []
        
        if user_id not in self.channel_restrictions[guild_id]['global_restricted_users']:
            self.channel_restrictions[guild_id]['global_restricted_users'].append(user_id)
            self.save_channel_restrictions()
            return True
        return False
    
    def remove_global_restriction(self, guild_id: int, user_id: int):
        """Bỏ cấm chat toàn bộ server cho user"""
        if (guild_id in self.channel_restrictions and 
            'global_restricted_users' in self.channel_restrictions[guild_id] and
            user_id in self.channel_restrictions[guild_id]['global_restricted_users']):
            
            self.channel_restrictions[guild_id]['global_restricted_users'].remove(user_id)
            self.save_channel_restrictions()
            return True
        return False
    
    async def handle_channel_restrict_message(self, message):
        """Xử lý tin nhắn - xóa nếu user vi phạm giới hạn channel"""
        try:
            # Bỏ qua bot messages
            if message.author.bot:
                return False
            
            # Bỏ qua DM
            if not message.guild:
                return False
            
            guild_id = message.guild.id
            user_id = message.author.id
            channel_id = message.channel.id
            
            # Kiểm tra user có bị giới hạn channel không
            if self.is_user_channel_restricted(guild_id, user_id, channel_id):
                # Xóa tin nhắn vi phạm
                try:
                    await message.delete()
                    
                    # Gửi thông báo riêng tư cho user
                    embed = discord.Embed(
                        title="🚫 Tin nhắn bị xóa",
                        description="Bạn không được phép chat trong channel này!",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📍 Channel bị cấm",
                        value=f"<#{channel_id}>",
                        inline=True
                    )
                    
                    # Hiển thị channels được phép (nếu có)
                    guild_data = self.channel_restrictions.get(guild_id, {})
                    if user_id in guild_data:
                        allowed_channels = guild_data[user_id]
                        if allowed_channels:
                            channels_text = '\n'.join([f"<#{cid}>" for cid in allowed_channels])
                            embed.add_field(
                                name="✅ Channels được phép",
                                value=channels_text,
                                inline=False
                            )
                    else:
                        embed.add_field(
                            name="⛔ Trạng thái",
                            value="Bạn bị cấm chat toàn bộ server",
                            inline=False
                        )
                    
                    embed.add_field(
                        name="💡 Liên hệ",
                        value="Liên hệ Admin để được hỗ trợ",
                        inline=False
                    )
                    
                    try:
                        await message.author.send(embed=embed)
                    except:
                        # Nếu không gửi được DM, gửi trong channel rồi xóa sau 5s
                        warning_msg = await message.channel.send(
                            f"{message.author.mention} Bạn không được phép chat trong channel này!", 
                            delete_after=5
                        )
                    
                    logger.info(f"Đã xóa tin nhắn vi phạm channel restriction: {user_id} trong {channel_id}")
                    return True
                    
                except discord.Forbidden:
                    logger.warning(f"Không có quyền xóa tin nhắn trong {channel_id}")
                except Exception as e:
                    logger.error(f"Lỗi khi xóa tin nhắn vi phạm: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Lỗi trong handle_channel_restrict_message: {e}")
            return False
    
    async def handle_restrict_command(self, ctx, action: str = None, user: discord.Member = None, *channels):
        """Xử lý lệnh restrict channel"""
        
        # Kiểm tra quyền admin
        if not self.bot_instance.is_admin(ctx.author.id):
            embed = discord.Embed(
                title="❌ Không có quyền",
                description="Chỉ Admin mới có thể sử dụng lệnh này!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        if not action:
            # Hiển thị hướng dẫn
            embed = discord.Embed(
                title="🔒 Channel Restriction System",
                description="Hệ thống giới hạn chat channel cho users",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📝 Các lệnh có sẵn",
                value="`/restrict add @user #channel1 #channel2` - Giới hạn user chỉ chat được ở channels chỉ định\n"
                      "`/restrict remove @user` - Bỏ giới hạn channel cho user\n"
                      "`/restrict ban @user` - Cấm user chat toàn bộ server\n"
                      "`/restrict unban @user` - Bỏ cấm chat toàn bộ server\n"
                      "`/restrict list` - Xem danh sách users bị giới hạn\n"
                      "`/restrict check @user` - Kiểm tra trạng thái giới hạn của user",
                inline=False
            )
            
            embed.add_field(
                name="👑 Quyền đặc biệt",
                value="• **Supreme Admin**: Chat được mọi nơi, không bị giới hạn\n"
                      "• **Admin**: Chat được mọi nơi, quản lý restrictions\n"
                      "• **User**: Bị giới hạn theo cấu hình",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Lưu ý",
                value="• User bị restrict sẽ có tin nhắn bị xóa tự động\n"
                      "• Nhận thông báo riêng tư khi vi phạm\n"
                      "• Supreme Admin và Admin không bao giờ bị giới hạn",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        guild_id = ctx.guild.id
        
        if action.lower() == 'add':
            if not user:
                embed = discord.Embed(
                    title="❌ Thiếu thông tin",
                    description="Vui lòng mention user cần giới hạn!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value="`/restrict add @user #channel1 #channel2`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Không thể restrict admin
            if self.bot_instance.is_admin(user.id) or user.id == self.bot_instance.supreme_admin_id:
                embed = discord.Embed(
                    title="❌ Không thể giới hạn",
                    description="Không thể giới hạn Admin hoặc Supreme Admin!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not channels:
                embed = discord.Embed(
                    title="❌ Thiếu channels",
                    description="Vui lòng chỉ định ít nhất 1 channel được phép!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value="`/restrict add @user #channel1 #channel2`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Parse channels
            allowed_channel_ids = []
            channel_mentions = []
            
            for channel_mention in channels:
                # Xử lý channel mention hoặc ID
                if channel_mention.startswith('<#') and channel_mention.endswith('>'):
                    channel_id = int(channel_mention[2:-1])
                elif channel_mention.isdigit():
                    channel_id = int(channel_mention)
                else:
                    continue
                
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    allowed_channel_ids.append(channel_id)
                    channel_mentions.append(f"<#{channel_id}>")
            
            if not allowed_channel_ids:
                embed = discord.Embed(
                    title="❌ Channels không hợp lệ",
                    description="Không tìm thấy channels hợp lệ nào!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Thêm restriction
            self.add_channel_restriction(guild_id, user.id, allowed_channel_ids)
            
            embed = discord.Embed(
                title="✅ Đã giới hạn channel",
                description=f"User {user.mention} chỉ được chat trong các channels được chỉ định",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User bị giới hạn",
                value=f"{user.mention} (`{user.id}`)",
                inline=True
            )
            
            embed.add_field(
                name="📍 Channels được phép",
                value='\n'.join(channel_mentions),
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Lưu ý",
                value="Tin nhắn ở channels khác sẽ bị xóa tự động",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            
        elif action.lower() == 'remove':
            if not user:
                embed = discord.Embed(
                    title="❌ Thiếu thông tin",
                    description="Vui lòng mention user cần bỏ giới hạn!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Bỏ restriction
            success = self.remove_channel_restriction(guild_id, user.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Đã bỏ giới hạn channel",
                    description=f"User {user.mention} có thể chat tự do trong tất cả channels",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ User không bị giới hạn",
                    description=f"User {user.mention} không có giới hạn channel nào",
                    color=discord.Color.orange()
                )
            
            await ctx.reply(embed=embed, mention_author=True)
            
        elif action.lower() == 'ban':
            if not user:
                embed = discord.Embed(
                    title="❌ Thiếu thông tin",
                    description="Vui lòng mention user cần cấm chat!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Không thể ban admin
            if self.bot_instance.is_admin(user.id) or user.id == self.bot_instance.supreme_admin_id:
                embed = discord.Embed(
                    title="❌ Không thể cấm",
                    description="Không thể cấm chat Admin hoặc Supreme Admin!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Thêm global restriction
            success = self.add_global_restriction(guild_id, user.id)
            
            if success:
                embed = discord.Embed(
                    title="🚫 Đã cấm chat toàn server",
                    description=f"User {user.mention} không thể chat trong bất kỳ channel nào",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ User đã bị cấm",
                    description=f"User {user.mention} đã bị cấm chat toàn server rồi",
                    color=discord.Color.orange()
                )
            
            await ctx.reply(embed=embed, mention_author=True)
            
        elif action.lower() == 'unban':
            if not user:
                embed = discord.Embed(
                    title="❌ Thiếu thông tin",
                    description="Vui lòng mention user cần bỏ cấm chat!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Bỏ global restriction
            success = self.remove_global_restriction(guild_id, user.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Đã bỏ cấm chat",
                    description=f"User {user.mention} có thể chat bình thường trở lại",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ User không bị cấm",
                    description=f"User {user.mention} không bị cấm chat toàn server",
                    color=discord.Color.orange()
                )
            
            await ctx.reply(embed=embed, mention_author=True)
            
        elif action.lower() == 'list':
            guild_data = self.channel_restrictions.get(guild_id, {})
            
            embed = discord.Embed(
                title="📋 Danh sách giới hạn channel",
                description="Users bị giới hạn chat trong server này",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Users bị cấm toàn server
            global_banned = guild_data.get('global_restricted_users', [])
            if global_banned:
                banned_text = []
                for user_id in global_banned[:10]:  # Giới hạn 10 users
                    try:
                        user = ctx.guild.get_member(user_id)
                        if user:
                            banned_text.append(f"• {user.mention} (`{user_id}`)")
                        else:
                            banned_text.append(f"• User ID: `{user_id}` (đã rời server)")
                    except:
                        banned_text.append(f"• User ID: `{user_id}`")
                
                if len(global_banned) > 10:
                    banned_text.append(f"... và {len(global_banned) - 10} user khác")
                
                embed.add_field(
                    name="🚫 Cấm chat toàn server",
                    value='\n'.join(banned_text) if banned_text else "Không có",
                    inline=False
                )
            
            # Users bị giới hạn channels
            channel_restricted = {k: v for k, v in guild_data.items() if k != 'global_restricted_users'}
            if channel_restricted:
                restricted_text = []
                count = 0
                for user_id, allowed_channels in channel_restricted.items():
                    if count >= 5:  # Giới hạn 5 users
                        break
                    try:
                        user = ctx.guild.get_member(user_id)
                        channels_text = ', '.join([f"<#{cid}>" for cid in allowed_channels[:3]])
                        if len(allowed_channels) > 3:
                            channels_text += f" (+{len(allowed_channels) - 3})"
                        
                        if user:
                            restricted_text.append(f"• {user.mention}: {channels_text}")
                        else:
                            restricted_text.append(f"• `{user_id}`: {channels_text}")
                        count += 1
                    except:
                        pass
                
                if len(channel_restricted) > 5:
                    restricted_text.append(f"... và {len(channel_restricted) - 5} user khác")
                
                embed.add_field(
                    name="🔒 Giới hạn channels",
                    value='\n'.join(restricted_text) if restricted_text else "Không có",
                    inline=False
                )
            
            if not global_banned and not channel_restricted:
                embed.add_field(
                    name="✅ Trạng thái",
                    value="Không có user nào bị giới hạn channel",
                    inline=False
                )
            
            embed.set_footer(text=f"Tổng: {len(global_banned)} banned, {len(channel_restricted)} restricted")
            
            await ctx.reply(embed=embed, mention_author=True)
            
        elif action.lower() == 'check':
            if not user:
                embed = discord.Embed(
                    title="❌ Thiếu thông tin",
                    description="Vui lòng mention user cần kiểm tra!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            guild_data = self.channel_restrictions.get(guild_id, {})
            
            embed = discord.Embed(
                title="🔍 Kiểm tra giới hạn channel",
                description=f"Trạng thái giới hạn của {user.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{user.mention} (`{user.id}`)",
                inline=True
            )
            
            # Kiểm tra quyền đặc biệt
            if user.id == self.bot_instance.supreme_admin_id:
                embed.add_field(
                    name="👑 Quyền",
                    value="Supreme Admin",
                    inline=True
                )
                embed.add_field(
                    name="✅ Trạng thái",
                    value="Chat được mọi nơi (không bị giới hạn)",
                    inline=False
                )
            elif self.bot_instance.is_admin(user.id):
                embed.add_field(
                    name="🛡️ Quyền",
                    value="Admin",
                    inline=True
                )
                embed.add_field(
                    name="✅ Trạng thái",
                    value="Chat được mọi nơi (không bị giới hạn)",
                    inline=False
                )
            else:
                embed.add_field(
                    name="👥 Quyền",
                    value="User thường",
                    inline=True
                )
                
                # Kiểm tra global ban
                global_banned = guild_data.get('global_restricted_users', [])
                if user.id in global_banned:
                    embed.add_field(
                        name="🚫 Trạng thái",
                        value="Bị cấm chat toàn server",
                        inline=False
                    )
                    embed.color = discord.Color.red()
                elif user.id in guild_data:
                    # Bị giới hạn channels
                    allowed_channels = guild_data[user.id]
                    channels_text = '\n'.join([f"<#{cid}>" for cid in allowed_channels])
                    
                    embed.add_field(
                        name="🔒 Trạng thái",
                        value="Bị giới hạn channels",
                        inline=False
                    )
                    embed.add_field(
                        name="✅ Channels được phép",
                        value=channels_text,
                        inline=False
                    )
                    embed.color = discord.Color.orange()
                else:
                    embed.add_field(
                        name="✅ Trạng thái",
                        value="Không bị giới hạn (chat được mọi nơi)",
                        inline=False
                    )
                    embed.color = discord.Color.green()
            
            await ctx.reply(embed=embed, mention_author=True)
            
        else:
            embed = discord.Embed(
                title="❌ Action không hợp lệ",
                description=f"Action `{action}` không được hỗ trợ!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Actions hợp lệ",
                value="`add`, `remove`, `ban`, `unban`, `list`, `check`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
    
    def register_commands(self) -> None:
        """Đăng ký các commands cho Channel Restriction"""
        
        @self.bot.command(name='restrict', description='Quản lý giới hạn chat channel cho users')
        async def restrict_command(ctx, action: str = None, user: discord.Member = None, *channels):
            await self.handle_restrict_command(ctx, action, user, *channels)
