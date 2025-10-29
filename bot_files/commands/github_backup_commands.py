"""
GitHub Backup Commands - Backup dữ liệu lên GitHub private repository
Lệnh: ;gitbackup, ;gitrestore (Supreme Admin only)
"""
import discord
from discord.ext import commands
import json
import os
import base64
import aiohttp
import asyncio
from datetime import datetime
import logging
from .base import BaseCommand

logger = logging.getLogger(__name__)

class GitHubBackupCommands(BaseCommand):
    def __init__(self, bot_instance):
        """
        Khởi tạo GitHub Backup Commands
        
        Args:
            bot_instance: Instance của AutoReplyBotRefactored
        """
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        
        # Load GitHub config
        self.github_token = None
        self.github_username = None
        self.backup_repo = None
        self.load_github_config()
        
        logger.info("GitHub Backup Commands đã được khởi tạo")
    
    def load_github_config(self):
        """Load GitHub configuration từ config.json"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.github_token = config.get('github_token')
                self.github_username = config.get('github_username')
                self.backup_repo = config.get('github_backup_repo', 'bot-data-backup')
                
                if self.github_token and self.github_username:
                    logger.info("✅ GitHub config loaded successfully")
                else:
                    logger.warning("⚠️ GitHub token hoặc username chưa được cấu hình")
            else:
                logger.warning("⚠️ config.json không tồn tại")
        except Exception as e:
            logger.error(f"❌ Lỗi khi load GitHub config: {e}")
    
    async def create_github_repo(self):
        """Tạo private repository trên GitHub"""
        if not self.github_token:
            return False, "GitHub token chưa được cấu hình"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Discord-Bot-Backup'
        }
        
        repo_data = {
            'name': self.backup_repo,
            'description': 'Discord Bot Data Backup - Private Repository',
            'private': True,
            'auto_init': True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.github.com/user/repos',
                    headers=headers,
                    json=repo_data
                ) as response:
                    if response.status == 201:
                        logger.info(f"✅ Đã tạo repository: {self.backup_repo}")
                        return True, "Repository đã được tạo thành công"
                    elif response.status == 422:
                        # Repository đã tồn tại
                        logger.info(f"ℹ️ Repository {self.backup_repo} đã tồn tại")
                        return True, "Repository đã tồn tại"
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Lỗi tạo repository: {response.status} - {error_text}")
                        return False, f"Lỗi API: {response.status}"
        except Exception as e:
            logger.error(f"❌ Exception khi tạo repository: {e}")
            return False, f"Lỗi kết nối: {str(e)}"
    
    async def upload_file_to_github(self, file_path, content, commit_message, max_retries=3):
        """Upload file lên GitHub repository với retry mechanism"""
        if not self.github_token:
            return False, "GitHub token chưa được cấu hình"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Discord-Bot-Backup'
        }
        
        # Encode content to base64
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        file_data = {
            'message': commit_message,
            'content': content_b64
        }
        
        # Retry mechanism
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Get existing file SHA if exists
                    async with session.get(
                        f'https://api.github.com/repos/{self.github_username}/{self.backup_repo}/contents/{file_path}',
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            existing_file = await response.json()
                            file_data['sha'] = existing_file['sha']
                    
                    # Upload/update file
                    async with session.put(
                        f'https://api.github.com/repos/{self.github_username}/{self.backup_repo}/contents/{file_path}',
                        headers=headers,
                        json=file_data
                    ) as response:
                        if response.status in [200, 201]:
                            return True, "File uploaded thành công"
                        else:
                            error_text = await response.text()
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ Attempt {attempt + 1} failed for {file_path}: {response.status} - Retrying...")
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            else:
                                logger.error(f"❌ Lỗi upload file {file_path}: {response.status} - {error_text}")
                                return False, f"Lỗi upload: {response.status}"
                                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Connection error attempt {attempt + 1} for {file_path}: {str(e)} - Retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ Exception khi upload {file_path}: {e}")
                    return False, f"Lỗi kết nối: {str(e)}"
        
        return False, "Tất cả attempts đều thất bại"
    
    async def backup_data_files(self):
        """Backup tất cả data files lên GitHub"""
        # Danh sách files cần backup
        data_files = [
            'shared_wallet.json',
            'taixiu_data.json',
            'flip_coin_data.json',
            'rps_data.json',
            'slot_data.json',
            'blackjack_data.json',
            'daily_data.json',
            'warnings.json',
            'maintenance_mode.json',
            'channel_permissions.json',
            'command_permissions.json',
            'supreme_admin.json',
            'admin.json',
            'priority.json'
        ]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        successful_uploads = []
        failed_uploads = []
        
        for file_name in data_files:
            if os.path.exists(file_name):
                try:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    success, message = await self.upload_file_to_github(
                        f"data/{file_name}",
                        content,
                        f"Backup {file_name} - {timestamp}"
                    )
                    
                    if success:
                        successful_uploads.append(file_name)
                    else:
                        failed_uploads.append((file_name, message))
                        
                except Exception as e:
                    failed_uploads.append((file_name, str(e)))
            else:
                failed_uploads.append((file_name, "File không tồn tại"))
        
        return successful_uploads, failed_uploads
    
    async def download_file_from_github(self, file_path):
        """Download file từ GitHub repository"""
        if not self.github_token:
            return None, "GitHub token chưa được cấu hình"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Discord-Bot-Backup'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.github.com/repos/{self.github_username}/{self.backup_repo}/contents/{file_path}',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        file_data = await response.json()
                        content_b64 = file_data['content']
                        content = base64.b64decode(content_b64).decode('utf-8')
                        return content, "Success"
                    else:
                        return None, f"File không tồn tại hoặc lỗi: {response.status}"
        except Exception as e:
            return None, f"Lỗi download: {str(e)}"
    
    def register_commands(self):
        """Đăng ký các commands cho GitHub Backup"""
        
        @self.bot.command(name='gitbackup', aliases=['gbackup'])
        async def github_backup(ctx):
            """
            Backup tất cả dữ liệu lên GitHub private repository (Supreme Admin only)
            
            Usage: ;gitbackup
            """
            try:
                # Kiểm tra quyền Supreme Admin
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể backup dữ liệu lên GitHub!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra config GitHub
                if not self.github_token or not self.github_username:
                    embed = discord.Embed(
                        title="❌ Chưa cấu hình GitHub",
                        description="GitHub token hoặc username chưa được cấu hình trong config.json!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="📝 Cần thêm vào config.json",
                        value="```json\n{\n  \"github_token\": \"your_token\",\n  \"github_username\": \"your_username\",\n  \"github_backup_repo\": \"bot-data-backup\"\n}```",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Tạo embed processing
                embed = discord.Embed(
                    title="🔄 Đang backup dữ liệu lên GitHub",
                    description="Vui lòng chờ...",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                message = await ctx.reply(embed=embed, mention_author=True)
                
                # Tạo repository nếu chưa có
                repo_success, repo_message = await self.create_github_repo()
                if not repo_success:
                    embed = discord.Embed(
                        title="❌ Lỗi tạo repository",
                        description=repo_message,
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    return
                
                # Backup data files
                successful, failed = await self.backup_data_files()
                
                # Tạo backup summary
                backup_summary = {
                    'timestamp': datetime.now().isoformat(),
                    'successful_files': successful,
                    'failed_files': [{'file': f[0], 'error': f[1]} for f in failed],
                    'total_files': len(successful) + len(failed)
                }
                
                # Upload backup summary
                await self.upload_file_to_github(
                    f"backup_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    json.dumps(backup_summary, indent=4, ensure_ascii=False),
                    f"Backup Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                # Tạo result embed
                if successful:
                    embed = discord.Embed(
                        title="✅ Backup thành công!",
                        description=f"Đã backup {len(successful)} files lên GitHub",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📦 Repository",
                        value=f"[{self.github_username}/{self.backup_repo}](https://github.com/{self.github_username}/{self.backup_repo})",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="✅ Files thành công",
                        value=f"```\n{chr(10).join(successful[:10])}{'...' if len(successful) > 10 else ''}```",
                        inline=False
                    )
                    
                    if failed:
                        failed_list = [f"❌ {f[0]}: {f[1]}" for f in failed[:5]]
                        embed.add_field(
                            name="❌ Files thất bại",
                            value=f"```\n{chr(10).join(failed_list)}{'...' if len(failed) > 5 else ''}```",
                            inline=False
                        )
                    
                    embed.set_footer(text=f"Backup by {ctx.author.display_name}")
                    
                else:
                    embed = discord.Embed(
                        title="❌ Backup thất bại",
                        description="Không có file nào được backup thành công",
                        color=discord.Color.red()
                    )
                
                await message.edit(embed=embed)
                logger.info(f"GitHub backup completed by {ctx.author}: {len(successful)} success, {len(failed)} failed")
                
            except Exception as e:
                logger.error(f"Lỗi trong gitbackup command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description=f"Có lỗi xảy ra: {str(e)[:100]}...",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='gitrestore', aliases=['grestore'])
        async def github_restore(ctx, file_name: str = None):
            """
            Restore dữ liệu từ GitHub backup (Supreme Admin only)
            
            Usage: ;gitrestore <file_name>
            """
            try:
                # Kiểm tra quyền Supreme Admin
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể restore dữ liệu từ GitHub!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                if not file_name:
                    embed = discord.Embed(
                        title="📋 GitHub Restore",
                        description="Restore dữ liệu từ GitHub backup",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📝 Cách sử dụng",
                        value="; <tên_file>`\n\nVí dụ: ; shared_wallet.json`",
                        inline=False
                    )
                    embed.add_field(
                        name="📁 Files có thể restore",
                        value="• shared_wallet.json\n• taixiu_data.json\n• flip_coin_data.json\n• rps_data.json\n• warnings.json\n• maintenance_mode.json",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra config GitHub
                if not self.github_token or not self.github_username:
                    embed = discord.Embed(
                        title="❌ Chưa cấu hình GitHub",
                        description="GitHub token hoặc username chưa được cấu hình!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Download file từ GitHub
                embed = discord.Embed(
                    title="🔄 Đang restore từ GitHub",
                    description=f"Đang tải {file_name}...",
                    color=discord.Color.orange()
                )
                message = await ctx.reply(embed=embed, mention_author=True)
                
                content, error = await self.download_file_from_github(f"data/{file_name}")
                
                if content:
                    # Backup file hiện tại trước khi restore
                    if os.path.exists(file_name):
                        backup_name = f"{file_name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        os.rename(file_name, backup_name)
                    
                    # Ghi file mới
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    embed = discord.Embed(
                        title="✅ Restore thành công!",
                        description=f"Đã restore {file_name} từ GitHub backup",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="📁 File",
                        value=file_name,
                        inline=True
                    )
                    embed.add_field(
                        name="📦 Repository",
                        value=f"{self.github_username}/{self.backup_repo}",
                        inline=True
                    )
                    embed.set_footer(text=f"Restored by {ctx.author.display_name}")
                    
                else:
                    embed = discord.Embed(
                        title="❌ Restore thất bại",
                        description=f"Không thể tải {file_name}: {error}",
                        color=discord.Color.red()
                    )
                
                await message.edit(embed=embed)
                logger.info(f"GitHub restore {file_name} by {ctx.author}: {'success' if content else 'failed'}")
                
            except Exception as e:
                logger.error(f"Lỗi trong gitrestore command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description=f"Có lỗi xảy ra: {str(e)[:100]}...",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='gitconfig')
        async def github_config(ctx):
            """
            Xem cấu hình GitHub backup (Supreme Admin only)
            
            Usage: ;gitconfig
            """
            try:
                # Kiểm tra quyền Supreme Admin
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể xem cấu hình GitHub!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                embed = discord.Embed(
                    title="⚙️ Cấu hình GitHub Backup",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🔑 GitHub Token",
                    value="✅ Đã cấu hình" if self.github_token else "❌ Chưa cấu hình",
                    inline=True
                )
                
                embed.add_field(
                    name="👤 GitHub Username",
                    value=self.github_username if self.github_username else "❌ Chưa cấu hình",
                    inline=True
                )
                
                embed.add_field(
                    name="📦 Backup Repository",
                    value=self.backup_repo if self.backup_repo else "❌ Chưa cấu hình",
                    inline=True
                )
                
                if self.github_username and self.backup_repo:
                    embed.add_field(
                        name="🔗 Repository URL",
                        value=f"[GitHub Repository](https://github.com/{self.github_username}/{self.backup_repo})",
                        inline=False
                    )
                
                embed.add_field(
                    name="📝 Hướng dẫn cấu hình",
                    value="Thêm vào `config.json`:\n```json\n{\n  \"github_token\": \"ghp_xxx\",\n  \"github_username\": \"username\",\n  \"github_backup_repo\": \"bot-data-backup\"\n}```",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong gitconfig command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {e}", mention_author=True)
        
        logger.info("Đã đăng ký GitHub Backup commands: gitbackup, gitrestore, gitconfig")
