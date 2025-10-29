# -*- coding: utf-8 -*-
"""
Discord Auto-Reply Bot - Refactored Version
Chia thành nhiều file để dễ quản lý
"""
import discord
from discord.ext import commands
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
import os
import sys
from collections import defaultdict, deque

# Set UTF-8 encoding for stdout
sys.stdout.reconfigure(encoding='utf-8')

# Import các command classes
from bot_files.commands.warn_commands import WarnCommands
from bot_files.commands.mute_commands import MuteCommands
from bot_files.commands.ai_commands import AICommands
from bot_files.commands.admin_commands import AdminCommands
from bot_files.commands.supreme_admin_commands import SupremeAdminCommands
from bot_files.commands.info_commands import InfoCommands
from bot_files.commands.priority_commands import PriorityCommands
from bot_files.commands.network_commands import NetworkCommands
from bot_files.commands.chat_commands import ChatCommands
from bot_files.commands.taixiu_commands import TaiXiuCommands
from bot_files.commands.backup_commands import BackupCommands
from bot_files.commands.announce_commands import AnnounceCommands
from bot_files.commands.spotify_commands import SpotifyCommands
from bot_files.commands.moderation_commands import ModerationCommands
from bot_files.commands.channel_commands import ChannelCommands
from bot_files.commands.server_commands import ServerCommands
from bot_files.commands.message_commands import MessageCommands
from bot_files.commands.tiktok_commands import TikTokCommands
from bot_files.commands.github_commands import GitHubCommands
from bot_files.commands.video_commands import VideoCommands
from bot_files.commands.music_commands import MusicCommands
from bot_files.commands.feedback_commands import FeedbackCommands
from bot_files.commands.slash_commands import SlashCommands
from bot_files.commands.emoji_commands import EmojiCommands
from bot_files.commands.dm_management_commands import DMManagementCommands
from bot_files.commands.permission_commands import PermissionCommands
from bot_files.commands.channel_permission_commands import ChannelPermissionCommands
from bot_files.commands.maintenance_commands import MaintenanceCommands
from bot_files.commands.github_backup_commands import GitHubBackupCommands
from bot_files.commands.game_menu_commands import GameMenuCommands
from bot_files.commands.rps_commands import RPSCommands
from bot_files.commands.slot_commands import SlotCommands
from bot_files.commands.blackjack_commands import BlackjackCommands
from bot_files.commands.wallet_commands import WalletCommands
from bot_files.commands.wallet_reload_commands import WalletReloadCommands
from bot_files.commands.daily_commands import DailyCommands
from bot_files.commands.github_download_commands import GitHubDownloadCommands
from bot_files.commands.afk_commands import AFKCommands
from bot_files.commands.ban_commands import BanCommands
from bot_files.commands.auto_delete_commands import AutoDeleteCommands
from bot_files.commands.purge_commands import PurgeCommands
from bot_files.commands.anti_abuse_commands import AntiAbuseCommands
from bot_files.commands.multibot_commands import MultiBotCommands
from bot_files.commands.nickname_control_commands import NicknameControlCommands
from bot_files.commands.admin_nickname_protection import AdminNicknameProtection
# from bot_files.commands.fire_delete_commands import FireDeleteCommands  # DISABLED - Xóa tính năng fire delete
from bot_files.commands.channel_restrict_commands import ChannelRestrictCommands
from bot_files.commands.flip_coin_commands import FlipCoinCommands
from bot_files.commands.admin_menu_commands import AdminMenuCommands
from bot_files.commands.bye_commands import ByeCommands
# from bot_files.commands.shop_commands import ShopCommands  # Đã xóa
from bot_files.commands.unluck_commands import UnluckCommands
# from bot_files.commands.leaderboard_commands import LeaderboardCommands  # Đã xóa
from bot_files.commands.nickname_commands import NicknameCommands
from bot_files.commands.reset_commands import ResetCommands
# from bot_files.commands.getkey_commands import GetKeyCommands  # Đã xóa
from bot_files.commands.complete_menu_commands import CompleteMenuCommands
from bot_files.commands.auto_reply_commands import AutoReplyCommands
from bot_files.commands.fishing_commands import FishingCommands
from bot_files.commands.giveaway_commands import GiveawayCommands
# from bot_files.commands.full_menu_commands import FullMenuCommands  # Đã tích hợp vào game_menu_commands
# from bot_files.commands.channel_restriction_commands import ChannelRestrictionCommands  # Đã tắt

from bot_files.utils.rate_limiter import RateLimiter
from bot_files.utils.memory_manager import MemoryManager
from bot_files.utils.network_optimizer import NetworkOptimizer
from bot_files.utils.message_cache import message_cache
from bot_files.utils.shared_wallet import SharedWallet
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Chỉ hiển thị trên console
    ]
)
logger = logging.getLogger(__name__)

