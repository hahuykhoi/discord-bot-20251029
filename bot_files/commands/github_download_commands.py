import discord
from discord.ext import commands
import aiohttp
import json
import os
import base64
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GitHubDownloadCommands:
    """Commands để download file từ GitHub private repository"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.config = self._load_github_config()
        
    def _load_github_config(self):
        """Load GitHub configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config_github.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading GitHub config: {e}")
            return {}
    
    def _get_github_token(self):
        """Lấy GitHub token từ environment hoặc config"""
        # Ưu tiên environment variable
        token = os.getenv('GITHUB_TOKEN')
        if token:
            return token
            
        # Fallback to config file
        try:
            with open('github_token.txt', 'r') as f:
                return f.read().strip()
        except:
            return None
    
    def _parse_github_url(self, url):
        """Parse GitHub URL để lấy owner, repo, path"""
        try:
            # https://github.com/owner/repo/blob/branch/path/to/file
            # hoặc https://github.com/owner/repo/tree/branch/folder/path
            parts = url.replace('https://github.com/', '').split('/')
            
            if len(parts) < 2:
                return None, None, None, None
                
            owner = parts[0]
            repo = parts[1]
            
            # Nếu có blob/tree thì lấy branch và path
            if len(parts) > 3 and parts[2] in ['blob', 'tree']:
                branch = parts[3]
                path = '/'.join(parts[4:]) if len(parts) > 4 else ''
            else:
                branch = 'main'  # default branch
                path = '/'.join(parts[2:]) if len(parts) > 2 else ''
                
            return owner, repo, branch, path
        except Exception as e:
            logger.error(f"Error parsing GitHub URL: {e}")
            return None, None, None, None
    
    async def _download_file_from_github(self, owner, repo, path, branch='main'):
        """Download file từ GitHub API"""
        token = self._get_github_token()
        if not token:
            raise Exception("GitHub token không được cấu hình!")
        
        # GitHub API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Discord-Bot'
        }
        
        params = {'ref': branch} if branch != 'main' else {}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers, params=params) as response:
                if response.status == 404:
                    raise Exception(f"File không tồn tại: {path}")
                elif response.status == 403:
                    raise Exception("Không có quyền truy cập repository!")
                elif response.status != 200:
                    raise Exception(f"Lỗi GitHub API: {response.status}")
                
                data = await response.json()
                
                # Nếu là file
                if data.get('type') == 'file':
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content, data['name'], data['size']
                # Nếu là folder
                elif isinstance(data, list):
                    return None, None, None  # Folder listing
                else:
                    raise Exception("Không thể xác định loại file/folder")
    
    async def _save_file_locally(self, content, filename, target_folder=None):
        """Lưu file vào local với backup file cũ nếu trùng tên"""
        try:
            # Xác định thư mục đích
            if target_folder:
                save_path = os.path.join(target_folder, filename)
                os.makedirs(target_folder, exist_ok=True)
            else:
                # Mặc định lưu trong thư mục bot
                bot_dir = os.path.dirname(os.path.dirname(__file__))
                save_path = os.path.join(bot_dir, filename)
            
            # Backup file cũ nếu tồn tại
            if os.path.exists(save_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{save_path}.backup_{timestamp}"
                os.rename(save_path, backup_path)
                logger.info(f"Backed up existing file to: {backup_path}")
            
            # Lưu file mới
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return save_path
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise Exception(f"Lỗi khi lưu file: {str(e)}")
    
    async def download_file_command(self, ctx, github_url: str, target_folder: str = None):
        """
        Download file từ GitHub private repository
        
        Args:
            ctx: Discord context
            github_url: URL của file trên GitHub
            target_folder: Thư mục đích (optional)
        """
        try:
            # Parse GitHub URL
            owner, repo, branch, path = self._parse_github_url(github_url)
            
            if not owner or not repo:
                await ctx.reply("❌ URL GitHub không hợp lệ!")
                return
            
            # Tạo embed thông báo đang download
            embed = discord.Embed(
                title="📥 Đang tải file từ GitHub...",
                description=f"**Repository:** {owner}/{repo}\n**Branch:** {branch}\n**File:** {path}",
                color=discord.Color.blue()
            )
            
            status_msg = await ctx.reply(embed=embed)
            
            # Download file
            content, filename, file_size = await self._download_file_from_github(owner, repo, path, branch)
            
            if content is None:
                embed.color = discord.Color.red()
                embed.title = "❌ Lỗi tải file"
                embed.description = "Đường dẫn này là thư mục, không phải file!"
                await status_msg.edit(embed=embed)
                return
            
            # Lưu file
            saved_path = await self._save_file_locally(content, filename, target_folder)
            
            # Cập nhật embed thành công
            embed.color = discord.Color.green()
            embed.title = "✅ Tải file thành công!"
            embed.description = f"**File:** {filename}\n**Kích thước:** {file_size:,} bytes\n**Lưu tại:** `{saved_path}`"
            
            embed.add_field(
                name="📊 Thông tin chi tiết:",
                value=(
                    f"**Repository:** {owner}/{repo}\n"
                    f"**Branch:** {branch}\n"
                    f"**Đường dẫn GitHub:** {path}\n"
                    f"**Thời gian:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                inline=False
            )
            
            await status_msg.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in download_file_command: {e}")
            
            # Cập nhật embed lỗi
            embed = discord.Embed(
                title="❌ Lỗi tải file",
                description=f"**Lỗi:** {str(e)}",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="💡 Gợi ý:",
                value=(
                    "• Kiểm tra URL GitHub có đúng không\n"
                    "• Đảm bảo GitHub token được cấu hình\n"
                    "• Kiểm tra quyền truy cập repository\n"
                    "• File có tồn tại trên branch đó không"
                ),
                inline=False
            )
            
            try:
                await status_msg.edit(embed=embed)
            except:
                await ctx.reply(embed=embed)
    
    async def list_repo_files_command(self, ctx, github_url: str, folder_path: str = ""):
        """
        Liệt kê files trong repository hoặc folder
        
        Args:
            ctx: Discord context  
            github_url: URL repository GitHub
            folder_path: Đường dẫn folder (optional)
        """
        try:
            owner, repo, branch, _ = self._parse_github_url(github_url)
            
            if not owner or not repo:
                await ctx.reply("❌ URL GitHub không hợp lệ!")
                return
            
            token = self._get_github_token()
            if not token:
                await ctx.reply("❌ GitHub token không được cấu hình!")
                return
            
            # API URL
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{folder_path}"
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            params = {'ref': branch} if branch != 'main' else {}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, params=params) as response:
                    if response.status != 200:
                        await ctx.reply(f"❌ Lỗi API: {response.status}")
                        return
                    
                    files_data = await response.json()
            
            # Tạo embed hiển thị files
            embed = discord.Embed(
                title=f"📁 Files trong {owner}/{repo}",
                description=f"**Folder:** `{folder_path or 'root'}`\n**Branch:** {branch}",
                color=discord.Color.blue()
            )
            
            files = []
            folders = []
            
            for item in files_data:
                if item['type'] == 'file':
                    size_kb = item['size'] / 1024
                    files.append(f"📄 `{item['name']}` ({size_kb:.1f} KB)")
                elif item['type'] == 'dir':
                    folders.append(f"📁 `{item['name']}/`")
            
            if folders:
                embed.add_field(
                    name="📁 Thư mục:",
                    value='\n'.join(folders[:10]),  # Giới hạn 10 items
                    inline=False
                )
            
            if files:
                embed.add_field(
                    name="📄 Files:",
                    value='\n'.join(files[:15]),  # Giới hạn 15 items
                    inline=False
                )
            
            if not files and not folders:
                embed.add_field(
                    name="📭 Trống",
                    value="Không có file hoặc thư mục nào",
                    inline=False
                )
            
            embed.add_field(
                name="💡 Sử dụng:",
                value=f"; <github_url>` để tải file cụ thể",
                inline=False
            )
            
            await ctx.reply(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in list_repo_files_command: {e}")
            await ctx.reply(f"❌ Lỗi: {str(e)}")

    def register_commands(self):
        """Đăng ký commands với bot"""
        
        @self.bot.bot.command(name='downloadfile', aliases=['dlfile', 'gitdownload'])
        async def download_file(ctx, github_url: str, target_folder: str = None):
            """
            Tải file từ GitHub private repository
            
            Usage:
                ;downloadfile <github_url> [target_folder]
                
            Examples:
                ;downloadfile https://github.com/user/repo/blob/main/config.json
                ;downloadfile https://github.com/user/repo/blob/main/data.json ./downloads
            """
            await self.download_file_command(ctx, github_url, target_folder)
        
        @self.bot.bot.command(name='listfiles', aliases=['lsfiles', 'gitls'])
        async def list_files(ctx, github_url: str, folder_path: str = ""):
            """
            Liệt kê files trong GitHub repository
            
            Usage:
                ;listfiles <github_url> [folder_path]
                
            Examples:
                ;listfiles https://github.com/user/repo
                ;listfiles https://github.com/user/repo/tree/main/data
            """
            await self.list_repo_files_command(ctx, github_url, folder_path)

def setup(bot):
    """Setup function để load commands (backward compatibility)"""
    github_cmd = GitHubDownloadCommands(bot)
    github_cmd.register_commands()
