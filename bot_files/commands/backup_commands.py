"""
Backup Commands - Hệ thống sao lưu và đồng bộ dữ liệu từ GitHub
Lệnh: ;backup sync, ;backup pull, ;backup status
"""
import discord
from discord.ext import commands
import json
import os
import logging
import asyncio
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BackupCommands:
    def __init__(self, bot_instance):
        """
        Khởi tạo Backup Commands
        
        Args:
            bot_instance: Instance của AutoReplyBotRefactored
        """
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        
        # Cấu hình GitHub
        self.github_config_file = 'config_github.json'
        self.github_config = self.load_github_config()
        
        # Tạo folder data nếu chưa có
        self.data_folder = 'data'
        self.ensure_data_folder()
        
        logger.info("Backup Commands đã được khởi tạo")
    
    def ensure_data_folder(self):
        """Tạo folder data và di chuyển các file dữ liệu vào đó"""
        try:
            # Tạo folder data nếu chưa có
            if not os.path.exists(self.data_folder):
                os.makedirs(self.data_folder)
                logger.info(f"Đã tạo folder {self.data_folder}")
            
            # Danh sách files cần di chuyển vào data folder
            files_to_move = [
                'shared_wallet.json',
                'taixiu_data.json', 
                'api-gemini.json',
                'config.json',
                'admin.json',
                'warnings.json',
                'priority.json',
                'supreme_admin.json',
                'auto_delete_config.json',
                'fire_delete_config.json',
                'afk_data.json',
                'banned_users.json'
            ]
            
            moved_files = []
            for file in files_to_move:
                # Kiểm tra file tồn tại ở root
                if os.path.exists(file):
                    data_file_path = os.path.join(self.data_folder, file)
                    # Chỉ di chuyển nếu chưa có trong data folder
                    if not os.path.exists(data_file_path):
                        try:
                            shutil.move(file, data_file_path)
                            moved_files.append(file)
                            logger.info(f"Đã di chuyển {file} vào {self.data_folder}/")
                        except Exception as e:
                            logger.error(f"Lỗi khi di chuyển {file}: {e}")
            
            if moved_files:
                logger.info(f"Đã di chuyển {len(moved_files)} files vào data folder")
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo data folder: {e}")
    
    def get_data_file_path(self, filename: str) -> str:
        """Lấy đường dẫn file trong data folder"""
        return os.path.join(self.data_folder, filename)
    
    def migrate_existing_data(self):
        """Di chuyển dữ liệu hiện có vào data folder"""
        try:
            # Tạo backup trước khi di chuyển
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            migration_backup = f"migration_backup_{timestamp}"
            
            if not os.path.exists('data_backups'):
                os.makedirs('data_backups')
            
            backup_path = os.path.join('data_backups', migration_backup)
            os.makedirs(backup_path, exist_ok=True)
            
            # Files cần migrate
            files_to_migrate = [
                'shared_wallet.json',
                'taixiu_data.json', 
                'api-gemini.json',
                'config.json',
                'admin.json',
                'warnings.json',
                'priority.json',
                'supreme_admin.json',
                'auto_delete_config.json',
                'fire_delete_config.json',
                'afk_data.json',
                'banned_users.json'
            ]
            
            migrated_files = []
            for file in files_to_migrate:
                if os.path.exists(file):
                    try:
                        # Backup file gốc
                        shutil.copy2(file, backup_path)
                        
                        # Di chuyển vào data folder
                        data_file_path = self.get_data_file_path(file)
                        if not os.path.exists(data_file_path):
                            shutil.move(file, data_file_path)
                            migrated_files.append(file)
                        else:
                            # Nếu đã có trong data, xóa file gốc
                            os.remove(file)
                            
                    except Exception as e:
                        logger.error(f"Lỗi migrate {file}: {e}")
            
            if migrated_files:
                logger.info(f"Migration hoàn tất: {len(migrated_files)} files -> data/")
                return migration_backup
            
            return None
            
        except Exception as e:
            logger.error(f"Lỗi trong migration: {e}")
            return None
    
    def load_github_config(self) -> Dict:
        """
        Tải cấu hình GitHub từ file JSON
        
        Returns:
            Dict: Cấu hình GitHub
        """
        try:
            if os.path.exists(self.github_config_file):
                with open(self.github_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Đã tải cấu hình GitHub")
                return config
            else:
                # Tạo config mặc định
                default_config = {
                    "repository_url": "https://github.com/username/bot_discord.git",
                    "branch": "main",
                    "data_files": [
                        "data/shared_wallet.json",
                        "data/taixiu_data.json", 
                        "data/api-gemini.json",
                        "data/config.json",
                        "data/admin.json",
                        "data/warnings.json",
                        "data/priority.json",
                        "data/supreme_admin.json",
                        "data/auto_delete_config.json",
                        "data/fire_delete_config.json",
                        "data/afk_data.json",
                        "data/banned_users.json"
                    ],
                    "backup_enabled": True,
                    "auto_backup_before_pull": True,
                    "data_folder": "data"
                }
                
                with open(self.github_config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                
                logger.info("Đã tạo cấu hình GitHub mặc định")
                return default_config
        except Exception as e:
            logger.error(f"Lỗi khi tải cấu hình GitHub: {e}")
            return {}
    
    def is_admin(self, user_id: int, guild_permissions) -> bool:
        """
        Kiểm tra xem user có phải admin không
        
        Args:
            user_id: ID của người dùng
            guild_permissions: Quyền trong guild
            
        Returns:
            bool: True nếu là admin
        """
        return self.bot_instance.has_warn_permission(user_id, guild_permissions)
    
    async def run_git_command(self, command: str, cwd: str = None) -> tuple:
        """
        Chạy lệnh git và trả về kết quả
        
        Args:
            command: Lệnh git cần chạy
            cwd: Thư mục làm việc
            
        Returns:
            tuple: (success, output, error)
        """
        try:
            if cwd is None:
                cwd = os.getcwd()
            
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            output = stdout.decode('utf-8', errors='ignore').strip()
            error = stderr.decode('utf-8', errors='ignore').strip()
            
            return success, output, error
            
        except Exception as e:
            logger.error(f"Lỗi khi chạy git command '{command}': {e}")
            return False, "", str(e)
    
    def backup_current_data(self) -> str:
        """
        Sao lưu dữ liệu hiện tại trước khi pull
        
        Returns:
            str: Tên file backup
        """
        try:
            # Tạo thư mục backup
            backup_dir = 'data_backups'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Tạo tên backup với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pre_pull_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy các file data quan trọng
            data_files = self.github_config.get('data_files', [])
            backed_up_files = []
            
            for file in data_files:
                if os.path.exists(file):
                    try:
                        shutil.copy2(file, backup_path)
                        backed_up_files.append(file)
                        logger.info(f"Backed up: {file}")
                    except Exception as e:
                        logger.error(f"Lỗi backup file {file}: {e}")
            
            # Tạo backup info
            backup_info = {
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'type': 'pre_pull_backup',
                'files_backed_up': backed_up_files,
                'total_files': len(backed_up_files)
            }
            
            info_file = os.path.join(backup_path, 'backup_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Backup hoàn tất: {backup_name}")
            return backup_name
            
        except Exception as e:
            logger.error(f"Lỗi khi backup dữ liệu: {e}")
            return ""
    
    async def check_git_repository(self) -> tuple:
        """
        Kiểm tra xem thư mục hiện tại có phải Git repository không
        
        Returns:
            tuple: (is_git_repo, error_message)
        """
        try:
            success, output, error = await self.run_git_command("git rev-parse --git-dir")
            return success, error if not success else ""
        except Exception as e:
            return False, str(e)
    
    async def handle_restore(self, ctx):
        """Xử lý lệnh restore từ GitHub"""
        # Kiểm tra Git repository trước
        is_git_repo, git_error = await self.check_git_repository()
        
        if not is_git_repo:
            embed = discord.Embed(
                title="❌ Không phải Git Repository",
                description="Thư mục hiện tại không phải là một Git repository!",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🐛 Chi tiết lỗi",
                value=f"```\n{git_error}\n```",
                inline=False
            )
            
            embed.add_field(
                name="💡 Cách khắc phục",
                value="**Bước 1**: Khởi tạo Git repository\n"
                      "```bash\ngit init\n```\n\n"
                      "**Bước 2**: Thêm remote repository\n"
                      "```bash\ngit remote add origin <URL_REPOSITORY>\n```\n\n"
                      "**Bước 3**: Pull code lần đầu\n"
                      "```bash\ngit pull origin main\n```",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Cấu hình repository",
                value=f"Cập nhật URL trong `{self.github_config_file}`:\n"
                      f"```json\n{{\n"
                      f'  "repository_url": "https://github.com/username/repo.git"\n'
                      f"}}\n```",
                inline=False
            )
            
            embed.set_footer(text="Sau khi thiết lập Git, hãy thử lại lệnh backup restore")
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        embed = discord.Embed(
            title="🔄 Đang khôi phục từ GitHub...",
            description="Vui lòng chờ trong giây lát...",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📦 Bước 1/4",
            value="Đang backup dữ liệu hiện tại...",
            inline=False
        )
        
        message = await ctx.reply(embed=embed, mention_author=True)
        
        backup_name = ""
        
        try:
            # Bước 1: Backup dữ liệu hiện tại
            backup_name = self.backup_current_data()
            
            embed.add_field(
                name="✅ Backup hoàn tất",
                value=f"Đã backup: `{backup_name}`",
                inline=False
            )
            embed.add_field(
                name="🔄 Bước 2/4",
                value="Đang reset working directory...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            # Bước 2: Reset working directory (discard local changes)
            # Kiểm tra xem có commit nào không trước khi reset
            has_commits, _, _ = await self.run_git_command("git rev-parse --verify HEAD")
            
            if has_commits:
                success, output, error = await self.run_git_command("git reset --hard HEAD")
                if not success:
                    raise Exception(f"Git reset failed: {error}")
            else:
                # Nếu chưa có commit, chỉ clean working directory
                success, output, error = await self.run_git_command("git clean -fd")
                if not success:
                    logger.warning(f"Git clean warning: {error}")  # Clean có thể fail nếu không có gì để clean
            
            embed.add_field(
                name="✅ Reset hoàn tất",
                value="Đã reset working directory",
                inline=False
            )
            embed.add_field(
                name="📥 Bước 3/4",
                value="Đang pull từ GitHub...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            # Bước 3: Force pull từ GitHub
            success, output, error = await self.run_git_command("git pull origin main --force")
            
            if not success:
                raise Exception(f"Git pull failed: {error}")
            
            embed.add_field(
                name="✅ Pull hoàn tất",
                value="Đã tải code mới từ GitHub",
                inline=False
            )
            embed.add_field(
                name="📁 Bước 4/4",
                value="Đang khôi phục data files...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            # Bước 4: Khôi phục data files từ GitHub (nếu có)
            data_files = self.github_config.get('data_files', [])
            restored_files = []
            missing_files = []
            
            for file in data_files:
                if os.path.exists(file):
                    # File tồn tại trên GitHub, đã được pull
                    restored_files.append(file)
                else:
                    missing_files.append(file)
            
            # Tạo embed kết quả cuối cùng
            embed = discord.Embed(
                title="✅ Khôi phục từ GitHub thành công!",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            if backup_name:
                embed.add_field(
                    name="📦 Backup an toàn",
                    value=f"Dữ liệu cũ đã được backup: `{backup_name}`",
                    inline=False
                )
            
            if restored_files:
                files_text = '\n'.join([f"• `{file}`" for file in restored_files[:10]])
                if len(restored_files) > 10:
                    files_text += f"\n... và {len(restored_files) - 10} file khác"
                
                embed.add_field(
                    name="📁 Files đã khôi phục",
                    value=files_text,
                    inline=False
                )
            
            if missing_files:
                files_text = '\n'.join([f"• `{file}`" for file in missing_files[:5]])
                if len(missing_files) > 5:
                    files_text += f"\n... và {len(missing_files) - 5} file khác"
                
                embed.add_field(
                    name="⚠️ Files không tìm thấy trên GitHub",
                    value=files_text,
                    inline=False
                )
            
            embed.add_field(
                name="🔄 Bước tiếp theo",
                value="Khởi động lại bot để áp dụng thay đổi (nếu cần)",
                inline=False
            )
            
            embed.add_field(
                name="💡 Lưu ý",
                value="• Tất cả thay đổi local đã bị ghi đè\n"
                      "• Dữ liệu cũ đã được backup an toàn\n"
                      "• Bot hiện đang chạy code từ GitHub",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Lỗi trong handle_restore: {e}")
            
            embed = discord.Embed(
                title="❌ Lỗi khi khôi phục từ GitHub",
                description="Có lỗi xảy ra trong quá trình khôi phục!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="🐛 Chi tiết",
                value=f"```\n{str(e)}\n```",
                inline=False
            )
            
            if backup_name:
                embed.add_field(
                    name="📦 Backup an toàn",
                    value=f"Dữ liệu đã được backup: `{backup_name}`",
                    inline=False
                )
            
            embed.add_field(
                name="💡 Gợi ý khắc phục",
                value="• Kiểm tra kết nối mạng\n"
                      "• Kiểm tra quyền truy cập GitHub\n"
                      "• Thử lại với `backup status` trước\n"
                      "• Liên hệ admin nếu cần hỗ trợ",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
    
    async def handle_init(self, ctx):
        """Xử lý lệnh init - khởi tạo Git repository"""
        embed = discord.Embed(
            title="🔧 Đang khởi tạo Git Repository...",
            description="Thiết lập Git repository và kết nối với GitHub",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📦 Bước 1/3",
            value="Đang khởi tạo Git repository...",
            inline=False
        )
        
        message = await ctx.reply(embed=embed, mention_author=True)
        
        try:
            # Bước 1: Git init
            success, output, error = await self.run_git_command("git init")
            
            if not success:
                raise Exception(f"Git init failed: {error}")
            
            embed.add_field(
                name="✅ Git init hoàn tất",
                value="Đã khởi tạo Git repository",
                inline=False
            )
            embed.add_field(
                name="🔗 Bước 2/3",
                value="Đang thêm remote repository...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            # Bước 2: Thêm remote origin
            repo_url = self.github_config.get('repository_url', '')
            if not repo_url or repo_url == "https://github.com/username/bot_discord.git":
                embed = discord.Embed(
                    title="⚠️ Cần cấu hình Repository URL",
                    description="Vui lòng cập nhật URL repository trong cấu hình",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="✅ Git init thành công",
                    value="Repository đã được khởi tạo",
                    inline=False
                )
                
                embed.add_field(
                    name="⚙️ Cần cấu hình",
                    value=f"Cập nhật `{self.github_config_file}`:\n"
                          f"```json\n{{\n"
                          f'  "repository_url": "https://github.com/your-username/your-repo.git"\n'
                          f"}}\n```",
                    inline=False
                )
                
                embed.add_field(
                    name="🔄 Bước tiếp theo",
                    value="Sau khi cập nhật URL, chạy lại `backup init`",
                    inline=False
                )
                
                try:
                    await message.edit(embed=embed)
                except:
                    await ctx.send(embed=embed)
                return
            
            # Xóa remote cũ nếu có
            await self.run_git_command("git remote remove origin")
            
            # Thêm remote mới
            success, output, error = await self.run_git_command(f"git remote add origin {repo_url}")
            
            if not success:
                raise Exception(f"Add remote failed: {error}")
            
            embed.add_field(
                name="✅ Remote added",
                value=f"Đã kết nối với: `{repo_url}`",
                inline=False
            )
            embed.add_field(
                name="📥 Bước 3/3",
                value="Đang pull code từ GitHub...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            # Bước 3: Pull code lần đầu (xử lý conflict)
            branch = self.github_config.get('branch', 'main')
            
            # Thử pull bình thường trước
            success, output, error = await self.run_git_command(f"git pull origin {branch}")
            
            # Nếu có conflict về untracked files, xử lý tự động
            if not success and "untracked working tree files would be overwritten" in error:
                embed.add_field(
                    name="⚠️ Phát hiện conflict",
                    value="Đang xử lý conflict với GitHub files...",
                    inline=False
                )
                
                try:
                    await message.edit(embed=embed)
                except:
                    pass
                
                # Stash các thay đổi local
                await self.run_git_command("git add .")
                await self.run_git_command("git stash")
                
                # Pull lại
                success, output, error = await self.run_git_command(f"git pull origin {branch}")
                
                # Nếu vẫn lỗi, thử force pull
                if not success:
                    success, output, error = await self.run_git_command(f"git pull origin {branch} --allow-unrelated-histories")
            
            if success:
                # Thành công
                embed = discord.Embed(
                    title="✅ Khởi tạo Git Repository thành công!",
                    description="Repository đã được thiết lập và đồng bộ với GitHub",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🔗 Repository",
                    value=f"`{repo_url}`",
                    inline=False
                )
                
                embed.add_field(
                    name="🌿 Branch",
                    value=f"`{branch}`",
                    inline=True
                )
                
                embed.add_field(
                    name="🎉 Hoàn tất",
                    value="Giờ bạn có thể sử dụng:\n"
                          "• `backup status` - Kiểm tra trạng thái\n"
                          "• `backup sync` - Đồng bộ từ GitHub\n"
                          "• `backup restore` - Khôi phục từ GitHub",
                    inline=False
                )
                
            else:
                # Pull thất bại nhưng Git đã được init
                embed = discord.Embed(
                    title="⚠️ Git Repository đã khởi tạo",
                    description="Repository đã được thiết lập nhưng không thể pull code",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="✅ Đã hoàn thành",
                    value="• Git repository đã được khởi tạo\n"
                          f"• Remote origin đã được thêm: `{repo_url}`",
                    inline=False
                )
                
                embed.add_field(
                    name="⚠️ Lỗi pull",
                    value=f"```\n{error[:300]}\n```",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Gợi ý",
                    value="• Repository có thể trống\n"
                          "• Thử tạo commit đầu tiên trên GitHub",
                    inline=False
                )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Lỗi trong handle_init: {e}")
            
            embed = discord.Embed(
                title="❌ Lỗi khi khởi tạo Git Repository",
                description="Có lỗi xảy ra trong quá trình khởi tạo!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="🐛 Chi tiết",
                value=f"```\n{str(e)}\n```",
                inline=False
            )
            
            embed.add_field(
                name="💡 Gợi ý khắc phục",
                value="• Kiểm tra quyền ghi trong thư mục\n"
                      "• Đảm bảo Git đã được cài đặt\n"
                      "• Kiểm tra URL repository trong config",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
    
    async def handle_status(self, ctx):
        """Xử lý lệnh status"""
        # Kiểm tra Git repository trước
        is_git_repo, git_error = await self.check_git_repository()
        
        if not is_git_repo:
            embed = discord.Embed(
                title="❌ Không phải Git Repository",
                description="Thư mục hiện tại không phải là một Git repository!",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🐛 Lỗi",
                value=f"```\n{git_error}\n```",
                inline=False
            )
            embed.add_field(
                name="💡 Hướng dẫn",
                value="Sử dụng `backup init` để khởi tạo repository",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        embed = discord.Embed(
            title="📊 Trạng thái Git Repository",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Kiểm tra git status
        success, output, error = await self.run_git_command("git status --porcelain")
        
        if success:
            if output:
                # Có thay đổi
                embed.add_field(
                    name="📝 Thay đổi chưa commit",
                    value=f"```\n{output[:1000]}\n```",
                    inline=False
                )
                embed.color = discord.Color.orange()
            else:
                embed.add_field(
                    name="✅ Working tree clean",
                    value="Không có thay đổi chưa commit",
                    inline=False
                )
        else:
            embed.add_field(
                name="❌ Lỗi Git",
                value=f"```\n{error}\n```",
                inline=False
            )
            embed.color = discord.Color.red()
        
        # Kiểm tra branch hiện tại
        success, branch, error = await self.run_git_command("git branch --show-current")
        if success:
            embed.add_field(
                name="🌿 Branch hiện tại",
                value=f"`{branch}`",
                inline=True
            )
        
        # Kiểm tra remote status
        success, remote_info, error = await self.run_git_command("git remote -v")
        if success and remote_info:
            lines = remote_info.split('\n')
            origin_fetch = next((line for line in lines if 'origin' in line and 'fetch' in line), '')
            if origin_fetch:
                repo_url = origin_fetch.split()[1]
                embed.add_field(
                    name="🔗 Remote Repository",
                    value=f"`{repo_url}`",
                    inline=False
                )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def handle_config(self, ctx):
        """Xử lý lệnh config"""
        embed = discord.Embed(
            title="⚙️ Cấu hình GitHub Backup",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        config = self.github_config
        
        embed.add_field(
            name="🔗 Repository URL",
            value=f"`{config.get('repository_url', 'Chưa cấu hình')}`",
            inline=False
        )
        
        embed.add_field(
            name="🌿 Branch",
            value=f"`{config.get('branch', 'main')}`",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Auto Backup",
            value="✅ Bật" if config.get('auto_backup_before_pull', True) else "❌ Tắt",
            inline=True
        )
        
        data_files = config.get('data_files', [])
        if data_files:
            files_text = '\n'.join([f"• `{file}`" for file in data_files[:10]])
            if len(data_files) > 10:
                files_text += f"\n... và {len(data_files) - 10} file khác"
            
            embed.add_field(
                name="📁 Files được backup",
                value=files_text,
                inline=False
            )
        
        embed.add_field(
            name="📝 File cấu hình",
            value=f"`{self.github_config_file}`",
            inline=True
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def handle_pull(self, ctx, backup_first: bool = True):
        """Xử lý lệnh pull/sync"""
        # Kiểm tra Git repository trước
        is_git_repo, git_error = await self.check_git_repository()
        
        if not is_git_repo:
            embed = discord.Embed(
                title="❌ Không phải Git Repository",
                description="Thư mục hiện tại không phải là một Git repository!",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🐛 Lỗi",
                value=f"```\n{git_error}\n```",
                inline=False
            )
            embed.add_field(
                name="💡 Hướng dẫn",
                value="Sử dụng `backup init` để khởi tạo repository",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Tạo embed loading
        embed = discord.Embed(
            title="🔄 Đang đồng bộ từ GitHub...",
            description="Vui lòng chờ trong giây lát...",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        if backup_first:
            embed.add_field(
                name="📦 Bước 1/3",
                value="Đang backup dữ liệu hiện tại...",
                inline=False
            )
        else:
            embed.add_field(
                name="📥 Bước 1/2",
                value="Đang pull từ GitHub...",
                inline=False
            )
        
        message = await ctx.reply(embed=embed, mention_author=True)
        
        backup_name = ""
        
        try:
            # Bước 1: Backup nếu cần
            if backup_first:
                backup_name = self.backup_current_data()
                
                embed.add_field(
                    name="✅ Backup hoàn tất",
                    value=f"Đã backup: `{backup_name}`",
                    inline=False
                )
                embed.add_field(
                    name="📥 Bước 2/3",
                    value="Đang pull từ GitHub...",
                    inline=False
                )
                
                try:
                    await message.edit(embed=embed)
                except:
                    pass
            
            # Bước 2: Git pull
            success, output, error = await self.run_git_command("git pull origin main")
            
            if success:
                # Thành công
                embed = discord.Embed(
                    title="✅ Đồng bộ GitHub thành công!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                if backup_name:
                    embed.add_field(
                        name="📦 Backup",
                        value=f"Dữ liệu cũ đã được backup: `{backup_name}`",
                        inline=False
                    )
                
                if output:
                    # Hiển thị thông tin pull
                    pull_info = output[:500] + "..." if len(output) > 500 else output
                    embed.add_field(
                        name="📥 Kết quả Pull",
                        value=f"```\n{pull_info}\n```",
                        inline=False
                    )
                
                embed.add_field(
                    name="🔄 Bước tiếp theo",
                    value="Khởi động lại bot để áp dụng thay đổi (nếu cần)",
                    inline=False
                )
                
            else:
                # Thất bại
                embed = discord.Embed(
                    title="❌ Lỗi khi pull từ GitHub",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🐛 Chi tiết lỗi",
                    value=f"```\n{error[:1000]}\n```",
                    inline=False
                )
                
                if backup_name:
                    embed.add_field(
                        name="📦 Backup an toàn",
                        value=f"Dữ liệu của bạn đã được backup: `{backup_name}`",
                        inline=False
                    )
                
                embed.add_field(
                    name="💡 Gợi ý",
                    value="• Kiểm tra `git status` để xem conflict\n"
                          "• Có thể cần resolve conflict thủ công\n"
                          "• Liên hệ admin nếu cần hỗ trợ",
                    inline=False
                )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Lỗi trong handle_pull: {e}")
            
            embed = discord.Embed(
                title="❌ Lỗi hệ thống",
                description="Có lỗi xảy ra trong quá trình đồng bộ!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="🐛 Chi tiết",
                value=f"```\n{str(e)}\n```",
                inline=False
            )
            
            if backup_name:
                embed.add_field(
                    name="📦 Backup an toàn",
                    value=f"Dữ liệu đã được backup: `{backup_name}`",
                    inline=False
                )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
    
    async def handle_fix_conflict(self, ctx):
        """Xử lý conflict với GitHub files"""
        embed = discord.Embed(
            title="🔧 Đang xử lý Git Conflict...",
            description="Khắc phục conflict với files từ GitHub",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🔍 Bước 1/4",
            value="Đang kiểm tra trạng thái Git...",
            inline=False
        )
        
        message = await ctx.reply(embed=embed, mention_author=True)
        
        try:
            # Kiểm tra Git repository
            is_git_repo, git_error = await self.check_git_repository()
            
            if not is_git_repo:
                embed = discord.Embed(
                    title="❌ Không phải Git Repository",
                    description="Vui lòng chạy `backup init` trước!",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
                return
            
            # Bước 1: Backup files hiện tại
            embed.add_field(
                name="📦 Bước 2/4",
                value="Đang backup files conflict...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            # Tạo backup folder cho conflict files
            conflict_backup_dir = f"conflict_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Kiểm tra files conflict phổ biến
            conflict_files = ["README.md", ".gitignore", "LICENSE"]
            backed_up_files = []
            
            for file in conflict_files:
                if os.path.exists(file):
                    if not os.path.exists(conflict_backup_dir):
                        os.makedirs(conflict_backup_dir)
                    try:
                        import shutil
                        shutil.copy2(file, conflict_backup_dir)
                        backed_up_files.append(file)
                    except Exception as e:
                        logger.error(f"Lỗi backup {file}: {e}")
            
            # Bước 2: Xóa conflict files
            embed.add_field(
                name="🗑️ Bước 3/4",
                value="Đang xóa conflict files...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            removed_files = []
            for file in conflict_files:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                        removed_files.append(file)
                    except Exception as e:
                        logger.error(f"Lỗi xóa {file}: {e}")
            
            # Bước 3: Pull từ GitHub
            embed.add_field(
                name="📥 Bước 4/4",
                value="Đang pull từ GitHub...",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                pass
            
            branch = self.github_config.get('branch', 'main')
            success, output, error = await self.run_git_command(f"git pull origin {branch}")
            
            # Nếu vẫn lỗi, thử với --allow-unrelated-histories
            if not success:
                success, output, error = await self.run_git_command(f"git pull origin {branch} --allow-unrelated-histories")
            
            # Tạo embed kết quả
            if success:
                embed = discord.Embed(
                    title="✅ Đã khắc phục Git Conflict!",
                    description="Conflict đã được giải quyết thành công",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                if backed_up_files:
                    embed.add_field(
                        name="📦 Files đã backup",
                        value=f"Backup tại: `{conflict_backup_dir}`\n" +
                              "\n".join([f"• `{file}`" for file in backed_up_files]),
                        inline=False
                    )
                
                if removed_files:
                    embed.add_field(
                        name="🗑️ Files đã xóa",
                        value="\n".join([f"• `{file}`" for file in removed_files]),
                        inline=False
                    )
                
                embed.add_field(
                    name="📥 Pull result",
                    value=f"```\n{output[:300] if output else 'Pull thành công'}\n```",
                    inline=False
                )
                
                embed.add_field(
                    name="🎉 Hoàn tất",
                    value="Giờ bạn có thể sử dụng:\n"
                          "• `backup status` - Kiểm tra trạng thái\n"
                          "• `backup sync` - Đồng bộ từ GitHub",
                    inline=False
                )
                
            else:
                embed = discord.Embed(
                    title="❌ Vẫn còn lỗi Git",
                    description="Không thể khắc phục conflict tự động",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🐛 Lỗi",
                    value=f"```\n{error[:500]}\n```",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Khắc phục thủ công",
                    value="```bash\n"
                          "git add .\n"
                          "git stash\n"
                          "git pull origin main --allow-unrelated-histories\n"
                          "```",
                    inline=False
                )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Lỗi trong handle_fix_conflict: {e}")
            
            embed = discord.Embed(
                title="❌ Lỗi khi xử lý conflict",
                description="Có lỗi xảy ra trong quá trình khắc phục!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="🐛 Chi tiết",
                value=f"```\n{str(e)}\n```",
                inline=False
            )
            
            try:
                await message.edit(embed=embed)
            except:
                await ctx.send(embed=embed)
    
    def register_commands(self) -> None:
        """
        Đăng ký các commands cho Backup
        """
        @self.bot.command(name='backup')
        async def backup_command(ctx, action: str = None):
            """
            Lệnh quản lý backup và đồng bộ GitHub
            
            Usage: 
            - ;backup sync - Đồng bộ từ GitHub (pull + merge)
            - ;backup pull - Tải code mới từ GitHub
            - ;backup restore - Khôi phục hoàn toàn từ GitHub (ghi đè local)
            - ;backup status - Kiểm tra trạng thái Git
            - ;backup config - Xem cấu hình GitHub
            """
            try:
                # Kiểm tra quyền admin
                if not self.is_admin(ctx.author.id, ctx.author.guild_permissions):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ admin mới có thể sử dụng lệnh backup!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                if not action:
                    # Hiển thị hướng dẫn
                    embed = discord.Embed(
                        title="🔄 Hệ thống Backup & Sync GitHub",
                        description="Quản lý sao lưu và đồng bộ dữ liệu từ GitHub",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📝 Các lệnh có sẵn",
                        value="`/backup sync` - Đồng bộ từ GitHub (an toàn)\n"
                              "`/backup pull` - Tải code mới từ GitHub\n"
                              "`/backup restore` - Khôi phục dữ liệu từ GitHub\n"
                              "`/backup init` - Khởi tạo Git repository\n"
                              "`/backup fix` - Khắc phục Git conflict\n"
                              "`/backup migrate` - Di chuyển dữ liệu vào data/\n"
                              "`/backup status` - Kiểm tra trạng thái Git\n"
                              "`/backup config` - Xem cấu hình GitHub",
                        inline=False
                    )
                    embed.add_field(
                        name="⚠️ Lưu ý",
                        value="• `sync` sẽ tự động backup dữ liệu trước khi pull\n"
                              "• `pull` chỉ tải code, không backup\n"
                              "• `restore` sẽ ghi đè TẤT CẢ thay đổi local\n"
                              "• Luôn kiểm tra `status` trước khi thực hiện",
                        inline=False
                    )
                    embed.set_footer(text="Chỉ admin mới có thể sử dụng các lệnh này")
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Xử lý các action
                if action.lower() == 'status':
                    await self.handle_status(ctx)
                elif action.lower() == 'config':
                    await self.handle_config(ctx)
                elif action.lower() == 'pull':
                    await self.handle_pull(ctx, backup_first=False)
                elif action.lower() == 'sync':
                    await self.handle_pull(ctx, backup_first=True)
                elif action.lower() == 'restore':
                    await self.handle_restore(ctx)
                elif action.lower() == 'init':
                    await self.handle_init(ctx)
                elif action.lower() == 'fix':
                    await self.handle_fix_conflict(ctx)
                elif action.lower() == 'migrate':
                    await self.handle_migrate(ctx)
                else:
                    embed = discord.Embed(
                        title="❌ Action không hợp lệ",
                        description=f"Action `{action}` không được hỗ trợ!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Actions hợp lệ",
                        value="`sync`, `pull`, `restore`, `init`, `fix`, `migrate`, `status`, `config`",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong backup command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi xử lý lệnh backup!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        
        # Các handle methods đã được định nghĩa như methods của class
        
        logger.info("Đã đăng ký backup commands")
