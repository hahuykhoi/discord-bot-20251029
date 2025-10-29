"""
Video commands - Gửi video vào kênh
"""
import discord
from discord.ext import commands
import logging
import os
import asyncio
import aiohttp
import aiofiles
from datetime import datetime
from urllib.parse import urlparse
import re
from .base import BaseCommand

logger = logging.getLogger(__name__)

class VideoCommands(BaseCommand):
    """Class chứa các commands video"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.videos_dir = "videos"
        # Tạo thư mục videos nếu chưa tồn tại
        if not os.path.exists(self.videos_dir):
            os.makedirs(self.videos_dir)
            logger.info(f"Đã tạo thư mục {self.videos_dir}")
    
    def register_commands(self):
        """Register video commands"""
        
        @self.bot.group(name='video', invoke_without_command=True)
        async def video_group(ctx, *, video_name: str = None):
            """
            Gửi video vào kênh hiện tại
            
            Usage: ;video <tên video>
            """
            await self._send_video_impl(ctx, video_name)
        
        @video_group.command(name='add')
        async def add_video(ctx, url: str, *, filename: str = None):
            """
            Tải video từ URL và lưu vào thư mục videos
            
            Usage: ;video add <URL> <tên file>
            """
            await self._add_video_impl(ctx, url, filename)
        
        @self.bot.command(name='listvideo', aliases=['videos'])
        async def list_videos(ctx):
            """
            Hiển thị danh sách video có sẵn
            
            Usage: ;listvideo hoặc ;videos
            """
            await self._list_videos_impl(ctx)
    
    async def _send_video_impl(self, ctx, video_name: str):
        """
        Implementation thực tế của video command
        """
        # Kiểm tra quyền gửi file
        if not ctx.channel.permissions_for(ctx.guild.me).attach_files:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Bot không có quyền gửi file trong kênh này!",
                mention_author=True
            )
            return
        
        if not video_name:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Vui lòng cung cấp tên video!\n"
                f"Sử dụng: ; <tên video>`\n"
                f"Xem danh sách video: ;`",
                mention_author=True
            )
            return
        
        # Tìm file video
        video_file = await self._find_video_file(video_name)
        
        if not video_file:
            # Hiển thị danh sách video có sẵn nếu không tìm thấy
            available_videos = await self._get_available_videos()
            if available_videos:
                # Hiển thị tối đa 20 video trong thông báo lỗi
                max_display = 20
                video_list = "\n".join([f"• `{video}`" for video in available_videos[:max_display]])
                if len(available_videos) > max_display:
                    video_list += f"\n... và {len(available_videos) - max_display} video khác"
                
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Không tìm thấy video `{video_name}`!\n\n"
                    f"**Video có sẵn:**\n{video_list}\n\n"
                    f"Sử dụng ;` để xem tất cả video.",
                    mention_author=True
                )
            else:
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Không tìm thấy video `{video_name}`!\n"
                    f"Thư mục video hiện đang trống. Vui lòng thêm video vào thư mục `{self.videos_dir}/`",
                    mention_author=True
                )
            return
        
        # Kiểm tra kích thước file (Discord limit 25MB cho server thường)
        file_size = os.path.getsize(video_file)
        max_size = 25 * 1024 * 1024  # 25MB
        
        if file_size > max_size:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Video `{os.path.basename(video_file)}` quá lớn! "
                f"Kích thước: {file_size / (1024*1024):.1f}MB (Tối đa: 25MB)",
                mention_author=True
            )
            return
        
        # Gửi video
        try:
            async with ctx.typing():
                # Gửi chỉ file video, không có embed
                with open(video_file, 'rb') as f:
                    discord_file = discord.File(f, filename=os.path.basename(video_file))
                    await ctx.send(file=discord_file)
                
                logger.info(f"Video {os.path.basename(video_file)} sent by {ctx.author} in {ctx.guild.name}#{ctx.channel.name}")
                
                # Xóa tin nhắn lệnh gốc để giữ kênh sạch sẽ
                try:
                    await ctx.message.delete()
                except discord.NotFound:
                    pass  # Tin nhắn đã bị xóa
                except discord.Forbidden:
                    pass  # Không có quyền xóa
                
        except discord.HTTPException as e:
            if "Request entity too large" in str(e):
                await ctx.reply(
                    f"{ctx.author.mention} ❌ File quá lớn để upload lên Discord!",
                    mention_author=True
                )
            else:
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Lỗi khi gửi video: {str(e)[:100]}",
                    mention_author=True
                )
        except Exception as e:
            logger.error(f"Error sending video {video_file}: {e}")
            await ctx.reply(
                f"{ctx.author.mention} ❌ Có lỗi xảy ra khi gửi video: {str(e)[:100]}",
                mention_author=True
            )
    
    async def _list_videos_impl(self, ctx):
        """
        Implementation thực tế của listvideo command
        """
        available_videos = await self._get_available_videos()
        
        if not available_videos:
            await ctx.reply(
                f"{ctx.author.mention} 📁 Thư mục video hiện đang trống!\n"
                f"Vui lòng thêm video vào thư mục `{self.videos_dir}/` để sử dụng lệnh ;`",
                mention_author=True
            )
            return
        
        # Tạo embed danh sách video
        embed = discord.Embed(
            title="🎬 Danh sách Video có sẵn",
            description=f"Tổng cộng: **{len(available_videos)}** video",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        # Tạo danh sách tất cả video với thông tin file
        video_list = []
        for i, video in enumerate(available_videos, 1):
            video_path = os.path.join(self.videos_dir, video)
            try:
                file_size = os.path.getsize(video_path)
                size_mb = file_size / (1024 * 1024)
                video_list.append(f"`{i}.` **{video}** ({size_mb:.1f}MB)")
            except:
                video_list.append(f"`{i}.` **{video}** (Lỗi đọc file)")
        
        # Discord embed field có giới hạn 1024 ký tự mỗi field
        # Chia video thành nhiều field nếu cần thiết
        max_chars_per_field = 1000  # Để lại chút buffer
        current_field_content = ""
        field_number = 1
        
        for video_line in video_list:
            # Kiểm tra nếu thêm video này vào field hiện tại có vượt quá giới hạn không
            if len(current_field_content + video_line + "\n") > max_chars_per_field:
                # Thêm field hiện tại vào embed
                if current_field_content:
                    embed.add_field(
                        name=f"📋 Video (Phần {field_number})" if field_number > 1 else "📋 Danh sách Video",
                        value=current_field_content.strip(),
                        inline=False
                    )
                    field_number += 1
                    current_field_content = ""
            
            current_field_content += video_line + "\n"
        
        # Thêm field cuối cùng nếu còn content
        if current_field_content:
            embed.add_field(
                name=f"📋 Video (Phần {field_number})" if field_number > 1 else "📋 Danh sách Video",
                value=current_field_content.strip(),
                inline=False
            )
        
        # Thêm hướng dẫn sử dụng
        embed.add_field(
            name="💡 Cách sử dụng",
            value="Sử dụng ; <tên video>` để gửi video vào kênh",
            inline=False
        )
        
        embed.set_footer(
            text=f"Yêu cầu bởi {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Video list requested by {ctx.author} in {ctx.guild.name}#{ctx.channel.name}")
    
    async def _find_video_file(self, video_name: str) -> str:
        """
        Tìm file video theo tên (hỗ trợ tìm kiếm không phân biệt hoa thường và không cần đuôi file)
        """
        if not os.path.exists(self.videos_dir):
            return None
        
        # Danh sách các định dạng video được hỗ trợ
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        
        # Tìm kiếm chính xác trước
        for ext in video_extensions:
            # Thử với tên gốc
            exact_match = os.path.join(self.videos_dir, video_name)
            if os.path.isfile(exact_match):
                return exact_match
            
            # Thử với tên + extension
            with_ext = os.path.join(self.videos_dir, video_name + ext)
            if os.path.isfile(with_ext):
                return with_ext
        
        # Tìm kiếm không phân biệt hoa thường
        try:
            files = os.listdir(self.videos_dir)
            video_name_lower = video_name.lower()
            
            for file in files:
                file_lower = file.lower()
                file_name_no_ext = os.path.splitext(file_lower)[0]
                
                # Kiểm tra xem có phải file video không
                if any(file_lower.endswith(ext) for ext in video_extensions):
                    # Tìm kiếm theo tên file đầy đủ
                    if file_lower == video_name_lower:
                        return os.path.join(self.videos_dir, file)
                    
                    # Tìm kiếm theo tên không có extension
                    if file_name_no_ext == video_name_lower:
                        return os.path.join(self.videos_dir, file)
                    
                    # Tìm kiếm chứa từ khóa
                    if video_name_lower in file_name_no_ext:
                        return os.path.join(self.videos_dir, file)
        
        except Exception as e:
            logger.error(f"Error searching for video file: {e}")
        
        return None
    
    async def _get_available_videos(self) -> list:
        """
        Lấy danh sách video có sẵn
        """
        if not os.path.exists(self.videos_dir):
            return []
        
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        videos = []
        
        try:
            for file in os.listdir(self.videos_dir):
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    videos.append(file)
            
            # Sắp xếp theo tên
            videos.sort()
            
        except Exception as e:
            logger.error(f"Error listing videos: {e}")
        
        return videos
    
    async def _add_video_impl(self, ctx, url: str, filename: str = None):
        """
        Implementation thực tế của video add command
        """
        # Kiểm tra quyền sử dụng dynamic permission system
        if hasattr(self.bot_instance, 'permission_manager'):
            has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'video')
            if not has_permission:
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Bạn không có quyền thêm video!",
                    mention_author=True
                )
                return
        else:
            # Fallback: Kiểm tra quyền admin nếu không có permission system
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Bạn không có quyền thêm video! "
                    f"Chỉ admin mới có thể sử dụng lệnh này.",
                    mention_author=True
                )
                return
        
        if not url:
            await ctx.reply(
                f"{ctx.author.mention} ❌ Vui lòng cung cấp URL video!\n"
                f"Sử dụng: ; add <URL> <tên file>`",
                mention_author=True
            )
            return
        
        # Validate URL
        if not self._is_valid_url(url):
            await ctx.reply(
                f"{ctx.author.mention} ❌ URL không hợp lệ! "
                f"Vui lòng cung cấp URL đầy đủ (bắt đầu với http:// hoặc https://)",
                mention_author=True
            )
            return
        
        # Generate filename if not provided
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                filename = f"video_{int(datetime.now().timestamp())}.mp4"
        
        # Ensure filename has valid extension
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        if not any(filename.lower().endswith(ext) for ext in video_extensions):
            filename += '.mp4'  # Default to mp4
        
        # Sanitize filename
        filename = self._sanitize_filename(filename)
        filepath = os.path.join(self.videos_dir, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            await ctx.reply(
                f"{ctx.author.mention} ❌ File `{filename}` đã tồn tại! "
                f"Vui lòng chọn tên khác hoặc xóa file cũ trước.",
                mention_author=True
            )
            return
        
        # Send initial message
        embed = discord.Embed(
            title="📥 Đang tải video...",
            description=f"**URL:** {url[:100]}{'...' if len(url) > 100 else ''}\n**File:** `{filename}`",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        status_msg = await ctx.reply(embed=embed, mention_author=True)
        
        try:
            # Download video
            async with ctx.typing():
                timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            await status_msg.edit(embed=discord.Embed(
                                title="❌ Lỗi tải video",
                                description=f"Không thể tải video từ URL (Status: {response.status})",
                                color=discord.Color.red()
                            ))
                            return
                        
                        # Check content type
                        content_type = response.headers.get('content-type', '').lower()
                        if not any(vid_type in content_type for vid_type in ['video', 'octet-stream', 'application']):
                            logger.warning(f"Suspicious content type: {content_type}")
                        
                        # Check file size
                        content_length = response.headers.get('content-length')
                        if content_length:
                            file_size = int(content_length)
                            max_size = 100 * 1024 * 1024  # 100MB limit for download
                            if file_size > max_size:
                                await status_msg.edit(embed=discord.Embed(
                                    title="❌ File quá lớn",
                                    description=f"File có kích thước {file_size / (1024*1024):.1f}MB (Tối đa: 100MB)",
                                    color=discord.Color.red()
                                ))
                                return
                        
                        # Update progress
                        embed.description = f"**URL:** {url[:100]}{'...' if len(url) > 100 else ''}\n**File:** `{filename}`\n📊 Đang tải..."
                        embed.color = discord.Color.blue()
                        await status_msg.edit(embed=embed)
                        
                        # Download and save file
                        async with aiofiles.open(filepath, 'wb') as f:
                            downloaded = 0
                            async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress every 1MB
                                if downloaded % (1024 * 1024) == 0:
                                    embed.description = f"**URL:** {url[:100]}{'...' if len(url) > 100 else ''}\n**File:** `{filename}`\n📊 Đã tải: {downloaded / (1024*1024):.1f}MB"
                                    try:
                                        await status_msg.edit(embed=embed)
                                    except:
                                        pass  # Ignore rate limit errors
            
            # Verify downloaded file
            if not os.path.exists(filepath):
                await status_msg.edit(embed=discord.Embed(
                    title="❌ Lỗi lưu file",
                    description="Không thể lưu file vào thư mục videos",
                    color=discord.Color.red()
                ))
                return
            
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                os.remove(filepath)
                await status_msg.edit(embed=discord.Embed(
                    title="❌ File trống",
                    description="File tải về có kích thước 0 bytes",
                    color=discord.Color.red()
                ))
                return
            
            # Success message
            success_embed = discord.Embed(
                title="✅ Tải video thành công!",
                description=(
                    f"**File:** `{filename}`\n"
                    f"**Kích thước:** {file_size / (1024*1024):.1f}MB\n"
                    f"**Lưu tại:** `{self.videos_dir}/{filename}`"
                ),
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            success_embed.add_field(
                name="💡 Cách sử dụng",
                value=f"Sử dụng ; {os.path.splitext(filename)[0]}` để gửi video này",
                inline=False
            )
            success_embed.set_footer(
                text=f"Thêm bởi {ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )
            
            await status_msg.edit(embed=success_embed)
            logger.info(f"Video downloaded: {filename} ({file_size} bytes) by {ctx.author}")
            
        except asyncio.TimeoutError:
            await status_msg.edit(embed=discord.Embed(
                title="⏰ Timeout",
                description="Quá thời gian tải video (5 phút). URL có thể quá chậm hoặc file quá lớn.",
                color=discord.Color.red()
            ))
        except aiohttp.ClientError as e:
            await status_msg.edit(embed=discord.Embed(
                title="❌ Lỗi kết nối",
                description=f"Không thể kết nối đến URL: {str(e)[:100]}",
                color=discord.Color.red()
            ))
        except Exception as e:
            # Clean up partial file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            
            logger.error(f"Error downloading video: {e}")
            await status_msg.edit(embed=discord.Embed(
                title="❌ Lỗi tải video",
                description=f"Có lỗi xảy ra: {str(e)[:100]}",
                color=discord.Color.red()
            ))
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Kiểm tra URL có hợp lệ không
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Làm sạch tên file, loại bỏ ký tự không hợp lệ
        """
        # Remove invalid characters for Windows/Linux
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove multiple spaces and dots
        filename = re.sub(r'\.+', '.', filename)
        filename = re.sub(r'\s+', ' ', filename)
        
        # Trim and ensure not empty
        filename = filename.strip()
        if not filename:
            filename = f"video_{int(datetime.now().timestamp())}.mp4"
        
        return filename
