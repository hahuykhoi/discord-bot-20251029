"""
Channel Permission Commands - Quản lý quyền chat trong kênh
"""

import discord
from discord.ext import commands
import json
import os
import logging
from .base import BaseCommand

logger = logging.getLogger(__name__)

class ChannelPermissionCommands(BaseCommand):
    """Commands để quản lý channel permissions"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.permissions_file = 'channel_permissions.json'
        self.permissions_data = self.load_permissions()
    
    def load_permissions(self):
        """Load channel permissions từ file"""
        try:
            if os.path.exists(self.permissions_file):
                with open(self.permissions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load channel permissions: {e}")
            return {}
    
    def save_permissions(self):
        """Save channel permissions vào file"""
        try:
            with open(self.permissions_file, 'w', encoding='utf-8') as f:
                json.dump(self.permissions_data, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu channel permissions")
        except Exception as e:
            logger.error(f"Lỗi khi save channel permissions: {e}")
    
    def is_channel_allowed(self, guild_id: int, channel_id: int, command_name: str = None) -> bool:
        """Kiểm tra xem channel có được phép chat không"""
        guild_key = str(guild_id)
        
        # Nếu server chưa set channel nào thì cho phép tất cả
        if guild_key not in self.permissions_data:
            return True
        
        # Kiểm tra bypass commands trước
        if command_name:
            bypass_commands = self.permissions_data[guild_key].get('bypass_commands', [])
            if command_name in bypass_commands:
                return True  # Command được bypass, cho phép ở mọi kênh
        
        # Nếu có list channels, check xem channel hiện tại có trong list không
        allowed_channels = self.permissions_data[guild_key].get('allowed_channels', [])
        
        # Nếu list rỗng thì cho phép tất cả
        if not allowed_channels:
            return True
        
        return channel_id in allowed_channels
    
    def register_commands(self):
        """Register channel permission commands"""
        
        @self.bot.command(name='setchannel', aliases=['addchannel', 'allowchannel'])
        async def set_channel(ctx, channel: discord.TextChannel = None):
            """
            Thêm kênh vào danh sách được phép chat
            
            Usage: ;setchannel #channel
            Example: ;setchannel #general
            """
            # Kiểm tra quyền admin
            if not ctx.author.guild_permissions.administrator:
                is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
                is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
                
                if not (is_admin or is_supreme):
                    await ctx.reply(
                        "❌ Bạn cần quyền **Administrator** hoặc là **Admin/Supreme Admin** của bot để sử dụng lệnh này!",
                        mention_author=True
                    )
                    return
            
            # Nếu không specify channel thì dùng channel hiện tại
            if channel is None:
                channel = ctx.channel
            
            guild_key = str(ctx.guild.id)
            
            # Khởi tạo data cho server nếu chưa có
            if guild_key not in self.permissions_data:
                self.permissions_data[guild_key] = {'allowed_channels': []}
            
            allowed_channels = self.permissions_data[guild_key].get('allowed_channels', [])
            
            # Kiểm tra xem channel đã được thêm chưa
            if channel.id in allowed_channels:
                await ctx.reply(
                    f"⚠️ Kênh {channel.mention} đã có trong danh sách được phép chat!",
                    mention_author=True
                )
                return
            
            # Thêm channel
            allowed_channels.append(channel.id)
            self.permissions_data[guild_key]['allowed_channels'] = allowed_channels
            self.save_permissions()
            
            embed = discord.Embed(
                title="✅ Đã thêm kênh chat",
                description=f"Kênh {channel.mention} đã được thêm vào danh sách được phép chat!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Tổng kênh được phép",
                value=f"**{len(allowed_channels)} kênh**",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Added channel {channel.id} to allowed list in guild {ctx.guild.id}")
        
        @self.bot.command(name='removechannel', aliases=['delchannel', 'disallowchannel'])
        async def remove_channel(ctx, channel: discord.TextChannel = None):
            """
            Xóa kênh khỏi danh sách được phép chat
            
            Usage: ;removechannel #channel
            Example: ;removechannel #general
            """
            # Kiểm tra quyền admin
            if not ctx.author.guild_permissions.administrator:
                is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
                is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
                
                if not (is_admin or is_supreme):
                    await ctx.reply(
                        "❌ Bạn cần quyền **Administrator** hoặc là **Admin/Supreme Admin** của bot để sử dụng lệnh này!",
                        mention_author=True
                    )
                    return
            
            # Nếu không specify channel thì dùng channel hiện tại
            if channel is None:
                channel = ctx.channel
            
            guild_key = str(ctx.guild.id)
            
            # Kiểm tra xem server có data không
            if guild_key not in self.permissions_data:
                await ctx.reply(
                    "⚠️ Server này chưa có kênh nào trong danh sách!",
                    mention_author=True
                )
                return
            
            allowed_channels = self.permissions_data[guild_key].get('allowed_channels', [])
            
            # Kiểm tra xem channel có trong list không
            if channel.id not in allowed_channels:
                await ctx.reply(
                    f"⚠️ Kênh {channel.mention} không có trong danh sách!",
                    mention_author=True
                )
                return
            
            # Xóa channel
            allowed_channels.remove(channel.id)
            self.permissions_data[guild_key]['allowed_channels'] = allowed_channels
            self.save_permissions()
            
            embed = discord.Embed(
                title="✅ Đã xóa kênh chat",
                description=f"Kênh {channel.mention} đã được xóa khỏi danh sách!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📊 Tổng kênh còn lại",
                value=f"**{len(allowed_channels)} kênh**",
                inline=False
            )
            
            if len(allowed_channels) == 0:
                embed.add_field(
                    name="ℹ️ Thông báo",
                    value="Danh sách trống - Bot sẽ cho phép chat ở mọi kênh!",
                    inline=False
                )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Removed channel {channel.id} from allowed list in guild {ctx.guild.id}")
        
        @self.bot.command(name='listchannels', aliases=['channels', 'allowedchannels'])
        async def list_channels(ctx):
            """
            Xem danh sách các kênh được phép chat
            
            Usage: ;listchannels
            """
            guild_key = str(ctx.guild.id)
            
            embed = discord.Embed(
                title="📋 Danh sách kênh được phép chat",
                color=discord.Color.blue()
            )
            
            # Kiểm tra xem server có data không
            if guild_key not in self.permissions_data or not self.permissions_data[guild_key].get('allowed_channels'):
                embed.description = "✅ **Tất cả các kênh đều được phép chat!**"
                embed.add_field(
                    name="ℹ️ Hướng dẫn",
                    value=(
                        "Để giới hạn chat trong kênh cụ thể:\n"
                        "; #channel` - Thêm kênh\n"
                        "; #channel` - Xóa kênh"
                    ),
                    inline=False
                )
            else:
                allowed_channels = self.permissions_data[guild_key]['allowed_channels']
                
                # Lấy thông tin các channels
                channel_list = []
                for channel_id in allowed_channels:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        channel_list.append(f"• {channel.mention} (ID: `{channel_id}`)")
                    else:
                        channel_list.append(f"• ~~Kênh đã bị xóa~~ (ID: `{channel_id}`)")
                
                embed.description = f"**{len(allowed_channels)} kênh được phép:**\n" + "\n".join(channel_list)
                
                embed.add_field(
                    name="⚠️ Lưu ý",
                    value="Bot chỉ hoạt động trong các kênh được liệt kê ở trên!",
                    inline=False
                )
            
            embed.set_footer(text=f"Server: {ctx.guild.name}")
            
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='resetchannels', aliases=['clearallchannels'])
        async def reset_channels(ctx):
            """
            Reset danh sách kênh - cho phép chat ở mọi kênh
            
            Usage: ;resetchannels
            """
            # Kiểm tra quyền admin
            if not ctx.author.guild_permissions.administrator:
                is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
                is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
                
                if not (is_admin or is_supreme):
                    await ctx.reply(
                        "❌ Bạn cần quyền **Administrator** hoặc là **Admin/Supreme Admin** của bot để sử dụng lệnh này!",
                        mention_author=True
                    )
                    return
            
            guild_key = str(ctx.guild.id)
            
            # Reset data
            if guild_key in self.permissions_data:
                del self.permissions_data[guild_key]
                self.save_permissions()
            
            embed = discord.Embed(
                title="✅ Đã reset danh sách kênh",
                description="Bot giờ có thể hoạt động ở **tất cả các kênh**!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="ℹ️ Thông báo",
                value="Sử dụng ;` để giới hạn kênh chat lại.",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Reset channel permissions for guild {ctx.guild.id}")
        
        @self.bot.command(name='allowcommand', aliases=['bypasscmd', 'allowcmd'])
        async def allow_command(ctx, command_name: str):
            """
            Cho phép lệnh hoạt động ở mọi kênh (kể cả kênh bị cấm)
            
            Usage: ;allowcommand <tên lệnh>
            Example: ;allowcommand help
            """
            # Kiểm tra quyền admin
            if not ctx.author.guild_permissions.administrator:
                is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
                is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
                
                if not (is_admin or is_supreme):
                    await ctx.reply(
                        "❌ Bạn cần quyền **Administrator** hoặc là **Admin/Supreme Admin** của bot để sử dụng lệnh này!",
                        mention_author=True
                    )
                    return
            
            guild_key = str(ctx.guild.id)
            
            # Khởi tạo data cho server nếu chưa có
            if guild_key not in self.permissions_data:
                self.permissions_data[guild_key] = {'allowed_channels': [], 'bypass_commands': []}
            
            if 'bypass_commands' not in self.permissions_data[guild_key]:
                self.permissions_data[guild_key]['bypass_commands'] = []
            
            bypass_commands = self.permissions_data[guild_key]['bypass_commands']
            
            # Kiểm tra lệnh đã được bypass chưa
            if command_name in bypass_commands:
                await ctx.reply(
                    f"⚠️ Lệnh `{command_name}` đã có thể dùng ở mọi kênh!",
                    mention_author=True
                )
                return
            
            # Thêm command vào bypass list
            bypass_commands.append(command_name)
            self.permissions_data[guild_key]['bypass_commands'] = bypass_commands
            self.save_permissions()
            
            embed = discord.Embed(
                title="✅ Đã cho phép lệnh bypass",
                description=f"Lệnh `;{command_name}` giờ có thể dùng ở **mọi kênh**!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Tổng lệnh bypass",
                value=f"**{len(bypass_commands)} lệnh**",
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Lưu ý",
                value="Lệnh này sẽ hoạt động ngay cả ở kênh bot bị cấm.",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Added bypass command '{command_name}' in guild {ctx.guild.id}")
        
        @self.bot.command(name='disallowcommand', aliases=['removebypass', 'removecmd'])
        async def disallow_command(ctx, command_name: str):
            """
            Xóa lệnh khỏi danh sách bypass
            
            Usage: ;disallowcommand <tên lệnh>
            Example: ;disallowcommand help
            """
            # Kiểm tra quyền admin
            if not ctx.author.guild_permissions.administrator:
                is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
                is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
                
                if not (is_admin or is_supreme):
                    await ctx.reply(
                        "❌ Bạn cần quyền **Administrator** hoặc là **Admin/Supreme Admin** của bot để sử dụng lệnh này!",
                        mention_author=True
                    )
                    return
            
            guild_key = str(ctx.guild.id)
            
            # Kiểm tra xem server có data không
            if guild_key not in self.permissions_data or 'bypass_commands' not in self.permissions_data[guild_key]:
                await ctx.reply(
                    "⚠️ Server này chưa có lệnh bypass nào!",
                    mention_author=True
                )
                return
            
            bypass_commands = self.permissions_data[guild_key]['bypass_commands']
            
            # Kiểm tra lệnh có trong list không
            if command_name not in bypass_commands:
                await ctx.reply(
                    f"⚠️ Lệnh `{command_name}` không có trong danh sách bypass!",
                    mention_author=True
                )
                return
            
            # Xóa command
            bypass_commands.remove(command_name)
            self.permissions_data[guild_key]['bypass_commands'] = bypass_commands
            self.save_permissions()
            
            embed = discord.Embed(
                title="✅ Đã xóa lệnh bypass",
                description=f"Lệnh `;{command_name}` đã bị xóa khỏi danh sách bypass!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📊 Tổng lệnh còn lại",
                value=f"**{len(bypass_commands)} lệnh**",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Removed bypass command '{command_name}' in guild {ctx.guild.id}")
        
        @self.bot.command(name='listbypass', aliases=['bypasslist', 'listallowed'])
        async def list_bypass(ctx):
            """
            Xem danh sách lệnh có thể dùng ở mọi kênh
            
            Usage: ;listbypass
            """
            guild_key = str(ctx.guild.id)
            
            embed = discord.Embed(
                title="📋 Danh sách lệnh bypass",
                color=discord.Color.blue()
            )
            
            # Kiểm tra xem server có data không
            if guild_key not in self.permissions_data or 'bypass_commands' not in self.permissions_data[guild_key] or not self.permissions_data[guild_key]['bypass_commands']:
                embed.description = "❌ **Chưa có lệnh bypass nào!**"
                embed.add_field(
                    name="ℹ️ Hướng dẫn",
                    value=(
                        "Để cho phép lệnh hoạt động ở mọi kênh:\n"
                        "; <tên lệnh>` - Thêm lệnh bypass\n"
                        "; <tên lệnh>` - Xóa lệnh bypass"
                    ),
                    inline=False
                )
            else:
                bypass_commands = self.permissions_data[guild_key]['bypass_commands']
                
                # Format danh sách commands
                cmd_list = [f"• `;{cmd}`" for cmd in bypass_commands]
                
                embed.description = f"**{len(bypass_commands)} lệnh có thể dùng ở mọi kênh:**\n" + "\n".join(cmd_list)
                
                embed.add_field(
                    name="✅ Lợi ích",
                    value="Các lệnh này hoạt động ngay cả khi bot bị cấm trong kênh!",
                    inline=False
                )
            
            embed.set_footer(text=f"Server: {ctx.guild.name}")
            
            await ctx.reply(embed=embed, mention_author=True)
