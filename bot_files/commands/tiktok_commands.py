"""
TikTok commands - Lấy thông tin tài khoản TikTok
"""
import discord
from discord.ext import commands
import logging
import aiohttp
import asyncio
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class TikTokCommands(BaseCommand):
    """Class chứa các commands TikTok"""
    
    def register_commands(self):
        """Register TikTok commands"""
        
        @self.bot.command(name='tiktok')
        async def tiktok_info(ctx, username: str = None):
            """
            Lấy thông tin tài khoản TikTok
            
            Usage: ;tiktok <username>
            """
            await self._tiktok_info_impl(ctx, username)
    
    async def _tiktok_info_impl(self, ctx, username: str):
        """
        Implementation thực tế của tiktok command
        """
        if not username:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Vui lòng cung cấp username TikTok!\n"
                f"Ví dụ: ; khaby.lame`",
                mention_author=True
            )
            return
        
        # Remove @ if user includes it
        username = username.replace('@', '')
        
        # Send typing indicator
        async with ctx.typing():
            try:
                # Call TikTok API
                api_url = f"https://huutri.id.vn/api/info/tiktok?username={username}"
                
                timeout = aiohttp.ClientTimeout(total=15)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(api_url) as response:
                        if response.status != 200:
                            await ctx.reply(
                                f"{ctx.author.mention} ❌ Lỗi API: Không thể lấy dữ liệu (Status: {response.status})",
                                mention_author=True
                            )
                            return
                        
                        try:
                            data = await response.json()
                        except Exception as json_error:
                            logger.error(f"JSON parsing error: {json_error}")
                            await ctx.reply(
                                f"{ctx.author.mention} ❌ Lỗi phân tích dữ liệu từ API",
                                mention_author=True
                            )
                            return
                
                # Check if API returned error or valid data
                logger.info(f"API response for {username}: {list(data.keys()) if data else 'Empty response'}")
                
                # Check if response has the expected fields
                if not data or 'id' not in data:
                    error_msg = data.get('message', 'Không tìm thấy tài khoản hoặc tài khoản không tồn tại')
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ {error_msg}",
                        mention_author=True
                    )
                    return
                
                # The API returns data directly, not nested in a "data" field
                user_data = data
                
                # Create embed
                embed = discord.Embed(
                    title=f"📱 Thông tin TikTok: @{username}",
                    color=discord.Color.from_rgb(255, 0, 80),  # TikTok pink color
                    timestamp=datetime.now()
                )
                
                # Basic info
                display_name = user_data.get('nickname', 'N/A')
                bio = user_data.get('signature', 'Không có bio')
                verified = user_data.get('verified', False)
                user_id = user_data.get('id', 'N/A')
                
                embed.add_field(
                    name="👤 Thông tin cơ bản",
                    value=(
                        f"**Tên hiển thị:** {display_name}\n"
                        f"**Username:** @{username}\n"
                        f"**User ID:** {user_id}\n"
                        f"**Verified:** {'✅ Có' if verified else '❌ Không'}\n"
                        f"**Bio:** {bio[:100]}{'...' if len(bio) > 100 else ''}"
                    ),
                    inline=False
                )
                
                # Stats from the stats object
                stats = user_data.get('stats', {})
                followers = stats.get('followers', 0)
                following = stats.get('following', 0)
                likes = stats.get('likes', 0)
                videos = stats.get('videos', 0)
                
                # Format numbers safely
                def format_number(num):
                    try:
                        num = int(num) if num else 0
                        if num >= 1000000:
                            return f"{num/1000000:.1f}M"
                        elif num >= 1000:
                            return f"{num/1000:.1f}K"
                        return str(num)
                    except (ValueError, TypeError):
                        return "0"
                
                # Safe number display
                def safe_format(num):
                    try:
                        return f"{int(num):,}" if num else "0"
                    except (ValueError, TypeError):
                        return "0"
                
                embed.add_field(
                    name="📊 Thống kê",
                    value=(
                        f"**Followers:** {format_number(followers)} ({safe_format(followers)})\n"
                        f"**Following:** {format_number(following)} ({safe_format(following)})\n"
                        f"**Likes:** {format_number(likes)} ({safe_format(likes)})\n"
                        f"**Videos:** {format_number(videos)} ({safe_format(videos)})"
                    ),
                    inline=True
                )
                
                # Additional info if available
                if user_data.get('region'):
                    embed.add_field(
                        name="🌍 Khu vực",
                        value=user_data.get('region', 'N/A'),
                        inline=True
                    )
                
                # Profile picture
                avatar_url = user_data.get('avatar')
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)
                
                # TikTok profile link
                profile_url = f"https://www.tiktok.com/@{username}"
                embed.add_field(
                    name="🔗 Liên kết",
                    value=f"[Xem profile TikTok]({profile_url})",
                    inline=False
                )
                
                # Footer
                embed.set_footer(
                    text="TikTok Info • Powered by huutri.id.vn API",
                    icon_url="https://sf16-website-login.neutral.ttwstatic.com/obj/tiktok_web_login_static/tiktok/webapp/main/webapp-desktop/8152caf0c8e8bc67ae0d.png"
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                logger.info(f"TikTok info retrieved for @{username} by {ctx.author}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in TikTok command: {e}")
                
                # Handle specific error types
                if "timeout" in error_msg.lower():
                    await ctx.reply(
                        f"{ctx.author.mention} ⏰ Timeout: API không phản hồi trong thời gian cho phép",
                        mention_author=True
                    )
                elif "connection" in error_msg.lower():
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Lỗi kết nối: Không thể kết nối đến API",
                        mention_author=True
                    )
                else:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Có lỗi xảy ra khi lấy thông tin TikTok: {error_msg[:100]}",
                        mention_author=True
                    )
