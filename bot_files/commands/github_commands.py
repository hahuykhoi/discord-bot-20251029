"""
GitHub commands - Lấy thông tin tài khoản GitHub
"""
import discord
from discord.ext import commands
import logging
import aiohttp
import asyncio
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class GitHubCommands(BaseCommand):
    """Class chứa các commands GitHub"""
    
    def register_commands(self):
        """Register GitHub commands"""
        
        @self.bot.command(name='github')
        async def github_info(ctx, username: str = None):
            """
            Lấy thông tin tài khoản GitHub
            
            Usage: ;github <username>
            """
            await self._github_info_impl(ctx, username)
    
    async def _github_info_impl(self, ctx, username: str):
        """
        Implementation thực tế của github command
        """
        if not username:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Vui lòng cung cấp username GitHub!\n"
                f"Ví dụ: ; torvalds`",
                mention_author=True
            )
            return
        
        # Remove @ if user includes it
        username = username.replace('@', '')
        
        # Send typing indicator
        async with ctx.typing():
            try:
                # Call GitHub API
                api_url = f"https://huutri.id.vn/api/info/github?username={username}"
                
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
                
                # Check if response has the expected fields (GitHub typically has 'login' field)
                if not data or 'login' not in data:
                    error_msg = data.get('message', 'Không tìm thấy tài khoản GitHub hoặc tài khoản không tồn tại')
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ {error_msg}",
                        mention_author=True
                    )
                    return
                
                # The API returns data directly
                user_data = data
                
                # Create embed
                embed = discord.Embed(
                    title=f"🐙 Thông tin GitHub: {user_data.get('login', username)}",
                    color=discord.Color.from_rgb(36, 41, 46),  # GitHub dark color
                    timestamp=datetime.now()
                )
                
                # Basic info
                display_name = user_data.get('name') or user_data.get('login', 'N/A')
                bio = user_data.get('bio', 'Không có bio')
                location = user_data.get('location', 'N/A')
                company = user_data.get('company', 'N/A')
                blog = user_data.get('blog', '')
                user_id = user_data.get('id', 'N/A')
                
                embed.add_field(
                    name="👤 Thông tin cơ bản",
                    value=(
                        f"**Tên hiển thị:** {display_name}\n"
                        f"**Username:** {user_data.get('login', username)}\n"
                        f"**User ID:** {user_id}\n"
                        f"**Địa điểm:** {location}\n"
                        f"**Công ty:** {company}"
                    ),
                    inline=False
                )
                
                # Bio
                if bio and bio != 'Không có bio':
                    embed.add_field(
                        name="📝 Bio",
                        value=bio[:200] + ('...' if len(bio) > 200 else ''),
                        inline=False
                    )
                
                # Stats
                followers = user_data.get('followers', 0)
                following = user_data.get('following', 0)
                public_repos = user_data.get('public_repos', 0)
                public_gists = user_data.get('public_gists', 0)
                
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
                        f"**Public Repos:** {format_number(public_repos)} ({safe_format(public_repos)})\n"
                        f"**Public Gists:** {format_number(public_gists)} ({safe_format(public_gists)})"
                    ),
                    inline=True
                )
                
                # Account info
                created_at = user_data.get('created_at', '')
                updated_at = user_data.get('updated_at', '')
                
                if created_at:
                    try:
                        # Parse ISO date
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_str = created_date.strftime('%d/%m/%Y')
                    except:
                        created_str = created_at[:10]  # Fallback to first 10 chars
                else:
                    created_str = 'N/A'
                
                embed.add_field(
                    name="📅 Thông tin tài khoản",
                    value=(
                        f"**Tạo tài khoản:** {created_str}\n"
                        f"**Loại tài khoản:** {user_data.get('type', 'User')}\n"
                        f"**Hireable:** {'✅ Có' if user_data.get('hireable') else '❌ Không'}"
                    ),
                    inline=True
                )
                
                # Profile picture
                avatar_url = user_data.get('avatar_url')
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)
                
                # Links
                profile_url = user_data.get('html_url', f"https://github.com/{username}")
                links_text = f"[GitHub Profile]({profile_url})"
                
                if blog and blog.strip():
                    # Add http if not present
                    blog_url = blog if blog.startswith(('http://', 'https://')) else f"https://{blog}"
                    links_text += f" • [Website]({blog_url})"
                
                embed.add_field(
                    name="🔗 Liên kết",
                    value=links_text,
                    inline=False
                )
                
                # Footer
                embed.set_footer(
                    text="GitHub Info • Powered by huutri.id.vn API",
                    icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                logger.info(f"GitHub info retrieved for {username} by {ctx.author}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in GitHub command: {e}")
                
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
                        f"{ctx.author.mention} ❌ Có lỗi xảy ra khi lấy thông tin GitHub: {error_msg[:100]}",
                        mention_author=True
                    )
