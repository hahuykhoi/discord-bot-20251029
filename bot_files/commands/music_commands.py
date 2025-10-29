"""
Simple Voice Commands for Discord Bot
Chỉ tham gia voice channel và ở đó
"""
import discord
from discord.ext import commands
import logging
from .base import BaseCommand

logger = logging.getLogger(__name__)

class MusicCommands(BaseCommand):
    """Class chứa lệnh voice đơn giản"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.voice_clients = {}  # Guild ID -> VoiceClient
        
    def register_commands(self):
        """Register simple voice command"""
        
        @self.bot.command(name='join', aliases=['j'])
        async def join_voice(ctx):
            """Tham gia voice channel và ở đó cho đến khi bị kick"""
            # Kiểm tra user có trong voice channel không
            if not ctx.author.voice:
                embed = discord.Embed(
                    title="❌ Không tìm thấy voice channel",
                    description="Bạn cần vào voice channel trước khi sử dụng lệnh này!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            channel = ctx.author.voice.channel
            
            # Kiểm tra bot đã trong voice channel chưa
            if ctx.guild.id in self.voice_clients:
                if self.voice_clients[ctx.guild.id].channel == channel:
                    embed = discord.Embed(
                        title="🎵 Đã trong voice channel",
                        description=f"Bot đã có mặt trong **{channel.name}**!\n\nBot sẽ ở đây cho đến khi bị kick hoặc disconnect.",
                        color=discord.Color.blue()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                else:
                    # Move to new channel
                    await self.voice_clients[ctx.guild.id].move_to(channel)
            else:
                # Join new channel
                try:
                    voice_client = await channel.connect()
                    self.voice_clients[ctx.guild.id] = voice_client
                except Exception as e:
                    embed = discord.Embed(
                        title="❌ Không thể tham gia voice channel",
                        description=f"Lỗi: {str(e)}",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
            
            embed = discord.Embed(
                title="🎵 Đã tham gia voice channel",
                description=f"Bot đã tham gia **{channel.name}**!\n\n💡 **Bot sẽ ở đây cho đến khi:**\n• Bị kick khỏi voice channel\n• Bị disconnect\n• Server restart",
                color=discord.Color.green()
            )
            embed.add_field(
                name="👥 Thành viên trong channel",
                value=f"{len(channel.members)} người",
                inline=True
            )
            embed.add_field(
                name="🔊 Trạng thái",
                value="Đang kết nối",
                inline=True
            )
            embed.add_field(
                name="⏰ Thời gian",
                value="Vô thời hạn",
                inline=True
            )
            embed.set_footer(text=f"Được gọi bởi {ctx.author.display_name}")
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Bot joined voice channel {channel.name} in {ctx.guild.name} (permanent stay)")
