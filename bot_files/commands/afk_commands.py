# -*- coding: utf-8 -*-
"""
AFK Commands - Hệ thống AFK cho Discord bot
Tính năng:
- Đặt trạng thái AFK với lý do
- Tự động thông báo khi có người mention user AFK
- Hiển thị thời gian AFK và lý do
- Tự động bỏ AFK khi user gửi tin nhắn đầu tiên
"""

import discord
from discord.ext import commands
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AFKCommands:
    def __init__(self, bot_instance):
        """
        Khởi tạo AFK Commands
        
        Args:
            bot_instance: Instance của bot chính
        """
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.afk_file = 'afk_data.json'
        self.afk_users: Dict[int, dict] = {}  # user_id -> {reason, timestamp, guild_id}
        
        # Load AFK data
        self.load_afk_data()
        
        logger.info("AFK Commands đã được khởi tạo")
    
    def load_afk_data(self) -> None:
        """
        Tải dữ liệu AFK từ file JSON
        """
        try:
            if os.path.exists(self.afk_file):
                with open(self.afk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    self.afk_users = {int(k): v for k, v in data.items()}
                logger.info(f"Đã tải {len(self.afk_users)} AFK users từ {self.afk_file}")
            else:
                logger.info("Không tìm thấy file AFK data, khởi tạo mới")
        except Exception as e:
            logger.error(f"Lỗi khi tải AFK data: {e}")
    
    def save_afk_data(self) -> None:
        """
        Lưu dữ liệu AFK vào file JSON
        """
        try:
            # Convert int keys to string for JSON
            data_to_save = {str(k): v for k, v in self.afk_users.items()}
            with open(self.afk_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu AFK data thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu AFK data: {e}")
    
    def set_afk(self, user_id: int, reason: str, guild_id: int) -> None:
        """
        Đặt user vào trạng thái AFK
        
        Args:
            user_id: ID của user
            reason: Lý do AFK
            guild_id: ID của guild
        """
        self.afk_users[user_id] = {
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'guild_id': guild_id
        }
        self.save_afk_data()
        logger.info(f"User {user_id} đã được đặt AFK với lý do: {reason}")
    
    def remove_afk(self, user_id: int) -> Optional[dict]:
        """
        Bỏ trạng thái AFK của user
        
        Args:
            user_id: ID của user
            
        Returns:
            dict: Thông tin AFK trước đó (nếu có)
        """
        afk_data = self.afk_users.pop(user_id, None)
        if afk_data:
            self.save_afk_data()
            logger.info(f"User {user_id} đã bỏ trạng thái AFK")
        return afk_data
    
    def is_afk(self, user_id: int) -> bool:
        """
        Kiểm tra xem user có đang AFK không
        
        Args:
            user_id: ID của user
            
        Returns:
            bool: True nếu user đang AFK
        """
        return user_id in self.afk_users
    
    def get_afk_info(self, user_id: int) -> Optional[dict]:
        """
        Lấy thông tin AFK của user
        
        Args:
            user_id: ID của user
            
        Returns:
            dict: Thông tin AFK (reason, timestamp, guild_id)
        """
        return self.afk_users.get(user_id)
    
    def format_afk_duration(self, timestamp_str: str) -> str:
        """
        Format thời gian AFK thành chuỗi dễ đọc
        
        Args:
            timestamp_str: Timestamp dạng ISO string
            
        Returns:
            str: Thời gian AFK đã format
        """
        try:
            afk_time = datetime.fromisoformat(timestamp_str)
            duration = datetime.now() - afk_time
            
            if duration.days > 0:
                return f"{duration.days} ngày {duration.seconds // 3600} giờ"
            elif duration.seconds >= 3600:
                hours = duration.seconds // 3600
                minutes = (duration.seconds % 3600) // 60
                return f"{hours} giờ {minutes} phút"
            elif duration.seconds >= 60:
                minutes = duration.seconds // 60
                return f"{minutes} phút"
            else:
                return "vài giây"
        except:
            return "không xác định"
    
    async def handle_afk_mention(self, message: discord.Message) -> None:
        """
        Xử lý khi có người mention user AFK
        
        Args:
            message: Message chứa mention
        """
        try:
            if not message.mentions:
                return
            
            afk_mentions = []
            for mentioned_user in message.mentions:
                if self.is_afk(mentioned_user.id):
                    afk_info = self.get_afk_info(mentioned_user.id)
                    if afk_info:
                        duration = self.format_afk_duration(afk_info['timestamp'])
                        afk_mentions.append({
                            'user': mentioned_user,
                            'reason': afk_info['reason'],
                            'duration': duration
                        })
            
            if afk_mentions:
                # Tạo embed thông báo AFK
                embed = discord.Embed(
                    title="💤 Người dùng đang AFK",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                
                for afk_data in afk_mentions:
                    user = afk_data['user']
                    reason = afk_data['reason']
                    duration = afk_data['duration']
                    
                    embed.add_field(
                        name=f"👤 {user.display_name}",
                        value=f"**Lý do:** {reason}\n**Thời gian:** {duration}",
                        inline=False
                    )
                
                embed.set_footer(text="Họ sẽ được thông báo khi quay lại online")
                
                await message.reply(embed=embed, mention_author=False)
                
                logger.info(f"Thông báo AFK cho {len(afk_mentions)} users được mention bởi {message.author}")
                
        except Exception as e:
            logger.error(f"Lỗi khi xử lý AFK mention: {e}")
    
    async def handle_user_return(self, message: discord.Message) -> None:
        """
        Xử lý khi user AFK gửi tin nhắn đầu tiên (quay lại online)
        
        Args:
            message: Message của user
        """
        try:
            user_id = message.author.id
            
            if self.is_afk(user_id):
                afk_info = self.remove_afk(user_id)
                
                if afk_info:
                    duration = self.format_afk_duration(afk_info['timestamp'])
                    
                    embed = discord.Embed(
                        title="🌟 Chào mừng trở lại!",
                        description=f"**{message.author.display_name}** đã quay lại online!",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📝 Lý do AFK trước đó",
                        value=afk_info['reason'],
                        inline=False
                    )
                    
                    embed.add_field(
                        name="⏰ Thời gian AFK",
                        value=duration,
                        inline=False
                    )
                    
                    embed.set_thumbnail(url=message.author.display_avatar.url)
                    embed.set_footer(text="Chúc bạn có một ngày tốt lành!")
                    
                    await message.reply(embed=embed, mention_author=False)
                    
                    logger.info(f"User {message.author} đã quay lại sau {duration} AFK")
                    
        except Exception as e:
            logger.error(f"Lỗi khi xử lý user return: {e}")
    
    async def handle_supreme_admin_mention(self, message: discord.Message) -> None:
        """
        Xử lý khi có người mention Supreme Admin đang AFK
        
        Args:
            message: Message chứa mention Supreme Admin
        """
        try:
            supreme_admin_id = self.bot_instance.supreme_admin_id
            if not supreme_admin_id:
                return
            
            # Kiểm tra xem Supreme Admin có được mention không
            mentioned_ids = [user.id for user in message.mentions]
            if supreme_admin_id not in mentioned_ids:
                return
            
            # Kiểm tra xem Supreme Admin có đang AFK không
            if not self.is_afk(supreme_admin_id):
                return
            
            afk_info = self.get_afk_info(supreme_admin_id)
            if not afk_info:
                return
            
            duration = self.format_afk_duration(afk_info['timestamp'])
            
            # Tạo embed đặc biệt cho Supreme Admin
            embed = discord.Embed(
                title="👑 Supreme Admin đang AFK",
                description="Admin tối cao hiện đang không có mặt",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📝 Lý do AFK",
                value=afk_info['reason'],
                inline=False
            )
            
            embed.add_field(
                name="⏰ Thời gian AFK",
                value=duration,
                inline=False
            )
            
            embed.add_field(
                name="💡 Lưu ý",
                value="Đây là admin tối cao của bot. Vui lòng chờ họ quay lại hoặc liên hệ admin khác.",
                inline=False
            )
            
            embed.set_footer(text="Supreme Admin sẽ được thông báo khi quay lại")
            
            await message.reply(embed=embed, mention_author=False)
            
            logger.info(f"Thông báo Supreme Admin AFK cho mention từ {message.author}")
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý Supreme Admin mention: {e}")
    
    def register_commands(self) -> None:
        """
        Đăng ký các commands AFK
        """
        @self.bot.command(name='afk', help='Đặt trạng thái AFK với lý do')
        async def afk_command(ctx, *, reason: str = "Không có lý do cụ thể"):
            """
            Lệnh đặt trạng thái AFK
            
            Usage: ;afk [lý do]
            """
            try:
                user_id = ctx.author.id
                guild_id = ctx.guild.id if ctx.guild else 0
                
                # Kiểm tra xem user đã AFK chưa
                if self.is_afk(user_id):
                    embed = discord.Embed(
                        title="💤 Bạn đã đang AFK",
                        description="Bạn đã ở trạng thái AFK rồi!",
                        color=discord.Color.orange()
                    )
                    
                    current_afk = self.get_afk_info(user_id)
                    if current_afk:
                        duration = self.format_afk_duration(current_afk['timestamp'])
                        embed.add_field(
                            name="📝 Lý do hiện tại",
                            value=current_afk['reason'],
                            inline=False
                        )
                        embed.add_field(
                            name="⏰ Thời gian AFK",
                            value=duration,
                            inline=False
                        )
                    
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Giới hạn độ dài lý do
                if len(reason) > 200:
                    reason = reason[:200] + "..."
                
                # Đặt trạng thái AFK
                self.set_afk(user_id, reason, guild_id)
                
                # Tạo embed thông báo
                embed = discord.Embed(
                    title="💤 Đã đặt trạng thái AFK",
                    description=f"**{ctx.author.display_name}** đã đặt trạng thái AFK",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📝 Lý do",
                    value=reason,
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Lưu ý",
                    value="Bạn sẽ tự động bỏ AFK khi gửi tin nhắn tiếp theo",
                    inline=False
                )
                
                embed.set_thumbnail(url=ctx.author.display_avatar.url)
                embed.set_footer(text="Chúc bạn nghỉ ngơi tốt!")
                
                await ctx.reply(embed=embed, mention_author=False)
                
                logger.info(f"User {ctx.author} đã đặt AFK với lý do: {reason}")
                
            except Exception as e:
                logger.error(f"Lỗi trong afk command: {e}")
                await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra khi đặt AFK: {str(e)[:100]}", mention_author=True)
        
        @self.bot.command(name='unafk', help='Bỏ trạng thái AFK thủ công')
        async def unafk_command(ctx):
            """
            Lệnh bỏ trạng thái AFK thủ công
            
            Usage: ;unafk
            """
            try:
                user_id = ctx.author.id
                
                if not self.is_afk(user_id):
                    embed = discord.Embed(
                        title="❌ Bạn không đang AFK",
                        description="Bạn hiện không ở trạng thái AFK",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                afk_info = self.remove_afk(user_id)
                
                if afk_info:
                    duration = self.format_afk_duration(afk_info['timestamp'])
                    
                    embed = discord.Embed(
                        title="🌟 Đã bỏ trạng thái AFK",
                        description=f"**{ctx.author.display_name}** đã bỏ trạng thái AFK thủ công",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📝 Lý do AFK trước đó",
                        value=afk_info['reason'],
                        inline=False
                    )
                    
                    embed.add_field(
                        name="⏰ Thời gian AFK",
                        value=duration,
                        inline=False
                    )
                    
                    embed.set_thumbnail(url=ctx.author.display_avatar.url)
                    
                    await ctx.reply(embed=embed, mention_author=False)
                    
                    logger.info(f"User {ctx.author} đã bỏ AFK thủ công sau {duration}")
                
            except Exception as e:
                logger.error(f"Lỗi trong unafk command: {e}")
                await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra khi bỏ AFK: {str(e)[:100]}", mention_author=True)
        
        @self.bot.command(name='afklist', help='Xem danh sách users đang AFK')
        async def afklist_command(ctx):
            """
            Lệnh xem danh sách users đang AFK
            
            Usage: ;afklist
            """
            try:
                if not self.afk_users:
                    embed = discord.Embed(
                        title="💤 Danh sách AFK",
                        description="Hiện tại không có ai đang AFK",
                        color=discord.Color.blue()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                embed = discord.Embed(
                    title="💤 Danh sách users đang AFK",
                    description=f"Có {len(self.afk_users)} người đang AFK",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                
                # Giới hạn hiển thị 10 users để tránh embed quá dài
                count = 0
                for user_id, afk_info in list(self.afk_users.items())[:10]:
                    try:
                        user = self.bot.get_user(user_id)
                        if user:
                            duration = self.format_afk_duration(afk_info['timestamp'])
                            embed.add_field(
                                name=f"👤 {user.display_name}",
                                value=f"**Lý do:** {afk_info['reason'][:50]}{'...' if len(afk_info['reason']) > 50 else ''}\n**Thời gian:** {duration}",
                                inline=False
                            )
                            count += 1
                    except:
                        continue
                
                if len(self.afk_users) > 10:
                    embed.set_footer(text=f"Hiển thị {count}/{len(self.afk_users)} users AFK")
                
                await ctx.reply(embed=embed, mention_author=False)
                
            except Exception as e:
                logger.error(f"Lỗi trong afklist command: {e}")
                await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem danh sách AFK: {str(e)[:100]}", mention_author=True)
        
        logger.info("Đã đăng ký tất cả AFK commands")
