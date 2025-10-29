"""
Spotify music commands for Discord bot
"""
import discord
from discord.ext import commands
import logging
import re
import asyncio
import aiohttp
from datetime import datetime, timedelta
from .base import BaseCommand

logger = logging.getLogger(__name__)

class SpotifyCommands(BaseCommand):
    """Class chứa các commands liên quan đến Spotify"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.current_music_task = None
        self.current_track_info = None
    
    def register_commands(self):
        """Register Spotify commands"""
        
        @self.bot.command(name='spotify')
        async def spotify_command(ctx, *, spotify_url: str = None):
            """
            Hiển thị bot đang nghe nhạc trên Spotify (Admin only)
            
            Usage: ;spotify <spotify_url>
            Example: ;spotify https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh
            """
            # Kiểm tra quyền sử dụng dynamic permission system
            if hasattr(self.bot_instance, 'permission_manager'):
                has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'spotify')
                if not has_permission:
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Bạn không có quyền sử dụng lệnh Spotify!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
            else:
                # Fallback: Kiểm tra quyền admin nếu không có permission system
                if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ admin mới có thể sử dụng lệnh Spotify!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
            
            if spotify_url is None:
                await self._show_spotify_help(ctx)
                return
            
            # Validate Spotify URL
            if not self._is_valid_spotify_url(spotify_url):
                embed = discord.Embed(
                    title="❌ URL không hợp lệ",
                    description="Vui lòng cung cấp URL Spotify hợp lệ!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="📝 Định dạng đúng",
                    value="• `https://open.spotify.com/track/...`\n• `https://open.spotify.com/album/...`\n• `https://open.spotify.com/playlist/...`",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Extract info from Spotify URL
            spotify_info = await self._get_spotify_track_info(spotify_url)
            
            if not spotify_info:
                embed = discord.Embed(
                    title="❌ Không thể lấy thông tin",
                    description="Không thể lấy thông tin bài hát từ Spotify!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            try:
                # Cancel previous music task if exists
                if self.current_music_task and not self.current_music_task.done():
                    self.current_music_task.cancel()
                
                # Set bot activity to show listening to Spotify
                activity = discord.Activity(
                    type=discord.ActivityType.listening,
                    name=f"{spotify_info['name']} - {spotify_info['artist']}",
                    url=spotify_url
                )
                await self.bot.change_presence(activity=activity)
                
                # Store current track info
                self.current_track_info = spotify_info
                
                # Calculate end time (default 3 minutes if duration not available)
                duration_minutes = spotify_info.get('duration_minutes', 3)
                end_time = datetime.now() + timedelta(minutes=duration_minutes)
                
                # Send confirmation embed
                embed = discord.Embed(
                    title="🎵 Bot đang nghe nhạc trên Spotify",
                    description=f"**{spotify_info['name']}**\nby {spotify_info['artist']}",
                    color=0x1DB954,  # Spotify green color
                    url=spotify_url
                )
                
                embed.add_field(
                    name="🎧 Loại",
                    value=spotify_info['type'].title(),
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ Thời lượng",
                    value=f"~{duration_minutes} phút",
                    inline=True
                )
                
                embed.add_field(
                    name="🕐 Kết thúc lúc",
                    value=f"<t:{int(end_time.timestamp())}:t>",
                    inline=True
                )
                
                embed.add_field(
                    name="🔗 Link",
                    value=f"[Mở trên Spotify]({spotify_url})",
                    inline=True
                )
                
                embed.add_field(
                    name="👤 Được đặt bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                if spotify_info.get('image_url'):
                    embed.set_thumbnail(url=spotify_info['image_url'])
                else:
                    embed.set_thumbnail(url="https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_CMYK_Green.png")
                
                embed.set_footer(
                    text="🎵 Bot sẽ tự động dừng khi bài hát kết thúc",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
                # Start auto-stop task
                self.current_music_task = asyncio.create_task(
                    self._auto_stop_music(duration_minutes * 60, ctx.channel)
                )
                
                logger.info(f"Spotify activity set by {ctx.author}: {spotify_info['name']} - {spotify_info['artist']} ({spotify_url}) for {duration_minutes} minutes")
                
            except Exception as e:
                logger.error(f"Error setting Spotify activity: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Có lỗi xảy ra khi thiết lập trạng thái Spotify!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='stopmusic')
        async def stop_music_command(ctx):
            """
            Dừng hiển thị trạng thái nghe nhạc (Admin only)
            
            Usage: ;stopmusic
            """
            # Kiểm tra quyền sử dụng dynamic permission system
            if hasattr(self.bot_instance, 'permission_manager'):
                has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'stopmusic')
                if not has_permission:
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Bạn không có quyền dừng nhạc!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
            else:
                # Fallback: Kiểm tra quyền admin nếu không có permission system
                if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ admin mới có thể dừng nhạc!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
            
            try:
                # Cancel current music task
                if self.current_music_task and not self.current_music_task.done():
                    self.current_music_task.cancel()
                
                # Clear bot activity
                await self.bot.change_presence(activity=None)
                
                track_name = ""
                if self.current_track_info:
                    track_name = f" ({self.current_track_info['name']})"
                
                embed = discord.Embed(
                    title="⏹️ Đã dừng hiển thị nhạc",
                    description=f"Bot không còn hiển thị trạng thái nghe nhạc nữa{track_name}.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="👤 Được dừng bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                logger.info(f"Spotify activity cleared by {ctx.author}")
                
                # Clear stored info
                self.current_track_info = None
                
            except Exception as e:
                logger.error(f"Error clearing activity: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Có lỗi xảy ra khi dừng trạng thái nhạc!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
    
    def _is_valid_spotify_url(self, url: str) -> bool:
        """Kiểm tra URL Spotify có hợp lệ không"""
        spotify_pattern = r'https://open\.spotify\.com/(track|album|playlist|artist)/[a-zA-Z0-9]+'
        return bool(re.match(spotify_pattern, url))
    
    async def _get_spotify_track_info(self, url: str) -> dict:
        """Lấy thông tin chi tiết từ Spotify URL"""
        # Extract type and ID from URL
        match = re.search(r'https://open\.spotify\.com/(\w+)/([a-zA-Z0-9]+)', url)
        if not match:
            return None
        
        content_type = match.group(1)
        content_id = match.group(2)
        
        # For now, return basic info with estimated duration
        # In a real implementation, you would use Spotify API
        type_names = {
            'track': 'Bài hát',
            'album': 'Album', 
            'playlist': 'Playlist',
            'artist': 'Nghệ sĩ'
        }
        
        # Simulate getting track info (in real app, use Spotify Web API)
        return {
            'type': type_names.get(content_type, content_type),
            'name': f"Spotify {type_names.get(content_type, 'Track')}",
            'artist': "Unknown Artist",
            'duration_minutes': 3,  # Default 3 minutes
            'id': content_id,
            'image_url': None
        }
    
    async def _auto_stop_music(self, duration_seconds: int, channel):
        """Tự động dừng nhạc sau thời gian nhất định"""
        try:
            await asyncio.sleep(duration_seconds)
            
            # Clear bot activity
            await self.bot.change_presence(activity=None)
            
            # Send notification
            if self.current_track_info:
                embed = discord.Embed(
                    title="🎵 Bài hát đã kết thúc",
                    description=f"**{self.current_track_info['name']}** đã phát xong.\nBot đã tự động dừng hiển thị trạng thái nhạc.",
                    color=0x1DB954
                )
                await channel.send(embed=embed)
                logger.info(f"Auto-stopped Spotify activity: {self.current_track_info['name']}")
            
            # Clear stored info
            self.current_track_info = None
            
        except asyncio.CancelledError:
            logger.info("Auto-stop music task was cancelled")
        except Exception as e:
            logger.error(f"Error in auto-stop music task: {e}")
    
    def _extract_spotify_info(self, url: str) -> dict:
        """Trích xuất thông tin cơ bản từ URL Spotify (legacy method)"""
        # Extract type and ID from URL
        match = re.search(r'https://open\.spotify\.com/(\w+)/([a-zA-Z0-9]+)', url)
        if match:
            content_type = match.group(1)
            content_id = match.group(2)
            
            # Generate a display name based on type
            type_names = {
                'track': 'Bài hát',
                'album': 'Album', 
                'playlist': 'Playlist',
                'artist': 'Nghệ sĩ'
            }
            
            return {
                'type': type_names.get(content_type, content_type),
                'name': f"{type_names.get(content_type, 'Nội dung')} Spotify",
                'id': content_id
            }
        
        return {
            'type': 'Nhạc',
            'name': 'Spotify Music',
            'id': 'unknown'
        }
    
    async def _show_spotify_help(self, ctx):
        """Hiển thị hướng dẫn sử dụng lệnh Spotify"""
        embed = discord.Embed(
            title="🎵 Lệnh Spotify",
            description="Hiển thị bot đang nghe nhạc trên Spotify",
            color=0x1DB954
        )
        
        embed.add_field(
            name="📝 Cách sử dụng",
            value=(
                "`/spotify <spotify_url>` - Đặt trạng thái nghe nhạc\n"
                "`/stopmusic` - Dừng hiển thị trạng thái nhạc"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔗 URL hỗ trợ",
            value=(
                "• Track: `https://open.spotify.com/track/...`\n"
                "• Album: `https://open.spotify.com/album/...`\n"
                "• Playlist: `https://open.spotify.com/playlist/...`\n"
                "• Artist: `https://open.spotify.com/artist/...`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Ví dụ",
            value="`/spotify https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh`",
            inline=False
        )
        
        embed.add_field(
            name="🔒 Quyền hạn",
            value="Chỉ Admin mới có thể sử dụng",
            inline=False
        )
        
        embed.add_field(
            name="⏰ Tự động dừng",
            value="Bot sẽ tự động dừng hiển thị nhạc khi bài hát kết thúc (~3 phút)",
            inline=False
        )
        
        embed.set_thumbnail(url="https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_CMYK_Green.png")
        
        await ctx.reply(embed=embed, mention_author=True)
