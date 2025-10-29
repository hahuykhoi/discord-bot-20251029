# -*- coding: utf-8 -*-
"""
Fire Delete Commands - Hệ thống xóa tin nhắn bằng emoji lửa 🔥
Admin react emoji 🔥 vào tin nhắn để xóa ngay lập tức
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FireDeleteCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.data_folder = 'data'
        self.fire_delete_file = os.path.join(self.data_folder, 'fire_delete_config.json')
        
        # Tạo data folder nếu chưa có
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.fire_delete_config = {}  # {guild_id: {'enabled': bool, 'delete_history': []}}
        self.load_fire_delete_config()
    
    def load_fire_delete_config(self):
        """Tải cấu hình fire delete từ file JSON"""
        try:
            if os.path.exists(self.fire_delete_file):
                with open(self.fire_delete_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    for guild_id_str, config in data.get('fire_delete_config', {}).items():
                        guild_id = int(guild_id_str)
                        self.fire_delete_config[guild_id] = config
                
                logger.info(f"Đã tải fire delete config từ {len(self.fire_delete_config)} guild")
            else:
                # Tạo file config mặc định
                default_data = {
                    "fire_delete_config": {},
                    "description": "Cấu hình Fire Delete theo guild",
                    "global_delete_history": []
                }
                with open(self.fire_delete_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Đã tạo file fire delete config mới: {self.fire_delete_file}")
        except Exception as e:
            logger.error(f"Lỗi khi tải fire delete config: {e}")
    
    def save_fire_delete_config(self):
        """Lưu cấu hình fire delete vào file JSON"""
        try:
            # Load existing data để giữ lại global_delete_history
            existing_data = {}
            if os.path.exists(self.fire_delete_file):
                with open(self.fire_delete_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Convert int keys to string for JSON
            fire_delete_data = {}
            for guild_id, config in self.fire_delete_config.items():
                fire_delete_data[str(guild_id)] = config
            
            # Update fire_delete_config
            existing_data['fire_delete_config'] = fire_delete_data
            existing_data['description'] = "Cấu hình Fire Delete theo guild"
            
            with open(self.fire_delete_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu fire delete config thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu fire delete config: {e}")
    
    def add_delete_history(self, guild_id: int, admin_id: int, message_info: dict, success: bool, error: str = ""):
        """Thêm lịch sử fire delete vào file"""
        try:
            # Load existing data
            existing_data = {}
            if os.path.exists(self.fire_delete_file):
                with open(self.fire_delete_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Ensure global_delete_history exists
            if 'global_delete_history' not in existing_data:
                existing_data['global_delete_history'] = []
            
            # Add new history entry
            history_entry = {
                'guild_id': guild_id,
                'admin_id': admin_id,
                'message_info': message_info,
                'success': success,
                'error': error,
                'timestamp': datetime.now().isoformat()
            }
            
            existing_data['global_delete_history'].append(history_entry)
            
            # Keep only last 100 entries để tránh file quá lớn
            if len(existing_data['global_delete_history']) > 100:
                existing_data['global_delete_history'] = existing_data['global_delete_history'][-100:]
            
            # Save back to file
            with open(self.fire_delete_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Lỗi khi thêm fire delete history: {e}")
    
    def is_fire_delete_enabled(self, guild_id: int) -> bool:
        """Kiểm tra xem fire delete có được bật cho guild không"""
        return self.fire_delete_config.get(guild_id, {}).get('enabled', False)
    
    def enable_fire_delete(self, guild_id: int):
        """Bật fire delete cho guild"""
        if guild_id not in self.fire_delete_config:
            self.fire_delete_config[guild_id] = {}
        
        self.fire_delete_config[guild_id]['enabled'] = True
        self.save_fire_delete_config()
    
    def disable_fire_delete(self, guild_id: int):
        """Tắt fire delete cho guild"""
        if guild_id not in self.fire_delete_config:
            self.fire_delete_config[guild_id] = {}
        
        self.fire_delete_config[guild_id]['enabled'] = False
        self.save_fire_delete_config()
    
    async def handle_fire_delete_reaction(self, reaction, user):
        """Xử lý khi có người react emoji 🔥"""
        try:
            # Bỏ qua nếu không phải emoji 🔥
            if str(reaction.emoji) != "🔥":
                return
            
            # Bỏ qua nếu là bot
            if user.bot:
                return
            
            # Bỏ qua nếu không phải trong guild
            if not reaction.message.guild:
                return
            
            guild_id = reaction.message.guild.id
            
            # Kiểm tra fire delete có được bật không
            if not self.is_fire_delete_enabled(guild_id):
                return
            
            # Kiểm tra quyền admin
            member = reaction.message.guild.get_member(user.id)
            if not member or not self.bot_instance.has_warn_permission(user.id, member.guild_permissions):
                # Gửi DM thông báo không có quyền
                try:
                    embed = discord.Embed(
                        title="❌ Không có quyền Fire Delete",
                        description="Chỉ admin mới có thể sử dụng emoji 🔥 để xóa tin nhắn!",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="🔥 Fire Delete",
                        value="Tính năng này chỉ dành cho admin để xóa tin nhắn nhanh chóng",
                        inline=False
                    )
                    embed.set_footer(text=f"Server: {reaction.message.guild.name}")
                    await user.send(embed=embed)
                except:
                    pass  # Không quan trọng nếu không gửi được DM
                return
            
            # Không thể xóa tin nhắn của chính bot
            if reaction.message.author == self.bot.user:
                try:
                    embed = discord.Embed(
                        title="⚠️ Không thể xóa tin nhắn bot",
                        description="Không thể sử dụng Fire Delete để xóa tin nhắn của chính bot!",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    await user.send(embed=embed)
                except:
                    pass
                return
            
            # Thông tin tin nhắn để lưu lịch sử
            message_info = {
                'message_id': reaction.message.id,
                'channel_id': reaction.message.channel.id,
                'channel_name': reaction.message.channel.name,
                'author_id': reaction.message.author.id,
                'author_name': reaction.message.author.display_name,
                'content_preview': reaction.message.content[:100] if reaction.message.content else "[No content]"
            }
            
            # Thử xóa tin nhắn
            try:
                await reaction.message.delete()
                
                # Gửi DM thông báo thành công
                try:
                    embed = discord.Embed(
                        title="🔥 Fire Delete thành công!",
                        description="Tin nhắn đã được xóa thành công!",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📍 Kênh",
                        value=f"#{message_info['channel_name']}",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="👤 Tác giả",
                        value=message_info['author_name'],
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📝 Nội dung",
                        value=f"```{message_info['content_preview']}```",
                        inline=False
                    )
                    
                    embed.set_footer(text=f"Server: {reaction.message.guild.name}")
                    await user.send(embed=embed)
                except:
                    pass  # Không quan trọng nếu không gửi được DM
                
                # Lưu lịch sử thành công
                self.add_delete_history(guild_id, user.id, message_info, True)
                
                logger.info(f"Fire Delete: Admin {user} đã xóa tin nhắn của {reaction.message.author} trong #{reaction.message.channel.name}")
                
            except discord.Forbidden:
                # Không có quyền xóa tin nhắn
                try:
                    embed = discord.Embed(
                        title="❌ Fire Delete thất bại",
                        description="Bot không có quyền xóa tin nhắn này!",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="💡 Giải pháp",
                        value="Đảm bảo bot có quyền 'Manage Messages' trong kênh này",
                        inline=False
                    )
                    await user.send(embed=embed)
                except:
                    pass
                
                # Lưu lịch sử thất bại
                self.add_delete_history(guild_id, user.id, message_info, False, "No permission")
                
            except discord.NotFound:
                # Tin nhắn đã bị xóa
                try:
                    embed = discord.Embed(
                        title="⚠️ Tin nhắn đã bị xóa",
                        description="Tin nhắn này đã bị xóa trước đó!",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    await user.send(embed=embed)
                except:
                    pass
                
                # Lưu lịch sử thất bại
                self.add_delete_history(guild_id, user.id, message_info, False, "Message not found")
                
            except Exception as e:
                # Lỗi khác
                try:
                    embed = discord.Embed(
                        title="❌ Fire Delete lỗi",
                        description=f"Có lỗi xảy ra: {str(e)[:100]}",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    await user.send(embed=embed)
                except:
                    pass
                
                # Lưu lịch sử thất bại
                self.add_delete_history(guild_id, user.id, message_info, False, str(e)[:100])
                logger.error(f"Fire Delete error: {e}")
            
        except Exception as e:
            logger.error(f"Lỗi trong handle_fire_delete_reaction: {e}")
    
    def register_commands(self):
        """Thiết lập các lệnh fire delete"""
        
        @self.bot.command(name='firedelete')
        async def fire_delete_command(ctx, action: str = None, limit: int = 10):
            """
            Quản lý tính năng Fire Delete
            Chỉ admin mới có quyền sử dụng
            
            Usage: 
            - ;firedelete on - Bật fire delete cho server
            - ;firedelete off - Tắt fire delete cho server
            - ;firedelete status - Xem trạng thái fire delete
            - ;firedelete history [số lượng] - Xem lịch sử fire delete (Supreme Admin)
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ admin mới có thể quản lý Fire Delete!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not action:
                # Hiển thị hướng dẫn
                embed = discord.Embed(
                    title="🔥 Fire Delete System",
                    description="Hệ thống xóa tin nhắn bằng emoji lửa",
                    color=discord.Color.orange()
                )
                
                embed.add_field(
                    name="📝 Cách sử dụng",
                    value="`/firedelete on` - Bật fire delete\n"
                          "`/firedelete off` - Tắt fire delete\n"
                          "`/firedelete status` - Xem trạng thái\n"
                          "`/firedelete history [số]` - Xem lịch sử",
                    inline=False
                )
                
                embed.add_field(
                    name="🔥 Cách hoạt động",
                    value="• Admin react emoji 🔥 vào tin nhắn để xóa\n"
                          "• Chỉ admin mới có quyền sử dụng\n"
                          "• Thông báo DM kết quả cho admin\n"
                          "• Lưu lịch sử tất cả hoạt động",
                    inline=False
                )
                
                # Trạng thái hiện tại
                is_enabled = self.is_fire_delete_enabled(ctx.guild.id)
                status_text = "🟢 **Đang BẬT**" if is_enabled else "🔴 **Đang TẮT**"
                
                embed.add_field(
                    name="📊 Trạng thái hiện tại",
                    value=status_text,
                    inline=True
                )
                
                embed.set_footer(text="Chỉ admin mới có thể sử dụng lệnh này")
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if action.lower() == 'on':
                # Bật fire delete
                if self.is_fire_delete_enabled(ctx.guild.id):
                    embed = discord.Embed(
                        title="⚠️ Đã được bật",
                        description="Fire Delete đã được bật cho server này rồi!",
                        color=discord.Color.orange()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                self.enable_fire_delete(ctx.guild.id)
                
                embed = discord.Embed(
                    title="🔥 Fire Delete đã BẬT!",
                    description="Admin có thể react emoji 🔥 để xóa tin nhắn!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🎯 Cách sử dụng",
                    value="• React emoji 🔥 vào tin nhắn muốn xóa\n"
                          "• Tin nhắn sẽ bị xóa ngay lập tức\n"
                          "• Bạn sẽ nhận thông báo DM về kết quả",
                    inline=False
                )
                
                embed.add_field(
                    name="⚠️ Lưu ý",
                    value="• Chỉ admin mới có quyền sử dụng\n"
                          "• Không thể xóa tin nhắn của bot\n"
                          "• Bot cần quyền 'Manage Messages'",
                    inline=False
                )
                
                embed.add_field(
                    name="👑 Bật bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                embed.set_footer(text="Fire Delete đã được kích hoạt")
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"Fire Delete ON: Bật bởi {ctx.author} trong guild {ctx.guild.id}")
                
            elif action.lower() == 'off':
                # Tắt fire delete
                if not self.is_fire_delete_enabled(ctx.guild.id):
                    embed = discord.Embed(
                        title="⚠️ Đã được tắt",
                        description="Fire Delete đã được tắt cho server này rồi!",
                        color=discord.Color.orange()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                self.disable_fire_delete(ctx.guild.id)
                
                embed = discord.Embed(
                    title="🔴 Fire Delete đã TẮT!",
                    description="Admin không thể dùng emoji 🔥 để xóa tin nhắn nữa!",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📴 Tình trạng",
                    value="• Emoji 🔥 không còn hoạt động\n"
                          "• Sử dụng `/firedelete on` để bật lại",
                    inline=False
                )
                
                embed.add_field(
                    name="👑 Tắt bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                embed.set_footer(text="Fire Delete đã được vô hiệu hóa")
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"Fire Delete OFF: Tắt bởi {ctx.author} trong guild {ctx.guild.id}")
                
            elif action.lower() == 'status':
                # Xem trạng thái
                is_enabled = self.is_fire_delete_enabled(ctx.guild.id)
                
                embed = discord.Embed(
                    title="📊 Trạng thái Fire Delete",
                    color=discord.Color.green() if is_enabled else discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                status_text = "🟢 **ĐANG BẬT**" if is_enabled else "🔴 **ĐANG TẮT**"
                embed.add_field(
                    name="🔥 Fire Delete",
                    value=status_text,
                    inline=True
                )
                
                if is_enabled:
                    embed.add_field(
                        name="✅ Hoạt động",
                        value="Admin có thể react 🔥 để xóa tin nhắn",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="❌ Không hoạt động",
                        value="Sử dụng `/firedelete on` để bật",
                        inline=False
                    )
                
                embed.add_field(
                    name="🏠 Server",
                    value=ctx.guild.name,
                    inline=True
                )
                
                embed.set_footer(text="Fire Delete Status")
                await ctx.reply(embed=embed, mention_author=True)
                
            elif action.lower() == 'history':
                # Xem lịch sử (chỉ Supreme Admin)
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể xem lịch sử Fire Delete!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                try:
                    # Giới hạn limit
                    limit = max(1, min(limit, 20))  # Từ 1 đến 20
                    
                    # Load history từ file
                    history_data = []
                    if os.path.exists(self.fire_delete_file):
                        with open(self.fire_delete_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            history_data = data.get('global_delete_history', [])
                    
                    # Filter theo guild hiện tại
                    guild_history = [h for h in history_data if h.get('guild_id') == ctx.guild.id]
                    
                    if not guild_history:
                        embed = discord.Embed(
                            title="📋 Lịch sử Fire Delete",
                            description="Chưa có lịch sử fire delete nào trong server này!",
                            color=discord.Color.blue()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                    
                    # Hiển thị entries gần nhất
                    recent_history = guild_history[-limit:]
                    
                    embed = discord.Embed(
                        title="🔥 Lịch sử Fire Delete",
                        description=f"**{len(recent_history)}** hoạt động gần nhất:",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    
                    for entry in reversed(recent_history):  # Hiển thị từ mới nhất
                        success_emoji = "✅" if entry['success'] else "❌"
                        
                        # Lấy thông tin admin
                        try:
                            admin = await self.bot.fetch_user(entry['admin_id'])
                            admin_info = f"{admin.display_name}"
                        except:
                            admin_info = f"Unknown Admin"
                        
                        # Lấy thông tin tin nhắn
                        msg_info = entry.get('message_info', {})
                        channel_name = msg_info.get('channel_name', 'Unknown')
                        author_name = msg_info.get('author_name', 'Unknown')
                        content_preview = msg_info.get('content_preview', 'No content')
                        
                        # Format timestamp
                        try:
                            timestamp = datetime.fromisoformat(entry['timestamp'])
                            time_str = timestamp.strftime("%d/%m/%Y %H:%M")
                        except:
                            time_str = "Unknown time"
                        
                        field_value = f"**Admin:** {admin_info}\n"
                        field_value += f"**Channel:** #{channel_name}\n"
                        field_value += f"**Author:** {author_name}\n"
                        field_value += f"**Content:** {content_preview[:50]}...\n"
                        if not entry['success']:
                            field_value += f"**Error:** {entry.get('error', 'Unknown')}\n"
                        field_value += f"**Time:** {time_str}"
                        
                        embed.add_field(
                            name=f"{success_emoji} Fire Delete",
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
                    logger.error(f"Lỗi trong fire delete history: {e}")
                
            else:
                embed = discord.Embed(
                    title="❌ Action không hợp lệ",
                    description=f"Action `{action}` không được hỗ trợ!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Actions hợp lệ",
                    value="`on`, `off`, `status`, `history`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        logger.info("Fire Delete commands đã được đăng ký")