class AutoReplyBotRefactored:
    def __init__(self, config_file: str = 'bot_files/data/config.json'):
        """
        Khởi tạo bot auto-reply được refactor
        
        Args:
            config_file: Đường dẫn đến file cấu hình
        """
        self.config_file = config_file
        self.config = self.load_config()
        
        # Thiết lập intents tối thiểu cần thiết
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guilds = True
        intents.members = True
        intents.presences = True
        
        # Bot với connection pooling tối ưu
        self.bot = commands.Bot(
            command_prefix=';', 
            intents=intents,
            max_messages=1000,  # Giới hạn message cache để tiết kiệm RAM
            chunk_guilds_at_startup=False,  # Không load tất cả members lúc start
            help_command=None  # Disable built-in help command
        )
        
        # Optimized data structures
        self.cooldowns: Dict[int, datetime] = {}
        self.warnings: Dict[int, deque] = defaultdict(lambda: deque(maxlen=50))  # Giới hạn 50 warnings/user
        self.user_command_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1))  # 1 command per 3 seconds per user
        self.user_reply_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1))  # 1 reply per 3 seconds per user
        self.admin_ids: Set[int] = set()  # Set nhanh hơn list cho lookup O(1)
        self.priority_users: Set[int] = set()  # Users bypass rate limiting
        self.mute_tasks: Dict[int, asyncio.Task] = {}
        self.supreme_admin_id: Optional[int] = None  # Supreme Administrator tối cao
        self._command_locks: Dict[str, asyncio.Lock] = {}  # Locks to prevent duplicate command execution
        
        # Cache để giảm API calls và file I/O
        self._role_cache: Dict[int, Optional[discord.Role]] = {}  # guild_id -> muted_role
        
        # Initialize utilities với cài đặt bảo thủ hơn
        self.rate_limiter = RateLimiter(max_concurrent=2, queue_delay=45)
        self.memory_manager = MemoryManager(self)
        self.network_optimizer = NetworkOptimizer(self)
        
        # Initialize shared wallet
        self.shared_wallet = SharedWallet()
        
        # Load data
        self.load_warnings()
        self.load_admin_ids()
        self.load_priority_users()
        self.load_supreme_admin()
        
        # Setup events và commands
        try:
            logger.info("Đang setup events...")
            self.setup_events()
            logger.info("Đang setup commands...")
            self.setup_commands()
            logger.info("Setup hoàn tất")
        except Exception as e:
            logger.error(f"Lỗi trong quá trình setup: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        logger.info("Refactored bot đã được khởi tạo thành công")
    
    def load_config(self) -> dict:
        """
        Tải cấu hình từ file JSON
        
        Returns:
            dict: Cấu hình của bot
        """
        # Tạo data folder nếu chưa có
        data_folder = 'data'
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        default_config = {
            "token": "",
            "auto_reply_message": "Xin chào! Tôi hiện tại không có mặt. Tôi sẽ phản hồi bạn sớm nhất có thể. Cảm ơn bạn đã liên hệ!",
            "cooldown_seconds": 5,
            "enabled": True,
            "custom_messages": {
                "default": "Xin chào! Tôi hiện tại không có mặt. Tôi sẽ phản hồi bạn sớm nhất có thể. Cảm ơn bạn đã liên hệ!",
                "busy": "Tôi hiện đang bận. Sẽ liên hệ lại với bạn sau.",
                "away": "Tôi hiện không có mặt. Vui lòng để lại tin nhắn."
            },
            "warnings_file": "bot_files/data/warnings.json",
            "admin_file": "bot_files/data/admin.json",
            "priority_file": "bot_files/data/priority.json",
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge với default config để đảm bảo có đủ các key
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Tạo file config mới với cấu hình mặc định
                self.save_config(default_config)
                logger.info(f"Đã tạo file cấu hình mới: {self.config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Lỗi khi tải cấu hình: {e}")
            return default_config
    
    def save_config(self, config: dict = None) -> None:
        """
        Lưu cấu hình vào file JSON
        
        Args:
            config: Cấu hình cần lưu (nếu None thì lưu self.config)
        """
        try:
            config_to_save = config if config is not None else self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu cấu hình thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu cấu hình: {e}")
    
    def load_warnings(self) -> None:
        """
        Tải danh sách warnings từ file JSON với deque optimization
        """
        warnings_file = self.config.get('warnings_file', 'warnings.json')
        try:
            if os.path.exists(warnings_file):
                with open(warnings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert to deque with maxlen for memory efficiency
                    for user_id_str, warnings_list in data.items():
                        user_id = int(user_id_str)
                        # Chỉ lấy 50 warnings gần nhất
                        recent_warnings = warnings_list[-50:] if len(warnings_list) > 50 else warnings_list
                        self.warnings[user_id] = deque(recent_warnings, maxlen=50)
                logger.info(f"Đã tải {len(self.warnings)} user warnings từ {warnings_file}")
            else:
                logger.info("Không tìm thấy file warnings, khởi tạo mới")
        except Exception as e:
            logger.error(f"Lỗi khi tải warnings: {e}")
    
    def load_admin_ids(self) -> None:
        """
        Tải danh sách admin IDs từ file JSON
        """
        admin_file = self.config.get('admin_file', 'admin.json')
        try:
            if os.path.exists(admin_file):
                with open(admin_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert list to set for O(1) lookup
                    self.admin_ids = set(data.get('admin_ids', []))
                logger.info(f"Đã tải {len(self.admin_ids)} admin IDs từ {admin_file}")
            else:
                # Tạo file admin mặc định
                default_admin_data = {
                    "admin_ids": [],
                    "description": "Danh sách User IDs có quyền sử dụng lệnh warn"
                }
                with open(admin_file, 'w', encoding='utf-8') as f:
                    json.dump(default_admin_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Đã tạo file admin mới: {admin_file}")
        except Exception as e:
            logger.error(f"Lỗi khi tải admin IDs: {e}")
    
    def load_priority_users(self) -> None:
        """
        Tải danh sách priority user IDs từ file JSON
        """
        priority_file = self.config.get('priority_file', 'priority.json')
        try:
            if os.path.exists(priority_file):
                with open(priority_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert list to set for O(1) lookup
                    self.priority_users = set(data.get('priority_users', []))
                logger.info(f"Đã tải {len(self.priority_users)} priority user IDs từ {priority_file}")
            else:
                # Tạo file priority mặc định
                default_priority_data = {
                    "priority_users": [],
                    "description": "Danh sách User IDs được bypass rate limiting"
                }
                with open(priority_file, 'w', encoding='utf-8') as f:
                    json.dump(default_priority_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Đã tạo file priority mới: {priority_file}")
        except Exception as e:
            logger.error(f"Lỗi khi tải priority user IDs: {e}")
    
    def load_supreme_admin(self) -> None:
        """
        Tải Supreme Admin ID từ file JSON
        """
        supreme_file = 'bot_files/data/supreme_admin.json'
        try:
            if os.path.exists(supreme_file):
                with open(supreme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.supreme_admin_id = data.get('supreme_admin_id')
                logger.info(f"Đã tải Supreme Admin ID: {self.supreme_admin_id}")
            else:
                logger.info("Không tìm thấy file supreme admin, chưa có Supreme Admin")
                self.supreme_admin_id = None
        except Exception as e:
            logger.error(f"Lỗi khi tải Supreme Admin ID: {e}")
            self.supreme_admin_id = None
    
    def is_supreme_admin(self, user_id: int) -> bool:
        """
        Kiểm tra xem user có phải là Supreme Admin không
        """
        return self.supreme_admin_id is not None and user_id == self.supreme_admin_id
    
    def is_admin(self, user_id: int) -> bool:
        """
        Kiểm tra xem user có phải là Admin không (bao gồm Supreme Admin)
        """
        # Supreme Admin có tất cả quyền admin
        if self.is_supreme_admin(user_id):
            return True
        
        # Kiểm tra trong danh sách admin thường
        return user_id in self.admin_ids
    
    def has_supreme_permission(self, user_id: int) -> bool:
        """
        Kiểm tra quyền Supreme Admin - quyền tối cao
        """
        return self.is_supreme_admin(user_id)
    
    def is_user_rate_limited(self, user_id: int, current_time: datetime) -> bool:
        """
        Kiểm tra xem user có bị rate limit không (1 lệnh/3 giây)
        """
        # Supreme Admin và priority users bypass rate limiting
        if self.is_supreme_admin(user_id) or user_id in self.priority_users:
            return False
        
        user_history = self.user_command_history[user_id]
        
        # Xóa các lệnh cũ hơn 3 giây
        three_seconds_ago = current_time - timedelta(seconds=3)
        while user_history and user_history[0] < three_seconds_ago:
            user_history.popleft()
        
        # Kiểm tra xem đã đạt giới hạn 1 lệnh chưa
        return len(user_history) >= 1
    
    def add_user_command(self, user_id: int, current_time: datetime) -> None:
        """
        Thêm lệnh vào lịch sử của user
        """
        self.user_command_history[user_id].append(current_time)
    
    def get_rate_limit_reset_time(self, user_id: int, current_time: datetime) -> int:
        """
        Lấy thời gian còn lại để reset rate limit (giây)
        """
        user_history = self.user_command_history[user_id]
        if not user_history:
            return 0
        
        # Thời gian của lệnh cuối cùng trong cửa sổ 3 giây
        last_command = user_history[-1]
        reset_time = last_command + timedelta(seconds=3)
        remaining = reset_time - current_time
        
        return max(0, int(remaining.total_seconds()))
    
    def get_command_lock(self, command_name: str, user_id: int) -> asyncio.Lock:
        """
        Lấy lock cho command để tránh duplicate execution
        """
        lock_key = f"{command_name}_{user_id}"
        if lock_key not in self._command_locks:
            self._command_locks[lock_key] = asyncio.Lock()
        return self._command_locks[lock_key]
    
    def is_user_reply_rate_limited(self, user_id: int, current_time: datetime) -> bool:
        """
        Kiểm tra xem user có bị rate limit cho reply không (1 reply/3 giây)
        """
        # Supreme Admin và priority users bypass rate limiting
        if self.is_supreme_admin(user_id) or user_id in self.priority_users:
            return False
        
        user_history = self.user_reply_history[user_id]
        
        # Xóa các reply cũ hơn 3 giây
        three_seconds_ago = current_time - timedelta(seconds=3)
        while user_history and user_history[0] < three_seconds_ago:
            user_history.popleft()
        
        # Kiểm tra xem đã đạt giới hạn 1 reply chưa
        return len(user_history) >= 1
    
    def add_user_reply(self, user_id: int, current_time: datetime) -> None:
        """
        Thêm reply vào lịch sử của user
        """
        self.user_reply_history[user_id].append(current_time)
    
    # Wrapper methods cho compatibility
    def mark_for_save(self):
        """Mark data for saving"""
        self.memory_manager.mark_for_save()
    
    async def execute_with_rate_limit(self, ctx, command_func, *args, **kwargs):
        """Execute command với rate limiting và priority bypass"""
        # Priority users bypass rate limiting
        if ctx.author.id in self.priority_users:
            await command_func(*args, **kwargs)
            logger.info(f"Priority user {ctx.author} bypassed rate limiting")
        else:
            await self.rate_limiter.execute_with_rate_limit(ctx, command_func, *args, **kwargs)
    
    def add_warning(self, user_id: int, reason: str, warned_by: str) -> int:
        """
        Thêm warning cho user với deque optimization
        """
        warning_data = {
            'reason': reason,
            'warned_by': warned_by,
            'timestamp': datetime.now().isoformat()
        }
        
        self.warnings[user_id].append(warning_data)
        self.mark_for_save()
        
        return len(self.warnings[user_id])
    
    def get_warnings(self, user_id: int) -> list:
        """
        Lấy danh sách warnings của user
        """
        return list(self.warnings.get(user_id, []))
    
    def clear_user_warnings(self, user_id: int):
        """
        Xóa tất cả warnings của user (reset về 0)
        """
        if user_id in self.warnings:
            del self.warnings[user_id]
            logger.info(f"Đã xóa tất cả warnings của user ID {user_id}")
        
        # Trigger save để lưu thay đổi
        self.memory_manager.trigger_save()
    
    def has_warn_permission(self, user_id: int, guild_permissions) -> bool:
        """
        Kiểm tra xem user có quyền sử dụng lệnh warn không
        """
        # Supreme Admin có mọi quyền
        if self.is_supreme_admin(user_id):
            return True
        
        # Kiểm tra quyền Discord (Administrator hoặc Manage Messages)
        if guild_permissions.administrator or guild_permissions.manage_messages:
            return True
        
        # Kiểm tra trong danh sách admin IDs
        if user_id in self.admin_ids:
            return True
        
        return False
    
    async def get_muted_role_cached(self, guild: discord.Guild) -> Optional[discord.Role]:
        """
        Cache-optimized method để get muted role
        """
        # Check cache first
        if guild.id in self._role_cache:
            return self._role_cache[guild.id]
        
        # Find existing role
        muted_role = discord.utils.get(guild.roles, name="Muted")
        
        if not muted_role:
            try:
                # Create new role with optimized permissions
                muted_role = await guild.create_role(
                    name="Muted",
                    color=discord.Color.dark_grey(),
                    reason="Auto-created for muting users"
                )
                
                # Batch setup permissions cho text channels only
                text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
                for channel in text_channels[:10]:  # Giới hạn 10 channels để tránh rate limit
                    try:
                        await channel.set_permissions(muted_role, send_messages=False)
                    except discord.Forbidden:
                        continue  # Skip nếu không có quyền
                        
                logger.info(f"Created Muted role for guild {guild.name}")
                
            except discord.Forbidden:
                logger.warning(f"Cannot create Muted role in {guild.name}")
                muted_role = None
        
        # Cache the result
        self._role_cache[guild.id] = muted_role
        return muted_role
    
    async def auto_unmute_after_delay(self, guild, member: discord.Member, delay_minutes: int = 1):
        """
        Tự động unmute user sau một khoảng thời gian
        """
        try:
            # Chờ delay_minutes phút
            await asyncio.sleep(delay_minutes * 60)
            
            # Tìm role "Muted"
            muted_role = discord.utils.get(guild.roles, name="Muted")
            if not muted_role:
                return
            
            # Kiểm tra user còn bị mute không
            if muted_role in member.roles:
                await member.remove_roles(muted_role, reason=f"Auto-unmute after {delay_minutes} minute(s)")
                
                # Gửi DM thông báo đã unmute
                try:
                    embed = discord.Embed(
                        title="🔊 Đã được unmute tự động",
                        description=f"Bạn đã được unmute tự động sau {delay_minutes} phút trong server **{guild.name}**",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="⚠️ Lưu ý", 
                        value="Hãy tuân thủ quy tắc server để tránh bị mute lại.", 
                        inline=False
                    )
                    await member.send(embed=embed)
                except:
                    pass  # Không quan trọng nếu không gửi được DM
                
                logger.info(f"Auto-unmuted user {member} ({member.id}) after {delay_minutes} minute(s)")
            
            # Xóa task khỏi tracking
            if member.id in self.mute_tasks:
                del self.mute_tasks[member.id]
                
        except asyncio.CancelledError:
            logger.info(f"Auto-unmute task for {member} was cancelled")
        except Exception as e:
            logger.error(f"Error in auto-unmute for {member}: {e}")
    
    def setup_events(self) -> None:
        """
        Thiết lập các event handler cho Discord bot
        """
        @self.bot.event
        async def on_ready():
            # Kiểm tra bot đã sẵn sàng chưa
            if not self.bot.user:
                logger.error("Bot user is None in on_ready event")
                return
                
            logger.info(f"Refactored bot đã đăng nhập thành công: {self.bot.user}")
            logger.info(f"Bot ID: {self.bot.user.id}")
            logger.info(f"Auto-reply đã được {'bật' if self.config['enabled'] else 'tắt'}")
            logger.info("Rate Limiting: 1 lệnh/3s, 1 reply/3s cho mỗi user")
            
            # Start utilities sau khi có event loop
            self.rate_limiter.start()
            self.memory_manager.start()
            
            # Start DM cleanup task
            if hasattr(self, 'dm_management_commands'):
                asyncio.create_task(self.dm_management_commands.start_cleanup_task())
            
            # Sync slash commands
            try:
                synced_count = await self.slash_commands.sync_commands()
                logger.info(f"Synced {synced_count} slash commands")
                print(f"🔄 Synced {synced_count} slash commands")
            except Exception as e:
                logger.error(f"Failed to sync slash commands: {e}")
                print(f"❌ Failed to sync slash commands: {e}")
            
            # Hiển thị invite link
            invite_link = self.get_invite_link()
            logger.info(f"Invite link: {invite_link}")
            print(f"{invite_link}")
            print("\n📝 Lưu ý quan trọng:")
            print("- Bot cần được mời vào server để có thể nhận DM từ thành viên")
            print("- Hoặc người dùng phải bật 'Cho phép tin nhắn trực tiếp từ thành viên server'")
            print("- Bot không thể bypass cài đặt riêng tư của người dùng")
            print("\n⚠️  Lệnh có sẵn:")
            print("  • ;help - Hướng dẫn sử dụng bot và lời chào")
            print("  • ;menu hoặc /menu - Hiển thị menu tất cả lệnh có sẵn")
            print("  • ;warn @user <lý do> - Cảnh báo user (timeout sau 3 lần)")
            print("  • ;mute @user <thời gian> <lý do> - Mute user với thời gian tùy chỉnh")
            print("  • ;unmute @user - Remove timeout user")
            print("  • ;warnings [@user] - Xem lịch sử warnings")
            print("  • ;muteinfo [@user] - Xem thông tin mute của user hoặc tất cả users")
            print("  • ;amenconfig - Quản lý thông báo mute DM (admin)")
            print("  • ;status - Xem trạng thái bot, CPU, RAM, ping")
            print("  • ;nhom - Xem thông tin chi tiết server (members, channels, etc)")
            print("  • ;taixiu tai/xiu <số tiền> - Chơi game tài xỉu")
            print("  • ;taixiustats [@user] - Xem thống kê tài xỉu")
            print("  • ;give @user <số tiền> - Give tiền cho member (admin)")
            print("  • ;admin add/remove/list - Quản lý admin")
            print("  • ;supremeadmin set/remove/info - Quản lý Supreme Admin (quyền tối cao)")
            print("  • ;addpriority <user_id> - Cấp quyền bypass rate limiting")
            print("  • ;removepriority <user_id> - Xóa quyền bypass")
            print("  • ;listpriority - Xem danh sách priority users")
            print("  • ;netping - Chẩn đoán kết nối và ping")
            print("  • ;netstat - Thống kê network chi tiết")
            print("  • ;dm <user_id> hoặc ;dm @user <nội dung> - Gửi DM cho user (không delay)")
            print("  • ;chatroom <channel_id> <nội dung> - Gửi tin nhắn vào channel theo ID")
            print("  • ;emoji <message_id> - Thêm emoji reaction ngẫu nhiên vào tin nhắn")
            print("  • ;spotify <url> - Hiển thị bot đang nghe nhạc Spotify (admin, tự động tắt)")
            print("  • ;stopmusic - Dừng hiển thị trạng thái nhạc (admin)")
            print("  • ;debug <link> - Debug Python code với AI")
            print("  • ;preview <link> - Preview code với AI")
            print("  • ;ask <câu hỏi> - Hỏi CodeMaster AI")
            print("  • @bot <tin nhắn> - Chat với AI (mention bot để trò chuyện)")
            print("  • ;apistatus - Xem trạng thái các API Gemini (admin)")
            print("  • ;switchapi - Chuyển sang API tiếp theo (admin)")
            print("  • ;test - Kiểm tra bot hoạt động")
            print("  • ;bot - Giới thiệu về bot creator")
            print("  • ;bio <nội dung> - Cập nhật status bot (admin)")
            print("  • ;tiktok <username> - Lấy thông tin tài khoản TikTok")
            print("  • ;github <username> - Lấy thông tin tài khoản GitHub")
            print("  • ;video <tên video> - Gửi video vào kênh hiện tại")
            print("  • ;video add <URL> <tên> - Tải video từ URL (admin)")
            print("  • ;listvideo - Xem danh sách video có sẵn")
            print("  • ;feedback <nội dung> - Gửi feedback cho Supreme Admin")
            print("  • ;feedbackstats - Xem thống kê feedback (Supreme Admin)")
            print("  • ;reload [module] - Reload commands modules (Supreme Admin)")
            print("  • ;listmodules - Xem danh sách modules có thể reload (Supreme Admin)")
            print("  • ;checkdms [số lượng] - Xem tin nhắn DM gần đây (Supreme Admin)")
            print("  • ;cleanupdms - Xóa DM cũ hơn 3 ngày (Supreme Admin)")
            print("  • ;afk [lý do] - Đặt trạng thái AFK với lý do")
            print("  • ;unafk - Bỏ trạng thái AFK thủ công")
            print("  • ;afklist - Xem danh sách users đang AFK")
            print("\n🔇 Hệ thống timeout: Tự động timeout 1 phút sau 3 warnings")
            print("\n🚦 Rate Limiting: 1 lệnh/3s, 1 AI reply/3s cho mỗi user")
            print("💡 Supreme Admin và Priority users được bypass rate limiting")
            print("📱 Hỗ trợ cả prefix commands (;) và slash commands (/)")
            
            
            # Log số lượng commands đã load
            commands_count = len(self.bot.commands)
            logger.info(f"Đã load {commands_count} commands: {[cmd.name for cmd in self.bot.commands]}")
            print(f"📋 Đã load {commands_count} commands: {', '.join([cmd.name for cmd in self.bot.commands])}")
            
            # Log số lượng admin IDs
            logger.info(f"Đã load {len(self.admin_ids)} admin IDs: {self.admin_ids}")
            print(f"👑 Admin IDs được cấp quyền warn: {len(self.admin_ids)} người")
            
            # Log Supreme Admin
            if self.supreme_admin_id:
                logger.info(f"Supreme Admin ID: {self.supreme_admin_id}")
                print(f"🔥 Supreme Admin (Quyền tối cao): {self.supreme_admin_id}")
            else:
                print("⚪ Chưa có Supreme Admin (sử dụng ;supremeadmin set <user_id>)")
        
        @self.bot.event
        async def on_message(message):
            # Bỏ qua tin nhắn từ chính bot (kiểm tra bot đã sẵn sàng)
            if not self.bot.user or message.author == self.bot.user:
                return
            
            # Bỏ qua tin nhắn từ webhook
            if message.webhook_id:
                return
            
            # KIỂM TRA USER BỊ BAN CHỈ CHO LỆNH - Không xóa tin nhắn thường
            if hasattr(self, 'ban_commands') and self.ban_commands.is_user_banned(message.author.id):
                # Chỉ chặn lệnh, không xóa tin nhắn thường
                if message.content.startswith(';'):
                    logger.warning(f"Banned user {message.author.id} ({message.author}) attempted command: {message.content}")
                    
                    # Gửi DM thông báo cho user bị ban (chỉ 1 lần mỗi 24h để tránh spam)
                    try:
                        ban_info = self.ban_commands.get_ban_info(message.author.id)
                        
                        # Kiểm tra xem đã gửi thông báo trong 24h chưa
                        current_time = datetime.now()
                        
                        # Sử dụng rate limiter để kiểm tra 24h cooldown
                        if not hasattr(self, '_ban_notifications'):
                            self._ban_notifications = {}
                        
                        last_notified = self._ban_notifications.get(message.author.id)
                        if not last_notified or (current_time - last_notified).total_seconds() > 86400:  # 24 hours
                            embed = discord.Embed(
                                title="🚫 Tài khoản bị cấm",
                                description="Bạn đã bị cấm sử dụng bot này và không thể sử dụng lệnh!",
                                color=discord.Color.red(),
                                timestamp=current_time
                            )
                            
                            if ban_info:
                                embed.add_field(
                                    name="📝 Lý do",
                                    value=ban_info.get('reason', 'Không có lý do'),
                                    inline=False
                                )
                                
                                ban_time = ban_info.get('timestamp')
                                if ban_time:
                                    try:
                                        ban_timestamp = datetime.fromisoformat(ban_time)
                                        embed.add_field(
                                            name="⏰ Thời gian bị cấm",
                                            value=f"<t:{int(ban_timestamp.timestamp())}:F>",
                                            inline=False
                                        )
                                    except:
                                        pass
                            
                            embed.add_field(
                                name="⚠️ Lưu ý",
                                value="• Bạn không thể sử dụng bất kỳ lệnh nào\n• Tin nhắn thường vẫn được giữ lại\n• Liên hệ admin để được hỗ trợ",
                                inline=False
                            )
                            
                            embed.set_footer(text="Thông báo này chỉ gửi 1 lần/24h")
                            
                            await message.author.send(embed=embed)
                            self._ban_notifications[message.author.id] = current_time
                            logger.info(f"Sent ban notification to user {message.author.id}")
                            
                    except discord.Forbidden:
                        # User đã tắt DM, không thể gửi thông báo
                        pass
                    except Exception as e:
                        logger.error(f"Error sending ban notification: {e}")
                    
                    # DỪNG XỬ LÝ CHỈ CHO LỆNH - Tin nhắn thường vẫn được xử lý bình thường
                    return
                
                # Nếu không phải lệnh, tiếp tục xử lý bình thường (không return)
            
            # Log tin nhắn để debug (chỉ log user không bị ban)
            if message.content.startswith(';'):
                logger.info(f"Command detected: {message.content} from {message.author}")
            
            # Xử lý Auto Delete system trước tất cả (trừ commands)
            if hasattr(self, 'auto_delete_commands') and not message.content.startswith(';'):
                await self.auto_delete_commands.handle_auto_delete_message(message)
                # Nếu tin nhắn bị xóa, không xử lý gì thêm
                try:
                    # Kiểm tra tin nhắn còn tồn tại không
                    await message.channel.fetch_message(message.id)
                except discord.NotFound:
                    # Tin nhắn đã bị xóa bởi auto delete
                    return
                except:
                    pass
            
            # Xử lý Channel Restriction system (trừ commands)
            if hasattr(self, 'channel_restrict_commands') and not message.content.startswith(';'):
                deleted = await self.channel_restrict_commands.handle_channel_restrict_message(message)
                if deleted:
                    return  # Tin nhắn đã bị xóa do vi phạm channel restriction
            
            # Xử lý Auto-Reply system (trừ commands)
            if hasattr(self, 'auto_reply_commands') and not message.content.startswith(';'):
                replied = await self.auto_reply_commands.handle_auto_reply(message)
                # Không return ở đây để cho phép các handler khác chạy tiếp
            
            # Channel Restriction system đã được tắt - xóa bỏ để tránh spam logs
            
            # Xử lý AFK system trước khi xử lý commands
            if hasattr(self, 'afk_commands'):
                # Xử lý user quay lại từ AFK (trừ khi là command AFK)
                if not message.content.startswith(';afk') and not message.content.startswith(';unafk'):
                    await self.afk_commands.handle_user_return(message)
                
                # Xử lý mention users AFK (bao gồm Supreme Admin)
                if message.mentions:
                    await self.afk_commands.handle_afk_mention(message)
                    # Xử lý riêng cho Supreme Admin mention
                    await self.afk_commands.handle_supreme_admin_mention(message)
                    
                    # Xử lý Bye system - admin được mention sẽ tự động trả lời
                    if hasattr(self, 'bye_commands'):
                        await self.bye_commands.handle_bye_mention(message)
            
            # Kiểm tra Anti-Abuse trước khi xử lý commands (đặc biệt là ;ask)
            if hasattr(self, 'anti_abuse_commands'):
                abuse_handled = await self.anti_abuse_commands.check_message_for_abuse(message)
                if abuse_handled:
                    return  # Đã xử lý xúc phạm, dừng hoàn toàn
            
            # Xử lý commands trước - KHÔNG xử lý gì khác nếu là command
            if message.content.startswith(';'):
                await self.bot.process_commands(message)
                return  # Dừng xử lý ở đây để tránh duplicate
            
            # Xử lý mention bot với AI response (chỉ khi KHÔNG phải command)
            if self.bot.user and self.bot.user in message.mentions:
                # Anti-abuse đã được kiểm tra ở trên, tiếp tục với AI response
                await self.handle_bot_mention(message)
                return  # Dừng xử lý ở đây
            
            # Xử lý reply đến tin nhắn của bot
            if message.reference and message.reference.message_id:
                await self.handle_reply_to_bot(message)
                return
            
            # Chỉ xử lý tin nhắn riêng (DM) cho auto-reply
            if isinstance(message.channel, discord.DMChannel):
                await self.handle_dm(message)
        
        # Thêm global check cho rate limiting
        @self.bot.check
        async def global_rate_limit_check(ctx):
            """
            Global check để áp dụng maintenance mode, rate limiting và channel permissions cho tất cả commands
            """
            # Kiểm tra bot đã sẵn sàng chưa
            if not self.bot.user:
                return False
            
            # Kiểm tra user có bị ban không
            if hasattr(self, 'ban_commands') and self.ban_commands.is_user_banned(ctx.author.id):
                # Log khi user bị ban cố gắng sử dụng lệnh
                logger.warning(f"Banned user {ctx.author.id} ({ctx.author}) attempted to use command: {ctx.command}")
                
                # Chặn lệnh thầm lặng - không gửi thông báo trong kênh
                # (DM notification đã được xử lý trong on_message)
                return False  # Chặn command
            
            # Kiểm tra maintenance mode (cho phép close, open, maintenancestatus)
            if hasattr(self, 'maintenance_manager'):
                maintenance_allowed_commands = ['close', 'open', 'maintenancestatus', 'maintenance', 'lock', 'unlock', 'unmaintenance', 'mstatus']
                command_name = ctx.command.name if ctx.command else None
                
                if self.maintenance_manager.is_maintenance_mode():
                    # Chỉ Supreme Admin mới có thể dùng lệnh trong maintenance mode
                    if not self.is_supreme_admin(ctx.author.id):
                        # Check nếu là lệnh được phép (status check)
                        if command_name not in maintenance_allowed_commands:
                            embed = discord.Embed(
                                title="🔒 Bot đang bảo trì",
                                description="Bot hiện đang trong chế độ bảo trì!",
                                color=discord.Color.red()
                            )
                            
                            maintenance_data = self.maintenance_manager.maintenance_data
                            closed_by = maintenance_data.get('closed_by', {})
                            reason = maintenance_data.get('reason', 'Đang bảo trì hệ thống')
                            
                            embed.add_field(
                                name="📝 Lý do",
                                value=reason,
                                inline=False
                            )
                            
                            embed.add_field(
                                name="👤 Thông báo bởi",
                                value=closed_by.get('name', 'Admin'),
                                inline=True
                            )
                            
                            embed.set_footer(text="Vui lòng chờ bot hoạt động trở lại • Sử dụng ;maintenancestatus để xem chi tiết")
                            
                            await ctx.reply(embed=embed, mention_author=True)
                            return False
            
            # Cho phép DM chỉ cho Admin
            if isinstance(ctx.channel, discord.DMChannel):
                # Chỉ Admin và Supreme Admin có thể dùng lệnh qua DM
                if self.is_admin(ctx.author.id) or self.is_supreme_admin(ctx.author.id):
                    return True
                else:
                    await ctx.reply(
                        "❌ **Chỉ Admin mới có thể sử dụng lệnh qua DM!**\n\n"
                        "👤 **User thường:** Vui lòng sử dụng bot trong server\n"
                        "👑 **Admin:** Có thể sử dụng bot mọi nơi",
                        mention_author=True
                    )
                    return False
            
            # Kiểm tra channel permissions (chỉ cho guild, không cho DM)
            if ctx.guild and hasattr(self, 'channel_permission_manager'):
                # Lấy tên command (bỏ prefix)
                command_name = ctx.command.name if ctx.command else None
                
                if not self.channel_permission_manager.is_channel_allowed(ctx.guild.id, ctx.channel.id, command_name):
                    # Gợi ý DM chỉ cho admin
                    if self.is_admin(ctx.author.id) or self.is_supreme_admin(ctx.author.id):
                        await ctx.reply(
                            "❌ **Bot không thể hoạt động trong kênh này!**\n"
                            "💬 **Gợi ý:** Admin có thể sử dụng bot qua DM (tin nhắn riêng)",
                            mention_author=True
                        )
                    else:
                        await ctx.reply(
                            "❌ **Bot không thể hoạt động trong kênh này!**\n"
                            "🔍 **Gợi ý:** Tìm kênh được phép hoặc liên hệ admin",
                            mention_author=True
                        )
                    return False
                
            current_time = datetime.now()
            user_id = ctx.author.id
            
            # Supreme Admin và Priority users bypass rate limiting
            if self.is_supreme_admin(user_id) or user_id in self.priority_users:
                return True
            
            # Kiểm tra rate limit
            if self.is_user_rate_limited(user_id, current_time):
                reset_time = self.get_rate_limit_reset_time(user_id, current_time)
                await ctx.reply(
                    f"{ctx.author.mention} ⏰ Bạn đang bị rate limit! "
                    f"Vui lòng chờ **{reset_time}** giây trước khi sử dụng lệnh tiếp theo.",
                    mention_author=True
                )
                return False
            
            # Thêm command vào lịch sử
            self.add_user_command(user_id, current_time)
            return True
        
        @self.bot.event
        async def on_command_error(ctx, error):
            """Xử lý lỗi commands"""
            async def safe_reply(message):
                """Gửi reply an toàn, fallback sang DM nếu không có quyền"""
                try:
                    # Kiểm tra bot có quyền gửi tin nhắn trong kênh không
                    if ctx.channel.permissions_for(ctx.guild.me).send_messages:
                        await ctx.reply(message, mention_author=True)
                    else:
                        # Tạo embed thông báo lỗi cho DM
                        error_embed = discord.Embed(
                            title="⚠️ Lỗi từ Discord Server",
                            description=f"Bot không thể trả lời trong kênh #{ctx.channel.name}",
                            color=discord.Color.orange(),
                            timestamp=datetime.now()
                        )
                        
                        error_embed.add_field(
                            name="🔍 Lệnh đã thực hiện:",
                            value=f"`{ctx.message.content[:100]}...`" if len(ctx.message.content) > 100 else f"`{ctx.message.content}`",
                            inline=False
                        )
                        
                        error_embed.add_field(
                            name="❌ Lỗi gặp phải:",
                            value=message.replace(ctx.author.mention, "").strip(),
                            inline=False
                        )
                        
                        error_embed.add_field(
                            name="🔧 Nguyên nhân:",
                            value="Bot thiếu quyền `Send Messages` trong kênh này",
                            inline=False
                        )
                        
                        error_embed.set_footer(
                            text=f"Server: {ctx.guild.name} • Kênh: #{ctx.channel.name}",
                            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
                        )
                        
                        # Gửi DM với embed
                        await ctx.author.send(embed=error_embed)
                        
                except discord.Forbidden:
                    # Nếu không gửi được DM, log error và bỏ qua
                    logger.warning(f"Không thể gửi thông báo lỗi cho {ctx.author.name} ({ctx.author.id}) - bot thiếu quyền DM")
                except Exception as e:
                    logger.error(f"Lỗi khi gửi thông báo lỗi: {e}")
            
            if isinstance(error, commands.CheckFailure):
                # Rate limit đã được xử lý trong global check, không cần làm gì thêm
                return
            elif isinstance(error, commands.CommandOnCooldown):
                # Đã xử lý trong on_command, không cần làm gì thêm
                return
            elif isinstance(error, commands.MissingRequiredArgument):
                await safe_reply(f"{ctx.author.mention} ❌ Thiếu tham số bắt buộc: `{error.param.name}`")
            elif isinstance(error, commands.BadArgument):
                await safe_reply(f"{ctx.author.mention} ❌ Tham số không hợp lệ: {str(error)}")
            elif isinstance(error, commands.CommandNotFound):
                # Bỏ qua lỗi command không tồn tại
                return
            elif isinstance(error, discord.Forbidden):
                logger.warning(f"Bot thiếu quyền thực hiện command '{ctx.command}' trong kênh #{ctx.channel.name}")
                await safe_reply(f"{ctx.author.mention} ❌ Bot không có quyền thực hiện lệnh này trong kênh này!")
            elif isinstance(error, discord.HTTPException):
                logger.error(f"Discord HTTP error in command '{ctx.command}': {error}")
                logger.error(f"Error code: {error.code}, Status: {error.status}, Response: {error.response}")
                if error.code == 50035:
                    await safe_reply(f"{ctx.author.mention} ❌ Nội dung quá dài hoặc không hợp lệ. Vui lòng thử lại với nội dung ngắn hơn.")
                elif error.code == 50013:
                    await safe_reply(f"{ctx.author.mention} ❌ Bot không có quyền thực hiện hành động này!")
                else:
                    await safe_reply(f"{ctx.author.mention} ❌ Lỗi Discord API: {str(error)[:100]}")
            else:
                logger.error(f"Command error in '{ctx.command}': {error}")
                logger.error(f"Error type: {type(error)}")
                await safe_reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra: {str(error)[:100]}")
        
        @self.bot.event
        async def on_reaction_add(reaction, user):
            """Xử lý khi có người react emoji"""
            try:
                # Fire Delete system đã bị vô hiệu hóa
                # if hasattr(self, 'fire_delete_commands'):
                #     await self.fire_delete_commands.handle_fire_delete_reaction(reaction, user)
                pass  # Placeholder vì Fire Delete đã bị vô hiệu hóa
            except Exception as e:
                logger.error(f"Lỗi trong on_reaction_add: {e}")
        
        @self.bot.event
        async def on_member_update(before, after):
            """Xử lý khi member update (nickname, roles, etc.)"""
            try:
                # Xử lý Nickname Control system (cũ)
                if hasattr(self, 'nickname_commands'):
                    await self.nickname_commands.handle_member_update(before, after)
                
                # Xử lý Nickname Control system (mới)
                if hasattr(self, 'nickname_control_commands'):
                    await self.nickname_control_commands.handle_member_update(before, after)
                
                # Xử lý Admin Nickname Protection
                if hasattr(self, 'admin_nickname_protection'):
                    await self.admin_nickname_protection.handle_member_update(before, after)
            except Exception as e:
                logger.error(f"Lỗi trong on_member_update: {e}")
    
    def setup_commands(self) -> None:
        """
        Thiết lập các commands cho bot bằng cách sử dụng command classes
        """
        # Initialize command classes
        self.ai_commands = AICommands(self)  # Store AI commands instance for mention responses
        admin_commands = AdminCommands(self)
        supreme_admin_commands = SupremeAdminCommands(self)
        info_commands = InfoCommands(self)
        priority_commands = PriorityCommands(self)
        network_commands = NetworkCommands(self)
        chat_commands = ChatCommands(self)
        taixiu_commands = TaiXiuCommands(self)
        backup_commands = BackupCommands(self)
        announce_commands = AnnounceCommands(self)
        spotify_commands = SpotifyCommands(self)
        moderation_commands = ModerationCommands(self)
        channel_commands = ChannelCommands(self)
        server_commands = ServerCommands(self)
        message_commands = MessageCommands(self)
        tiktok_commands = TikTokCommands(self)
        github_commands = GitHubCommands(self)
        video_commands = VideoCommands(self)
        music_commands = MusicCommands(self)
        feedback_commands = FeedbackCommands(self)
        slash_commands = SlashCommands(self)
        emoji_commands = EmojiCommands(self)
        dm_management_commands = DMManagementCommands(self)
        permission_commands = PermissionCommands(self)
        channel_permission_commands = ChannelPermissionCommands(self)
        maintenance_commands = MaintenanceCommands(self)
        github_backup_commands = GitHubBackupCommands(self)
        game_menu_commands = GameMenuCommands(self)
        rps_commands = RPSCommands(self)
        slot_commands = SlotCommands(self)
        blackjack_commands = BlackjackCommands(self)
        self.wallet_commands = WalletCommands(self)
        flip_coin_commands = FlipCoinCommands(self)
        wallet_reload_commands = WalletReloadCommands(self)
        daily_commands = DailyCommands(self)
        github_download_commands = GitHubDownloadCommands(self)
        admin_menu_commands = AdminMenuCommands(self)
        # virustotal_commands = VirusTotalCommands(self)  # Đã xóa
        
        # Khởi tạo các command classes
        self.warn_commands = WarnCommands(self)
        self.mute_commands = MuteCommands(self)
        self.afk_commands = AFKCommands(self)
        self.ban_commands = BanCommands(self)
        self.auto_delete_commands = AutoDeleteCommands(self)
        self.purge_commands = PurgeCommands(self)
        self.anti_abuse_commands = AntiAbuseCommands(self)
        # self.fire_delete_commands = FireDeleteCommands(self)  # DISABLED - Xóa tính năng fire delete
        self.channel_restrict_commands = ChannelRestrictCommands(self)
        self.bye_commands = ByeCommands(self)
        # self.shop_commands = ShopCommands(self)  # Đã xóa
        self.unluck_commands = UnluckCommands(self)
        # self.leaderboard_commands = LeaderboardCommands(self)  # Đã xóa
        self.nickname_commands = NicknameCommands(self)
        self.reset_commands = ResetCommands(self)
        # self.getkey_commands = GetKeyCommands(self)  # Đã xóa
        self.complete_menu_commands = CompleteMenuCommands(self)
        self.auto_reply_commands = AutoReplyCommands(self)
        self.fishing_commands = FishingCommands(self)
        self.giveaway_commands = GiveawayCommands(self)
        # self.full_menu_commands = FullMenuCommands(self)  # Đã tích hợp vào game_menu_commands
        # self.channel_restriction_commands = ChannelRestrictionCommands(self)  # Đã tắt
        
        # Khởi tạo Anti-Abuse Commands
        self.anti_abuse_commands = AntiAbuseCommands(self)
        self.anti_abuse_commands.register_commands()
        
        # Khởi tạo Multi-Bot Commands
        self.multibot_commands = MultiBotCommands(self)
        self.multibot_commands.register_commands()
        
        # Khởi tạo Nickname Control Commands
        self.nickname_control_commands = NicknameControlCommands(self)
        self.nickname_control_commands.register_commands()
        
        # Khởi tạo Admin Nickname Protection
        self.admin_nickname_protection = AdminNicknameProtection(self)
        self.admin_nickname_protection.register_commands()
        
        # Register AI commands
        self.ai_commands.register_commands()
        
        # Register other commands
        admin_commands.register_commands()
        supreme_admin_commands.register_commands()
        info_commands.register_commands()
        priority_commands.register_commands()
        network_commands.register_commands()
        chat_commands.register_commands()
        taixiu_commands.register_commands()
        backup_commands.register_commands()
        announce_commands.register_commands()
        spotify_commands.register_commands()
        moderation_commands.register_commands()
        channel_commands.register_commands()
        server_commands.register_commands()
        message_commands.register_commands()
        tiktok_commands.register_commands()
        github_commands.register_commands()
        video_commands.register_commands()
        music_commands.register_commands()
        feedback_commands.register_commands()
        slash_commands.register_commands()
        emoji_commands.register_commands()
        dm_management_commands.register_commands()
        permission_commands.register_commands()
        channel_permission_commands.register_commands()
        maintenance_commands.register_commands()
        github_backup_commands.register_commands()
        game_menu_commands.register_commands()
        rps_commands.register_commands()
        slot_commands.register_commands()
        blackjack_commands.register_commands()
        self.wallet_commands.register_commands()
        flip_coin_commands.register_commands()
        wallet_reload_commands.register_commands()
        daily_commands.register_commands()
        github_download_commands.register_commands()
        admin_menu_commands.register_commands()
        # virustotal_commands.register_commands()  # Đã xóa
        self.afk_commands.register_commands()
        self.ban_commands.register_commands()
        self.auto_delete_commands.register_commands()
        self.purge_commands.register_commands()
        self.anti_abuse_commands.register_commands()
        # self.fire_delete_commands.register_commands()  # DISABLED - Xóa tính năng fire delete
        self.channel_restrict_commands.register_commands()
        self.bye_commands.register_commands()
        # self.shop_commands.register_commands()  # Đã xóa
        self.unluck_commands.register_commands()
        # self.leaderboard_commands.register_commands()  # Đã xóa
        self.nickname_commands.register_commands()
        self.reset_commands.register_commands()
        # self.getkey_commands.register_commands()  # Đã xóa
        self.complete_menu_commands.register_commands()
        self.auto_reply_commands.register_commands()
        self.fishing_commands.register_commands()
        self.giveaway_commands.register_commands()
        # self.full_menu_commands.register_commands()  # Đã tích hợp vào game_menu_commands
        # self.channel_restriction_commands.register_commands()  # Đã tắt
        
        # Store instances for syncing and DM handling
        self.slash_commands = slash_commands
        self.dm_management_commands = dm_management_commands
        self.permission_manager = permission_commands
        self.maintenance_manager = maintenance_commands
        self.channel_permission_manager = channel_permission_commands
        # afk_commands, ban_commands, auto_delete_commands đã được lưu ở trên
        # fire_delete_commands đã bị vô hiệu hóa
        
        logger.info("Đã đăng ký tất cả commands từ các command classes")
    
    def get_invite_link(self) -> str:
        """
        Tạo invite link cho bot với quyền administrator
        """
        if not self.bot.user:
            return "Bot chưa đăng nhập"
        
        # Cấp quyền administrator cho bot
        permissions = discord.Permissions(administrator=True)
        
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=['bot']
        )
        
        return invite_url
    
    async def handle_dm(self, message: discord.Message) -> None:
        """
        Xử lý tin nhắn riêng (DM)
        """
        try:
            # Shop system đã bị xóa - bỏ qua shop order handling
            
            # Forward DM đến Supreme Admin trước (không phụ thuộc vào auto-reply)
            if hasattr(self, 'dm_management_commands'):
                await self.dm_management_commands.handle_dm_message(message)
            
            # Kiểm tra xem auto-reply có được bật không
            if not self.config.get('enabled', True):
                return
            
            user_id = message.author.id
            current_time = datetime.now()
            
            # Kiểm tra cooldown
            if self.is_on_cooldown(user_id, current_time):
                logger.info(f"DM từ {message.author} bị bỏ qua do cooldown")
                return
            
            # Cập nhật thời gian gửi tin nhắn cuối cùng
            self.cooldowns[user_id] = current_time
            
            # Lấy tin nhắn auto-reply
            auto_reply_message = self.config.get('auto_reply_message', 
                'Xin chào! Tôi hiện tại không có mặt. Tôi sẽ phản hồi bạn sớm nhất có thể. Cảm ơn bạn đã liên hệ!')
            
            # Gửi tin nhắn auto-reply
            await message.reply(auto_reply_message)
            
            logger.info(f"Đã gửi auto-reply cho {message.author} ({user_id})")
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý DM từ {message.author}: {e}")
    
    def is_on_cooldown(self, user_id: int, current_time: datetime) -> bool:
        """
        Kiểm tra xem user có đang trong thời gian cooldown không
        """
        if user_id not in self.cooldowns:
            return False
        
        last_reply_time = self.cooldowns[user_id]
        cooldown_duration = timedelta(seconds=self.config.get('cooldown_seconds', 5))
        
        return current_time - last_reply_time < cooldown_duration
    
    async def handle_bot_mention(self, message: discord.Message) -> None:
        """
        Xử lý khi bot được mention - trả lời bằng AI
        """
        try:
            # Kiểm tra bot đã sẵn sàng chưa
            if not self.bot.user:
                return
                
            # Kiểm tra xem AI có khả dụng không
            if not hasattr(self, 'ai_commands') or not self.ai_commands.gemini_model:
                await message.reply("👋 Xin chào! Rất vui được gặp bạn! (AI hiện chưa được cấu hình)", mention_author=True)
                return
            
            # Lấy nội dung tin nhắn, loại bỏ mention
            content = message.content
            for mention in message.mentions:
                content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
            content = content.strip()
            
            # Nếu không có nội dung, chỉ chào hỏi
            if not content:
                content = "xin chào"
            
            # Gửi typing indicator
            async with message.channel.typing():
                # Generate AI response using new rotation system
                ai_response = await self.ai_commands.generate_mention_response(content)
                
                # Giới hạn độ dài response
                if len(ai_response) > 500:
                    ai_response = ai_response[:500] + "..."
                
                # Gửi response
                await message.reply(ai_response, mention_author=False)
                
            logger.info(f"AI mentioned response sent to {message.author} in {message.guild.name if message.guild else 'DM'}")
                
        except Exception as e:
            logger.error(f"Lỗi khi xử lý bot mention từ {message.author}: {e}")
            # Fallback response
            await message.reply("👋 Xin chào! Rất vui được gặp bạn! 😊 (Có lỗi nhỏ với AI, nhưng tôi vẫn ở đây!)", mention_author=True)
    
    async def handle_reply_to_bot(self, message: discord.Message) -> None:
        """
        Xử lý khi ai đó reply tin nhắn của bot - tiếp tục cuộc hội thoại
        """
        try:
            # Kiểm tra bot đã sẵn sàng chưa
            if not self.bot.user:
                return
            
            # Lấy tin nhắn được reply
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
            except (discord.NotFound, discord.Forbidden):
                return  # Không thể lấy tin nhắn được reply
            
            # Kiểm tra xem tin nhắn được reply có phải của bot không
            if replied_message.author != self.bot.user:
                return  # Không phải reply tin nhắn của bot
            
            # Kiểm tra xem AI có khả dụng không
            if not hasattr(self, 'ai_commands') or not self.ai_commands.gemini_model:
                return  # AI không khả dụng, không trả lời
            
            # Kiểm tra rate limiting riêng cho reply (3 giây)
            current_time = datetime.now()
            user_id = message.author.id
            
            # Supreme Admin và Priority users bypass rate limiting
            if not (self.is_supreme_admin(user_id) or user_id in self.priority_users):
                if self.is_user_reply_rate_limited(user_id, current_time):
                    # Không gửi thông báo rate limit cho reply để tránh spam
                    return
                # Thêm vào lịch sử reply
                self.add_user_reply(user_id, current_time)
            
            # Lấy nội dung tin nhắn reply
            content = message.content.strip()
            if not content:
                return  # Không có nội dung để trả lời
            
            # Lấy context từ tin nhắn trước đó (giảm từ 6 xuống 3 để tiết kiệm API calls)
            context_messages = []
            try:
                # Lấy ít tin nhắn hơn để giảm API calls
                async for msg in message.channel.history(limit=3, before=message):
                    if msg.author == self.bot.user or msg.author == message.author:
                        context_messages.append(f"{msg.author.display_name}: {msg.content[:50]}")  # Giảm độ dài
                    if len(context_messages) >= 2:  # Giảm context xuống 2
                        break
            except discord.HTTPException as e:
                if e.status == 429:
                    logger.warning("Rate limited when fetching context messages")
                pass  # Không lấy được context thì thôi
            
            # Tạo context string
            context = ""
            if context_messages:
                context = "\n".join(reversed(context_messages[-3:]))  # 3 tin nhắn gần nhất
            
            # Gọi AI để tạo response với context
            async with message.channel.typing():
                ai_response = await self.ai_commands.generate_reply_response(content, context)
                
                # Giới hạn độ dài response
                if len(ai_response) > 400:
                    ai_response = ai_response[:400] + "..."
            
            # Gửi response
            await message.reply(ai_response, mention_author=False)
            
            logger.info(f"AI replied to {message.author} in {message.guild.name if message.guild else 'DM'}#{message.channel.name if hasattr(message.channel, 'name') else 'DM'}")
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý reply từ {message.author}: {e}")
    
    
    async def run(self) -> None:
        """
        Chạy bot với error handling tốt hơn
        """
        token = self.config.get('token')
        if not token:
            logger.error(
                "Token không được tìm thấy! "
                "Vui lòng cập nhật token trong file config.json"
            )
            return
        
        try:
            logger.info("Đang khởi động bot...")
            
            # Start message cache cleanup task
            message_cache.start_cleanup_task()
            
            await self.bot.start(token)
        except discord.LoginFailure:
            logger.error("Token không hợp lệ! Vui lòng kiểm tra lại token")
        except Exception as e:
            logger.error(f"Lỗi khi chạy bot: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def stop(self) -> None:
        """
        Dừng bot với cleanup tối ưu
        """
        logger.info("Đang dừng refactored bot...")
        
        # Stop utilities
        self.rate_limiter.stop()
        self.memory_manager.stop()
        
        # Stop message cache
        message_cache.stop_cleanup_task()
        
        # Stop DM cleanup task
        if hasattr(self, 'dm_management_commands'):
            self.dm_management_commands.stop_cleanup_task()
        
        # Cancel all mute tasks
        for task in self.mute_tasks.values():
            task.cancel()
        
        # Cleanup nickname tasks
        if hasattr(self, 'nickname_commands'):
            asyncio.create_task(self.nickname_commands.cleanup_tasks())
        
        asyncio.create_task(self.bot.close())


def main():
    """
    Hàm main để chạy refactored bot
    """
    print("=== Discord Auto-Reply Bot (Refactored) ===")
    print("Tính năng:")
    print("- Modular architecture với command classes")
    print("- Rate limiting với queue system")
    print("- Memory management tối ưu")
    print("- Batch saving và caching")
    print("- Auto-mute system")
    print("\nĐang khởi động bot...")

    # Tạo instance của refactored bot
    bot = AutoReplyBotRefactored()
    
    # Hiển thị hướng dẫn cấu hình nếu chưa có token
    if not bot.config.get('token'):
        print("\n⚠️  CẢNH BÁO: Chưa có token!")
        print("\nVui lòng làm theo các bước sau:")
        print("1. Mở file 'bot_files/data/config.json'")
        print("2. Thêm token Discord của bạn vào trường 'token'")
        print("3. Tùy chỉnh tin nhắn auto-reply nếu muốn")
        print("4. Chạy lại chương trình")
        return
    
    try:
        # Chạy bot
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nĐã nhận tín hiệu dừng. Đang thoát...")
        bot.stop()
    except Exception as e:
        logger.error(f"Lỗi không mong muốn: {e}")


if __name__ == "__main__":
    main()
