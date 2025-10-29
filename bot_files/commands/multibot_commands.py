import discord
from discord.ext import commands
import json
import os
import asyncio
import aiohttp
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MultiBotCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.tokens_file = 'tokens/bot_config.json'
        self.bot_configs = {}
        self.load_bot_configs()
        self.setup_commands()
    
    def load_bot_configs(self):
        """Load bot configurations from file"""
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bot_configs = data.get('bots', {})
                    self.settings = data.get('settings', {})
                logger.info(f"Loaded {len(self.bot_configs)} bot configurations")
            else:
                logger.warning("Bot config file not found, creating default")
                self.create_default_config()
        except Exception as e:
            logger.error(f"Error loading bot configs: {e}")
            self.bot_configs = {}
            self.settings = {}
    
    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "bots": {},
            "settings": {
                "max_concurrent_bots": 5,
                "message_delay": 1.0,
                "retry_attempts": 3,
                "timeout": 30
            },
            "last_updated": datetime.now().isoformat()
        }
        
        os.makedirs('tokens', exist_ok=True)
        with open(self.tokens_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
    
    def save_bot_configs(self):
        """Save bot configurations to file"""
        try:
            data = {
                "bots": self.bot_configs,
                "settings": self.settings,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.tokens_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info("Bot configurations saved successfully")
        except Exception as e:
            logger.error(f"Error saving bot configs: {e}")
    
    async def send_message_via_bot(self, token, channel_id, content):
        """Send message using specific bot token"""
        try:
            headers = {
                'Authorization': f'Bot {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'content': content
            }
            
            async with aiohttp.ClientSession() as session:
                url = f'https://discord.com/api/v10/channels/{channel_id}/messages'
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return True, "Success"
                    else:
                        error_text = await response.text()
                        return False, f"HTTP {response.status}: {error_text}"
        
        except Exception as e:
            return False, str(e)
    
    async def send_dm_via_bot(self, token, user_id, content):
        """Send DM using specific bot token"""
        try:
            headers = {
                'Authorization': f'Bot {token}',
                'Content-Type': 'application/json'
            }
            
            # First create DM channel
            dm_payload = {
                'recipient_id': user_id
            }
            
            async with aiohttp.ClientSession() as session:
                # Create DM channel
                dm_url = 'https://discord.com/api/v10/users/@me/channels'
                async with session.post(dm_url, headers=headers, json=dm_payload) as dm_response:
                    if dm_response.status != 200:
                        error_text = await dm_response.text()
                        return False, f"Failed to create DM: HTTP {dm_response.status}: {error_text}"
                    
                    dm_data = await dm_response.json()
                    dm_channel_id = dm_data['id']
                
                # Send message to DM channel
                message_payload = {
                    'content': content
                }
                
                message_url = f'https://discord.com/api/v10/channels/{dm_channel_id}/messages'
                async with session.post(message_url, headers=headers, json=message_payload) as message_response:
                    if message_response.status == 200:
                        return True, "Success"
                    else:
                        error_text = await message_response.text()
                        return False, f"HTTP {message_response.status}: {error_text}"
        
        except Exception as e:
            return False, str(e)
    
    async def change_bot_nickname(self, token, guild_id, nickname):
        """Change bot nickname using specific bot token"""
        try:
            headers = {
                'Authorization': f'Bot {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'nick': nickname
            }
            
            async with aiohttp.ClientSession() as session:
                url = f'https://discord.com/api/v10/guilds/{guild_id}/members/@me'
                async with session.patch(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return True, "Success"
                    else:
                        error_text = await response.text()
                        return False, f"HTTP {response.status}: {error_text}"
        
        except Exception as e:
            return False, str(e)
    
    def setup_commands(self):
        """Setup multi-bot commands"""
        
        @self.bot.command(name='multibot')
        async def multibot_command(ctx, action=None, *args):
            """
            Multi-bot management system
            
            Usage:
            ;multibot list - Xem danh sách bot
            ;multibot add <name> <token> [description] - Thêm bot mới
            ;multibot remove <name> - Xóa bot
            ;multibot toggle <name> - Bật/tắt bot
            ;multibot send <bot_name> <channel_id> <message> - Gửi tin nhắn
            ;multibot broadcast <channel_id> <message> - Gửi qua tất cả bot active
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin mới có thể sử dụng Multi-Bot system!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not action:
                await self.show_help(ctx)
                return
            
            if action == 'list':
                await self.list_bots(ctx)
            elif action == 'add':
                await self.add_bot(ctx, args)
            elif action == 'remove':
                await self.remove_bot(ctx, args)
            elif action == 'toggle':
                await self.toggle_bot(ctx, args)
            elif action == 'send':
                await self.send_message(ctx, args)
            elif action == 'broadcast':
                await self.broadcast_message(ctx, args)
            else:
                await self.show_help(ctx)
        
        @self.bot.command(name='sendall')
        async def sendall_command(ctx, channel_id=None, count=None, *, message=None):
            """
            Gửi tin nhắn qua số lượng bot tùy chọn
            
            Usage: ;sendall <channel_id> [count] <message>
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin mới có thể sử dụng lệnh sendall!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Parse arguments
            if not channel_id:
                embed = discord.Embed(
                    title="❌ Thiếu tham số",
                    description="Cần ít nhất channel ID và tin nhắn!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value=(
                        "`;sendall <channel_id> <message>` - Gửi qua tất cả bot\n"
                        "`;sendall <channel_id> <số> <message>` - Gửi qua số bot cụ thể"
                    ),
                    inline=False
                )
                embed.add_field(
                    name="📝 Ví dụ",
                    value=(
                        "`;sendall 123456789 Hello everyone!`\n"
                        "`;sendall 123456789 3 Hello from 3 bots!`"
                    ),
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Check if count is provided
            bot_count = None
            if count and count.isdigit():
                bot_count = int(count)
                if bot_count < 1:
                    embed = discord.Embed(
                        title="❌ Số lượng không hợp lệ",
                        description="Số lượng bot phải lớn hơn 0!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
            elif count and not count.isdigit():
                # count is actually part of message
                message = f"{count} {message}" if message else count
                bot_count = None
            
            if not message:
                embed = discord.Embed(
                    title="❌ Thiếu tin nhắn",
                    description="Vui lòng nhập nội dung tin nhắn!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            try:
                channel_id_int = int(channel_id)
            except ValueError:
                embed = discord.Embed(
                    title="❌ Channel ID không hợp lệ",
                    description="Channel ID phải là số!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Call custom broadcast with count
            await self.broadcast_with_count(ctx, channel_id_int, message, bot_count)
        
        @self.bot.command(name='dmall')
        async def dmall_command(ctx, user_id=None, count=None, *, message=None):
            """
            Gửi DM qua số lượng bot tùy chọn
            
            Usage: ;dmall <user_id> [count] <message>
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin mới có thể sử dụng lệnh dmall!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Parse arguments
            if not user_id:
                embed = discord.Embed(
                    title="❌ Thiếu tham số",
                    description="Cần ít nhất user ID và tin nhắn!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value=(
                        "`;dmall <user_id> <message>` - DM qua tất cả bot\n"
                        "`;dmall <user_id> <số> <message>` - DM qua số bot cụ thể\n"
                        "`;dmall @user <message>` - DM qua mention"
                    ),
                    inline=False
                )
                embed.add_field(
                    name="📝 Ví dụ",
                    value=(
                        "`;dmall 123456789 Hello!`\n"
                        "`;dmall @user 2 Hello from 2 bots!`"
                    ),
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Handle mention
            if user_id.startswith('<@') and user_id.endswith('>'):
                user_id = user_id[2:-1]
                if user_id.startswith('!'):
                    user_id = user_id[1:]
            
            # Check if count is provided
            bot_count = None
            if count and count.isdigit():
                bot_count = int(count)
                if bot_count < 1:
                    embed = discord.Embed(
                        title="❌ Số lượng không hợp lệ",
                        description="Số lượng bot phải lớn hơn 0!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
            elif count and not count.isdigit():
                # count is actually part of message
                message = f"{count} {message}" if message else count
                bot_count = None
            
            if not message:
                embed = discord.Embed(
                    title="❌ Thiếu tin nhắn",
                    description="Vui lòng nhập nội dung tin nhắn!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            try:
                user_id_int = int(user_id)
            except ValueError:
                embed = discord.Embed(
                    title="❌ User ID không hợp lệ",
                    description="User ID phải là số!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Call DM broadcast
            await self.dm_broadcast_with_count(ctx, user_id_int, message, bot_count)
        
        @self.bot.command(name='setupbot')
        async def setupbot_command(ctx, *, nickname=None):
            """
            Đổi tên tất cả bot thành một tên
            
            Usage: ;setupbot <nickname>
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin mới có thể sử dụng lệnh setupbot!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not nickname:
                embed = discord.Embed(
                    title="❌ Thiếu tên bot",
                    description="Vui lòng nhập tên mới cho tất cả bot!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Cách sử dụng",
                    value="`;setupbot <tên_mới>`",
                    inline=False
                )
                embed.add_field(
                    name="📝 Ví dụ",
                    value="`;setupbot Helper Bot`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if len(nickname) > 32:
                embed = discord.Embed(
                    title="❌ Tên quá dài",
                    description="Tên bot không được vượt quá 32 ký tự!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Lấy danh sách bot active
            active_bots = {name: config for name, config in self.bot_configs.items() 
                          if config.get('active', False)}
            
            if not active_bots:
                embed = discord.Embed(
                    title="⚠️ Không có bot active",
                    description="Không có bot nào được kích hoạt để đổi tên!",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 Giải pháp",
                    value="Sử dụng `;multibot toggle <name>` để kích hoạt bot",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Hiển thị progress
            progress_embed = discord.Embed(
                title="🤖 Đang đổi tên bot...",
                description=f"Đổi tên {len(active_bots)} bot thành: **{nickname}**",
                color=discord.Color.yellow()
            )
            progress_msg = await ctx.reply(embed=progress_embed, mention_author=True)
            
            # Đổi tên tất cả bot
            results = {}
            delay = self.settings.get('message_delay', 1.0)
            guild_id = ctx.guild.id
            
            for bot_name, config in active_bots.items():
                token = config['token']
                success, result = await self.change_bot_nickname(token, guild_id, nickname)
                results[bot_name] = {'success': success, 'result': result}
                
                # Delay giữa các bot để tránh rate limit
                await asyncio.sleep(delay)
            
            # Hiển thị kết quả
            success_count = sum(1 for r in results.values() if r['success'])
            fail_count = len(results) - success_count
            
            if success_count > 0:
                embed = discord.Embed(
                    title="🤖 Đổi tên bot hoàn tất",
                    description=f"Đã đổi tên {success_count}/{len(active_bots)} bot thành: **{nickname}**",
                    color=discord.Color.green() if fail_count == 0 else discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title="❌ Đổi tên thất bại",
                    description="Không thể đổi tên bot nào!",
                    color=discord.Color.red()
                )
            
            # Chi tiết kết quả
            success_bots = [name for name, r in results.items() if r['success']]
            fail_bots = [name for name, r in results.items() if not r['success']]
            
            if success_bots:
                embed.add_field(
                    name="✅ Thành công",
                    value=', '.join(success_bots),
                    inline=False
                )
            
            if fail_bots:
                embed.add_field(
                    name="❌ Thất bại",
                    value=', '.join(fail_bots),
                    inline=False
                )
                
                # Hiển thị lý do thất bại đầu tiên
                first_fail = next((r['result'] for r in results.values() if not r['success']), None)
                if first_fail:
                    embed.add_field(
                        name="🔍 Lý do thất bại",
                        value=first_fail[:200] + "..." if len(first_fail) > 200 else first_fail,
                        inline=False
                    )
            
            embed.add_field(
                name="📝 Tên mới",
                value=f"**{nickname}**",
                inline=False
            )
            
            embed.set_footer(text="Lưu ý: Bot cần quyền 'Change Nickname' để đổi tên")
            
            await progress_msg.edit(embed=embed)
            logger.info(f"Admin {ctx.author} changed {success_count}/{len(active_bots)} bot nicknames to: {nickname}")
    
    async def broadcast_with_count(self, ctx, channel_id, message, bot_count=None):
        """Broadcast message with custom bot count"""
        # Lấy danh sách bot active
        active_bots = {name: config for name, config in self.bot_configs.items() 
                      if config.get('active', False)}
        
        if not active_bots:
            embed = discord.Embed(
                title="⚠️ Không có bot active",
                description="Không có bot nào được kích hoạt để gửi tin nhắn!",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="💡 Giải pháp",
                value="Sử dụng `;multibot toggle <name>` để kích hoạt bot",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Giới hạn số lượng bot nếu được chỉ định
        if bot_count:
            if bot_count > len(active_bots):
                embed = discord.Embed(
                    title="⚠️ Số lượng vượt quá",
                    description=f"Chỉ có {len(active_bots)} bot active, không thể gửi qua {bot_count} bot!",
                    color=discord.Color.orange()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Lấy số lượng bot đầu tiên
            active_bots = dict(list(active_bots.items())[:bot_count])
        
        # Hiển thị progress
        progress_embed = discord.Embed(
            title="📡 Đang gửi tin nhắn...",
            description=f"Gửi tin nhắn qua {len(active_bots)} bot",
            color=discord.Color.yellow()
        )
        progress_msg = await ctx.reply(embed=progress_embed, mention_author=True)
        
        # Gửi tin nhắn qua các bot
        results = {}
        delay = self.settings.get('message_delay', 1.0)
        
        for bot_name, config in active_bots.items():
            token = config['token']
            success, result = await self.send_message_via_bot(token, channel_id, message)
            results[bot_name] = {'success': success, 'result': result}
            
            # Delay giữa các bot để tránh rate limit
            await asyncio.sleep(delay)
        
        # Hiển thị kết quả
        success_count = sum(1 for r in results.values() if r['success'])
        fail_count = len(results) - success_count
        
        if success_count > 0:
            embed = discord.Embed(
                title="📡 Gửi tin nhắn hoàn tất",
                description=f"Đã gửi tin nhắn qua {success_count}/{len(active_bots)} bot",
                color=discord.Color.green() if fail_count == 0 else discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Gửi tin nhắn thất bại",
                description="Không thể gửi tin nhắn qua bot nào!",
                color=discord.Color.red()
            )
        
        # Chi tiết kết quả
        success_bots = [name for name, r in results.items() if r['success']]
        fail_bots = [name for name, r in results.items() if not r['success']]
        
        if success_bots:
            embed.add_field(
                name="✅ Thành công",
                value=', '.join(success_bots),
                inline=False
            )
        
        if fail_bots:
            embed.add_field(
                name="❌ Thất bại",
                value=', '.join(fail_bots),
                inline=False
            )
        
        embed.add_field(
            name="📝 Nội dung",
            value=message[:200] + "..." if len(message) > 200 else message,
            inline=False
        )
        
        embed.add_field(
            name="📍 Kênh",
            value=f"<#{channel_id}>",
            inline=True
        )
        
        if bot_count:
            embed.add_field(
                name="🤖 Số bot",
                value=f"{len(active_bots)} bot",
                inline=True
            )
        
        await progress_msg.edit(embed=embed)
        logger.info(f"Admin {ctx.author} sent message via {success_count}/{len(active_bots)} bots")
    
    async def dm_broadcast_with_count(self, ctx, user_id, message, bot_count=None):
        """Broadcast DM with custom bot count"""
        # Lấy danh sách bot active
        active_bots = {name: config for name, config in self.bot_configs.items() 
                      if config.get('active', False)}
        
        if not active_bots:
            embed = discord.Embed(
                title="⚠️ Không có bot active",
                description="Không có bot nào được kích hoạt để gửi DM!",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="💡 Giải pháp",
                value="Sử dụng `;multibot toggle <name>` để kích hoạt bot",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Giới hạn số lượng bot nếu được chỉ định
        if bot_count:
            if bot_count > len(active_bots):
                embed = discord.Embed(
                    title="⚠️ Số lượng vượt quá",
                    description=f"Chỉ có {len(active_bots)} bot active, không thể gửi qua {bot_count} bot!",
                    color=discord.Color.orange()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Lấy số lượng bot đầu tiên
            active_bots = dict(list(active_bots.items())[:bot_count])
        
        # Hiển thị progress
        progress_embed = discord.Embed(
            title="💬 Đang gửi DM...",
            description=f"Gửi DM qua {len(active_bots)} bot",
            color=discord.Color.yellow()
        )
        progress_msg = await ctx.reply(embed=progress_embed, mention_author=True)
        
        # Gửi DM qua các bot
        results = {}
        delay = self.settings.get('message_delay', 1.0)
        
        for bot_name, config in active_bots.items():
            token = config['token']
            success, result = await self.send_dm_via_bot(token, user_id, message)
            results[bot_name] = {'success': success, 'result': result}
            
            # Delay giữa các bot để tránh rate limit
            await asyncio.sleep(delay)
        
        # Hiển thị kết quả
        success_count = sum(1 for r in results.values() if r['success'])
        fail_count = len(results) - success_count
        
        if success_count > 0:
            embed = discord.Embed(
                title="💬 Gửi DM hoàn tất",
                description=f"Đã gửi DM qua {success_count}/{len(active_bots)} bot",
                color=discord.Color.green() if fail_count == 0 else discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Gửi DM thất bại",
                description="Không thể gửi DM qua bot nào!",
                color=discord.Color.red()
            )
        
        # Chi tiết kết quả
        success_bots = [name for name, r in results.items() if r['success']]
        fail_bots = [name for name, r in results.items() if not r['success']]
        
        if success_bots:
            embed.add_field(
                name="✅ Thành công",
                value=', '.join(success_bots),
                inline=False
            )
        
        if fail_bots:
            embed.add_field(
                name="❌ Thất bại",
                value=', '.join(fail_bots),
                inline=False
            )
            
            # Hiển thị lý do thất bại đầu tiên
            first_fail = next((r['result'] for r in results.values() if not r['success']), None)
            if first_fail:
                embed.add_field(
                    name="🔍 Lý do thất bại",
                    value=first_fail[:200] + "..." if len(first_fail) > 200 else first_fail,
                    inline=False
                )
        
        embed.add_field(
            name="📝 Nội dung",
            value=message[:200] + "..." if len(message) > 200 else message,
            inline=False
        )
        
        embed.add_field(
            name="👤 Người nhận",
            value=f"<@{user_id}>",
            inline=True
        )
        
        if bot_count:
            embed.add_field(
                name="🤖 Số bot",
                value=f"{len(active_bots)} bot",
                inline=True
            )
        
        embed.set_footer(text="Lưu ý: User phải cho phép DM từ server members")
        
        await progress_msg.edit(embed=embed)
        logger.info(f"Admin {ctx.author} sent DM via {success_count}/{len(active_bots)} bots to user {user_id}")
    
    async def show_help(self, ctx):
        """Show help menu"""
        embed = discord.Embed(
            title="🤖 Multi-Bot System",
            description="Quản lý và sử dụng nhiều bot Discord",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Quản lý Bot",
            value=(
                "`;multibot list` - Xem danh sách bot\n"
                "`;multibot add <name> <token> [mô tả]` - Thêm bot\n"
                "`;multibot remove <name>` - Xóa bot\n"
                "`;multibot toggle <name>` - Bật/tắt bot"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💬 Gửi tin nhắn",
            value=(
                "`;sendall <channel_id> [số] <message>` - Gửi qua số bot tùy chọn\n"
                "`;dmall <user_id> [số] <message>` - DM qua số bot tùy chọn\n"
                "`;multibot send <bot> <channel_id> <message>` - Gửi qua 1 bot"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎭 Quản lý tên bot",
            value=(
                "`;setupbot <tên_mới>` - Đổi tên tất cả bot active"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Lưu ý",
            value="• Chỉ Admin mới có quyền sử dụng\n• Token được lưu trữ an toàn\n• Bot phải có quyền gửi tin nhắn",
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def list_bots(self, ctx):
        """List all configured bots"""
        if not self.bot_configs:
            embed = discord.Embed(
                title="📝 Danh sách Bot trống",
                description="Chưa có bot nào được cấu hình. Sử dụng `;multibot add` để thêm bot.",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        embed = discord.Embed(
            title="🤖 Danh sách Multi-Bot",
            description=f"Tổng cộng: {len(self.bot_configs)} bot",
            color=discord.Color.green()
        )
        
        for bot_name, config in self.bot_configs.items():
            status = "🟢 Active" if config.get('active', False) else "🔴 Inactive"
            embed.add_field(
                name=f"{config.get('name', bot_name)}",
                value=(
                    f"**Status:** {status}\n"
                    f"**ID:** {bot_name}\n"
                    f"**Mô tả:** {config.get('description', 'Không có mô tả')}"
                ),
                inline=True
            )
        
        embed.set_footer(text="Sử dụng ;multibot toggle <name> để bật/tắt bot")
        await ctx.reply(embed=embed, mention_author=True)
    
    async def add_bot(self, ctx, args):
        """Add new bot configuration"""
        if len(args) < 2:
            embed = discord.Embed(
                title="❌ Thiếu tham số",
                description="Cần ít nhất tên bot và token!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;multibot add <name> <token> [mô tả]`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        bot_name = args[0]
        token = args[1]
        description = ' '.join(args[2:]) if len(args) > 2 else "Không có mô tả"
        
        # Xóa tin nhắn chứa token để bảo mật
        try:
            await ctx.message.delete()
        except:
            pass
        
        if bot_name in self.bot_configs:
            embed = discord.Embed(
                title="⚠️ Bot đã tồn tại",
                description=f"Bot '{bot_name}' đã được cấu hình trước đó!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Thêm bot mới
        self.bot_configs[bot_name] = {
            'name': bot_name.title(),
            'token': token,
            'description': description,
            'active': False,
            'added_by': ctx.author.id,
            'added_at': datetime.now().isoformat()
        }
        
        self.save_bot_configs()
        
        embed = discord.Embed(
            title="✅ Thêm bot thành công",
            description=f"Bot '{bot_name}' đã được thêm vào hệ thống!",
            color=discord.Color.green()
        )
        embed.add_field(name="Tên", value=bot_name.title(), inline=True)
        embed.add_field(name="Mô tả", value=description, inline=True)
        embed.add_field(name="Trạng thái", value="🔴 Inactive (mặc định)", inline=True)
        embed.set_footer(text="Sử dụng ;multibot toggle để kích hoạt bot")
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} added new bot: {bot_name}")
    
    async def remove_bot(self, ctx, args):
        """Remove bot configuration"""
        if not args:
            embed = discord.Embed(
                title="❌ Thiếu tên bot",
                description="Vui lòng nhập tên bot cần xóa!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;multibot remove <name>`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        bot_name = args[0]
        
        if bot_name not in self.bot_configs:
            embed = discord.Embed(
                title="❌ Bot không tồn tại",
                description=f"Không tìm thấy bot '{bot_name}'!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Xóa bot
        removed_bot = self.bot_configs.pop(bot_name)
        self.save_bot_configs()
        
        embed = discord.Embed(
            title="✅ Xóa bot thành công",
            description=f"Bot '{bot_name}' đã được xóa khỏi hệ thống!",
            color=discord.Color.green()
        )
        embed.add_field(name="Bot đã xóa", value=removed_bot.get('name', bot_name), inline=True)
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} removed bot: {bot_name}")
    
    async def toggle_bot(self, ctx, args):
        """Toggle bot active status"""
        if not args:
            embed = discord.Embed(
                title="❌ Thiếu tên bot",
                description="Vui lòng nhập tên bot cần bật/tắt!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        bot_name = args[0]
        
        if bot_name not in self.bot_configs:
            embed = discord.Embed(
                title="❌ Bot không tồn tại",
                description=f"Không tìm thấy bot '{bot_name}'!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Toggle status
        current_status = self.bot_configs[bot_name].get('active', False)
        new_status = not current_status
        self.bot_configs[bot_name]['active'] = new_status
        self.save_bot_configs()
        
        status_text = "🟢 Active" if new_status else "🔴 Inactive"
        action_text = "kích hoạt" if new_status else "tắt"
        
        embed = discord.Embed(
            title=f"✅ Đã {action_text} bot",
            description=f"Bot '{bot_name}' hiện tại: {status_text}",
            color=discord.Color.green() if new_status else discord.Color.red()
        )
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} toggled bot {bot_name}: {new_status}")
    
    async def send_message(self, ctx, args):
        """Send message via specific bot"""
        if len(args) < 3:
            embed = discord.Embed(
                title="❌ Thiếu tham số",
                description="Cần đủ: tên bot, channel ID và nội dung tin nhắn!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;multibot send <bot_name> <channel_id> <message>`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        bot_name = args[0]
        try:
            channel_id = int(args[1])
        except ValueError:
            embed = discord.Embed(
                title="❌ Channel ID không hợp lệ",
                description="Channel ID phải là số!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        message = ' '.join(args[2:])
        
        if bot_name not in self.bot_configs:
            embed = discord.Embed(
                title="❌ Bot không tồn tại",
                description=f"Không tìm thấy bot '{bot_name}'!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        if not self.bot_configs[bot_name].get('active', False):
            embed = discord.Embed(
                title="⚠️ Bot chưa kích hoạt",
                description=f"Bot '{bot_name}' chưa được kích hoạt!",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="💡 Giải pháp",
                value=f"Sử dụng `;multibot toggle {bot_name}` để kích hoạt",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Gửi tin nhắn
        token = self.bot_configs[bot_name]['token']
        success, result = await self.send_message_via_bot(token, channel_id, message)
        
        if success:
            embed = discord.Embed(
                title="✅ Gửi tin nhắn thành công",
                description=f"Đã gửi tin nhắn qua bot '{bot_name}'",
                color=discord.Color.green()
            )
            embed.add_field(name="Bot", value=bot_name, inline=True)
            embed.add_field(name="Channel", value=f"<#{channel_id}>", inline=True)
            embed.add_field(name="Nội dung", value=message[:100] + "..." if len(message) > 100 else message, inline=False)
        else:
            embed = discord.Embed(
                title="❌ Gửi tin nhắn thất bại",
                description=f"Không thể gửi tin nhắn qua bot '{bot_name}'",
                color=discord.Color.red()
            )
            embed.add_field(name="Lỗi", value=result, inline=False)
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} sent message via {bot_name}: {success}")
    
    async def broadcast_message(self, ctx, args):
        """Broadcast message via all active bots"""
        if len(args) < 2:
            embed = discord.Embed(
                title="❌ Thiếu tham số",
                description="Cần channel ID và nội dung tin nhắn!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;multibot broadcast <channel_id> <message>`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        try:
            channel_id = int(args[0])
        except ValueError:
            embed = discord.Embed(
                title="❌ Channel ID không hợp lệ",
                description="Channel ID phải là số!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        message = ' '.join(args[1:])
        
        # Lấy danh sách bot active
        active_bots = {name: config for name, config in self.bot_configs.items() 
                      if config.get('active', False)}
        
        if not active_bots:
            embed = discord.Embed(
                title="⚠️ Không có bot active",
                description="Không có bot nào được kích hoạt để gửi tin nhắn!",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="💡 Giải pháp",
                value="Sử dụng `;multibot toggle <name>` để kích hoạt bot",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Hiển thị progress
        progress_embed = discord.Embed(
            title="📡 Đang broadcast...",
            description=f"Gửi tin nhắn qua {len(active_bots)} bot active",
            color=discord.Color.yellow()
        )
        progress_msg = await ctx.reply(embed=progress_embed, mention_author=True)
        
        # Gửi tin nhắn qua tất cả bot
        results = {}
        delay = self.settings.get('message_delay', 1.0)
        
        for bot_name, config in active_bots.items():
            token = config['token']
            success, result = await self.send_message_via_bot(token, channel_id, message)
            results[bot_name] = {'success': success, 'result': result}
            
            # Delay giữa các bot để tránh rate limit
            await asyncio.sleep(delay)
        
        # Hiển thị kết quả
        success_count = sum(1 for r in results.values() if r['success'])
        fail_count = len(results) - success_count
        
        if success_count > 0:
            embed = discord.Embed(
                title="📡 Broadcast hoàn tất",
                description=f"Đã gửi tin nhắn qua {success_count}/{len(active_bots)} bot",
                color=discord.Color.green() if fail_count == 0 else discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Broadcast thất bại",
                description="Không thể gửi tin nhắn qua bot nào!",
                color=discord.Color.red()
            )
        
        # Chi tiết kết quả
        success_bots = [name for name, r in results.items() if r['success']]
        fail_bots = [name for name, r in results.items() if not r['success']]
        
        if success_bots:
            embed.add_field(
                name="✅ Thành công",
                value=', '.join(success_bots),
                inline=False
            )
        
        if fail_bots:
            embed.add_field(
                name="❌ Thất bại",
                value=', '.join(fail_bots),
                inline=False
            )
        
        embed.add_field(
            name="📝 Nội dung",
            value=message[:200] + "..." if len(message) > 200 else message,
            inline=False
        )
        
        await progress_msg.edit(embed=embed)
        logger.info(f"Admin {ctx.author} broadcast message: {success_count}/{len(active_bots)} success")
    
    def register_commands(self):
        """Register all commands"""
        logger.info("Multi-Bot commands đã được đăng ký")
