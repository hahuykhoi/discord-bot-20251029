import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class ByeCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.bye_data_file = 'data/bye_data.json'
        self.bye_data = self.load_bye_data()
        
    def load_bye_data(self):
        """Load bye messages data from JSON file"""
        if os.path.exists(self.bye_data_file):
            try:
                with open(self.bye_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_bye_data(self):
        """Save bye messages data to JSON file"""
        os.makedirs(os.path.dirname(self.bye_data_file), exist_ok=True)
        with open(self.bye_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.bye_data, f, ensure_ascii=False, indent=2)
    
    def is_admin(self, user_id):
        """Check if user is admin or supreme admin"""
        return self.bot_instance.is_admin(user_id)
    
    def get_bye_message(self, user_id):
        """Get bye message for a user"""
        return self.bye_data.get(str(user_id))
    
    def set_bye_message(self, user_id, message):
        """Set bye message for a user"""
        self.bye_data[str(user_id)] = {
            'message': message,
            'set_time': datetime.now().isoformat(),
            'active': True
        }
        self.save_bye_data()
    
    def remove_bye_message(self, user_id):
        """Remove bye message for a user"""
        if str(user_id) in self.bye_data:
            del self.bye_data[str(user_id)]
            self.save_bye_data()
            return True
        return False
    
    async def bye_command_impl(self, ctx, message=None):
        """
        Set auto-reply message when mentioned
        Usage: ;bye <message> - Set bye message
               ;bye off - Remove bye message
               ;bye - Show current bye message
        """
        # Check if user is admin
        if not self.is_admin(ctx.author.id):
            embed = discord.Embed(
                title="❌ Không có quyền",
                description="Chỉ Admin mới có thể sử dụng lệnh này!",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        # Show current bye message
        if message is None:
            current_bye = self.get_bye_message(ctx.author.id)
            if current_bye:
                embed = discord.Embed(
                    title="💬 Tin nhắn Bye hiện tại",
                    description=f"**Nội dung:** {current_bye['message']}\n**Đặt lúc:** {current_bye['set_time'][:19].replace('T', ' ')}",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="💬 Tin nhắn Bye",
                    description="Bạn chưa đặt tin nhắn bye nào.",
                    color=0xffff00
                )
            await ctx.send(embed=embed)
            return
        
        # Remove bye message
        if message.lower() == 'off':
            if self.remove_bye_message(ctx.author.id):
                embed = discord.Embed(
                    title="✅ Đã tắt",
                    description="Đã tắt tin nhắn bye tự động.",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Bạn chưa có tin nhắn bye nào để tắt.",
                    color=0xff0000
                )
            await ctx.send(embed=embed)
            return
        
        # Set bye message
        self.set_bye_message(ctx.author.id, message)
        embed = discord.Embed(
            title="✅ Đã đặt tin nhắn Bye",
            description=f"**Nội dung:** {message}\n\nKhi ai đó tag bạn, bot sẽ tự động trả lời với nội dung này.",
            color=0x00ff00
        )
        embed.add_field(
            name="📝 Lưu ý",
            value="• Nếu bạn đang AFK, tin nhắn bye sẽ thay thế trạng thái AFK\n• Chỉ Admin mới có thể sử dụng tính năng này\n• Dùng ; off` để tắt",
            inline=False
        )
        await ctx.send(embed=embed)
    
    async def handle_bye_mention(self, message):
        """Xử lý khi admin có bye message được mention"""
        try:
            for mentioned_user in message.mentions:
                # Bỏ qua nếu là bot
                if mentioned_user.bot:
                    continue
                
                # Kiểm tra user có bye message không
                bye_data = self.get_bye_message(mentioned_user.id)
                if not bye_data:
                    continue
                
                # Kiểm tra user có đang AFK không
                is_afk = False
                if hasattr(self.bot, 'afk_commands'):
                    is_afk = self.bot.afk_commands.is_user_afk(mentioned_user.id)
                
                # Nếu đang AFK, bỏ AFK và thay thế bằng bye message
                if is_afk:
                    # Bỏ AFK
                    self.bot.afk_commands.remove_afk(mentioned_user.id)
                    
                    # Tạo embed thông báo bỏ AFK và bye message
                    embed = discord.Embed(
                        title="💬 Tin nhắn tự động",
                        description=f"**{mentioned_user.display_name}** đã quay lại và để lại tin nhắn:",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="📝 Nội dung",
                        value=bye_data['message'],
                        inline=False
                    )
                    embed.set_footer(text="Đã tự động bỏ AFK • Tin nhắn bye tự động")
                else:
                    # Chỉ gửi bye message
                    embed = discord.Embed(
                        title="💬 Tin nhắn tự động",
                        description=f"**{mentioned_user.display_name}** để lại tin nhắn:",
                        color=0x0099ff,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="📝 Nội dung",
                        value=bye_data['message'],
                        inline=False
                    )
                    embed.set_footer(text="Tin nhắn bye tự động")
                
                # Gửi tin nhắn
                await message.channel.send(embed=embed)
                
        except Exception as e:
            # Log lỗi nhưng không gửi tin nhắn lỗi để tránh spam
            print(f"Lỗi trong bye mention handler: {e}")
    
    def register_commands(self):
        """Register all commands"""
        @self.bot.command(name='bye')
        async def bye_command(ctx, *, message=None):
            await self.bye_command_impl(ctx, message)
        
        @self.bot.command(name='byelist')
        async def bye_list(ctx):
            await self.bye_list_impl(ctx)
    
    async def bye_list_impl(self, ctx):
        """Show list of users with bye messages (Admin only)"""
        if not self.is_admin(ctx.author.id):
            embed = discord.Embed(
                title="❌ Không có quyền",
                description="Chỉ Admin mới có thể xem danh sách này!",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if not self.bye_data:
            embed = discord.Embed(
                title="📋 Danh sách Bye Messages",
                description="Không có admin nào đặt tin nhắn bye.",
                color=0xffff00
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Danh sách Bye Messages",
            color=0x00ff00
        )
        
        for user_id, data in self.bye_data.items():
            try:
                user = self.bot.get_user(int(user_id))
                username = user.display_name if user else f"Unknown User ({user_id})"
                message_preview = data['message'][:50] + "..." if len(data['message']) > 50 else data['message']
                set_time = data['set_time'][:19].replace('T', ' ')
                
                embed.add_field(
                    name=f"👤 {username}",
                    value=f"**Tin nhắn:** {message_preview}\n**Đặt lúc:** {set_time}",
                    inline=False
                )
            except:
                continue
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ByeCommands(bot))
