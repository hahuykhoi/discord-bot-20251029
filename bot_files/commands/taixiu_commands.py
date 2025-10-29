"""
Tài Xỉu Commands - Hệ thống game tài xỉu cho Discord bot
Lệnh: ;taixiu tai/xiu <số tiền>
"""
import discord
from discord.ext import commands
import json
import os
import random
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional
from utils.shared_wallet import shared_wallet

logger = logging.getLogger(__name__)

class TaiXiuCommands:
    def __init__(self, bot_instance):
        """
        Khởi tạo TaiXiu Commands
        
        Args:
            bot_instance: Instance của AutoReplyBotRefactored
        """
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.player_data_file = 'data/taixiu_players.json'
        self.player_data = self.load_player_data()
        self.shared_wallet = shared_wallet
        self.daily_give_file = 'data/daily_give_limits.json'
        self.daily_give_data = self.load_daily_give_data()
        self.min_bet = 1  # Cược tối thiểu (chỉ > 0)
        self.max_bet = 250000  # Giới hạn max cược 250k
        self.starting_money = 5000  # Tiền khởi tạo cho người chơi mới
        
        # Tracking game đang chạy
        self.active_games = set()  # Set chứa user_id của những user đang có game chạy
        
        logger.info("TaiXiu Commands đã được khởi tạo")
    
    def load_player_data(self) -> Dict:
        """
        Tải dữ liệu người chơi từ file JSON
        
        Returns:
            Dict: Dữ liệu người chơi
        """
        try:
            if os.path.exists(self.player_data_file):
                with open(self.player_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Đã tải dữ liệu {len(data)} người chơi tài xỉu")
                return data
            else:
                logger.info("Không tìm thấy file dữ liệu tài xỉu, tạo mới")
                return {}
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu tài xỉu: {e}")
            return {}
    
    def save_player_data(self) -> None:
        """
        Lưu dữ liệu người chơi vào file JSON
        """
        try:
            # Tạo thư mục data nếu chưa có
            os.makedirs(os.path.dirname(self.player_data_file), exist_ok=True)
            
            with open(self.player_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.player_data, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu dữ liệu tài xỉu thành công")
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu tài xỉu: {e}")
    
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
    
    def get_player_money(self, user_id: int, guild_permissions=None) -> int:
        """
        Lấy số tiền của người chơi từ shared wallet
        
        Args:
            user_id: ID của người chơi
            guild_permissions: Quyền trong guild (không dùng nữa)
            
        Returns:
            int: Số tiền từ shared wallet
        """
        # Sử dụng shared wallet thống nhất
        return shared_wallet.get_balance(user_id)
    
    def _ensure_player_data(self, user_id: int) -> None:
        """Đảm bảo player data tồn tại cho stats"""
        user_id_str = str(user_id)
        if user_id_str not in self.player_data:
            self.player_data[user_id_str] = {
                'money': self.starting_money,
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'total_bet': 0,
                'total_win': 0,
                'winrate': 0.0,
                'games_10m_plus': 0,  # Số game với cược >= 10M
                'created_at': datetime.now().isoformat(),
                'last_played': datetime.now().isoformat()
            }
            self.save_player_data()
            logger.info(f"Created stats data for user {user_id}")
    
    def update_player_money(self, user_id: int, amount: int, is_win: bool, bet_amount: int, guild_permissions=None) -> None:
        """
        Cập nhật số tiền của người chơi qua shared wallet
        
        Args:
            user_id: ID của người chơi
            amount: Số tiền thay đổi (có thể âm)
            is_win: True nếu thắng, False nếu thua
            bet_amount: Số tiền đã cược
            guild_permissions: Không dùng nữa
        """
        # Đảm bảo player data tồn tại cho stats
        self._ensure_player_data(user_id)
        user_id_str = str(user_id)
        
        # Cập nhật tiền qua shared wallet
        old_money = shared_wallet.get_balance(user_id)
        if amount > 0:
            new_money = shared_wallet.add_balance(user_id, amount)
        else:
            new_money = shared_wallet.subtract_balance(user_id, abs(amount))
        
        # Log chi tiết việc cộng/trừ tiền
        action = "CỘNG" if amount > 0 else "TRỪ"
        logger.info(f"Money update for user {user_id}: {action} {abs(amount)} điểm "
                   f"({old_money:,} → {new_money:,})")
        
        # Cập nhật thống kê (chỉ lưu stats, không lưu money)
        self.player_data[user_id_str]['total_games'] += 1
        self.player_data[user_id_str]['total_bet'] += bet_amount
        self.player_data[user_id_str]['last_played'] = datetime.now().isoformat()
        
        # Tracking game với cược >= 10M
        if bet_amount >= 10_000_000:
            if 'games_10m_plus' not in self.player_data[user_id_str]:
                self.player_data[user_id_str]['games_10m_plus'] = 0
            self.player_data[user_id_str]['games_10m_plus'] += 1
        
        if is_win:
            self.player_data[user_id_str]['wins'] += 1
            self.player_data[user_id_str]['total_win'] += abs(amount)
            
            # Reset lose streak khi thắng
            self.player_data[user_id_str]['lose_streak'] = 0
            logger.info(f"User {user_id} won taixiu - reset lose streak to 0")
            
            # Weekly leaderboard đã bị xóa
        else:
            self.player_data[user_id_str]['losses'] += 1
            
            # Tăng lose streak khi thua
            current_streak = self.player_data[user_id_str].get('lose_streak', 0)
            self.player_data[user_id_str]['lose_streak'] = current_streak + 1
            logger.info(f"User {user_id} lost taixiu - lose streak: {self.player_data[user_id_str]['lose_streak']}")
        
        # Cập nhật winrate
        total_games = self.player_data[user_id_str]['total_games']
        wins = self.player_data[user_id_str]['wins']
        self.player_data[user_id_str]['winrate'] = (wins / total_games * 100) if total_games > 0 else 0
        
        self.save_player_data()
    
    def load_daily_give_data(self) -> Dict:
        """Load daily give limit data"""
        try:
            if os.path.exists(self.daily_give_file):
                with open(self.daily_give_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load daily give data: {e}")
            return {}
    
    def save_daily_give_data(self) -> None:
        """Save daily give limit data"""
        try:
            os.makedirs(os.path.dirname(self.daily_give_file), exist_ok=True)
            with open(self.daily_give_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_give_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save daily give data: {e}")
    
    def get_daily_give_amount(self, user_id: int) -> int:
        """Lấy số tiền đã give trong ngày hôm nay"""
        today = datetime.now().strftime('%Y-%m-%d')
        user_str = str(user_id)
        
        if user_str not in self.daily_give_data:
            self.daily_give_data[user_str] = {}
        
        return self.daily_give_data[user_str].get(today, 0)
    
    def add_daily_give_amount(self, user_id: int, amount: int) -> None:
        """Thêm số tiền đã give vào tracking hôm nay"""
        today = datetime.now().strftime('%Y-%m-%d')
        user_str = str(user_id)
        
        if user_str not in self.daily_give_data:
            self.daily_give_data[user_str] = {}
        
        self.daily_give_data[user_str][today] = self.daily_give_data[user_str].get(today, 0) + amount
        self.save_daily_give_data()
    
    def give_money_to_player(self, user_id: int, amount: int) -> None:
        """
        Give tiền cho người chơi qua shared wallet (admin only)
        
        Args:
            user_id: ID của người chơi
            amount: Số tiền give
        """
        # Thêm tiền qua shared wallet
        shared_wallet.add_balance(user_id, amount)
        
        # Đảm bảo player data tồn tại cho stats
        self._ensure_player_data(user_id)
        self.save_player_data()
        
        logger.info(f"Gave {amount} money to user {user_id}")
    
    def is_user_playing(self, user_id: int) -> bool:
        """
        Kiểm tra xem user có đang chơi game không
        
        Args:
            user_id: ID của user
            
        Returns:
            bool: True nếu user đang có game chạy
        """
        return user_id in self.active_games
    
    def start_game_for_user(self, user_id: int) -> bool:
        """
        Bắt đầu game cho user (thêm vào active games)
        
        Args:
            user_id: ID của user
            
        Returns:
            bool: True nếu thành công, False nếu user đã có game chạy
        """
        if user_id in self.active_games:
            return False
        
        self.active_games.add(user_id)
        logger.info(f"Started game for user {user_id}. Active games: {len(self.active_games)}")
        return True
    
    def end_game_for_user(self, user_id: int) -> None:
        """
        Kết thúc game cho user (xóa khỏi active games)
        
        Args:
            user_id: ID của user
        """
        if user_id in self.active_games:
            self.active_games.remove(user_id)
            logger.info(f"Ended game for user {user_id}. Active games: {len(self.active_games)}")
    
    def roll_dice(self, bet_type: str = None, is_admin: bool = False, user_id: int = None) -> tuple:
        """
        Tung 3 xúc xắc và tính kết quả
        
        Args:
            bet_type: Loại cược ("TÀI" hoặc "XỈU")
            is_admin: True nếu là admin, False nếu là user thường
            user_id: ID của người chơi để track streak
        
        Returns:
            tuple: (dice1, dice2, dice3, total, result)
        """
        # Kiểm tra unluck system trước tiên
        is_unlucky = False
        if user_id and hasattr(self.bot_instance, 'unluck_commands'):
            is_unlucky = self.bot_instance.unluck_commands.is_user_unlucky(user_id)
            if is_unlucky:
                # Tăng số game bị ảnh hưởng
                self.bot_instance.unluck_commands.increment_game_affected(user_id)
                logger.info(f"User {user_id} is unlucky - forcing loss")
        
        # Xác định kết quả game
        if is_unlucky:
            should_win = False  # Unlucky user luôn thua
            logger.info(f"Unlucky user {user_id} - forcing loss")
        else:
            # Logic game: Dynamic win rate system
            # Lấy user data để check streak
            user_data = self.player_data.get(str(user_id), {}) if user_id else {}
            
            # Dynamic win rate: Base 40%, +20% mỗi lần thua liên tiếp
            base_rate = 0.4  # 40% base
            lose_streak = user_data.get('lose_streak', 0)
            dynamic_rate = min(base_rate + (lose_streak * 0.2), 0.9)  # Max 90%
            
            should_win = random.random() < dynamic_rate
            logger.info(f"User {user_id} - Dynamic rate {dynamic_rate*100:.0f}% (streak: {lose_streak}) - {'WIN' if should_win else 'LOSE'}")
        
        if bet_type and should_win:
            # Tạo kết quả thắng theo bet_type
            if bet_type == "TÀI":
                # Tạo tổng từ 11-17 để thắng TÀI
                target_total = random.randint(11, 17)
            else:  # XỈU
                # Tạo tổng từ 4-10 để thắng XỈU
                target_total = random.randint(4, 10)
            
            # Tạo 3 xúc xắc có tổng = target_total
            dice1, dice2, dice3 = self._generate_dice_for_total(target_total)
        else:
            # Tạo kết quả ngẫu nhiên hoặc thua
            if bet_type and not should_win:
                # Tạo kết quả thua
                if bet_type == "TÀI":
                    # Tạo tổng từ 4-10 để thua TÀI
                    target_total = random.randint(4, 10)
                else:  # XỈU
                    # Tạo tổng từ 11-17 để thua XỈU
                    target_total = random.randint(11, 17)
                
                dice1, dice2, dice3 = self._generate_dice_for_total(target_total)
            else:
                # Kết quả hoàn toàn ngẫu nhiên
                dice1 = random.randint(1, 6)
                dice2 = random.randint(1, 6)
                dice3 = random.randint(1, 6)
        
        total = dice1 + dice2 + dice3
        
        # Tài (11-17), Xỉu (4-10)
        result = "TÀI" if total >= 11 else "XỈU"
        
        return dice1, dice2, dice3, total, result
    
    def _generate_dice_for_total(self, target_total: int) -> tuple:
        """
        Tạo 3 xúc xắc có tổng bằng target_total
        
        Args:
            target_total: Tổng mong muốn (4-18)
            
        Returns:
            tuple: (dice1, dice2, dice3)
        """
        # Đảm bảo target_total trong khoảng hợp lệ
        target_total = max(3, min(18, target_total))
        
        # Tạo 2 xúc xắc đầu ngẫu nhiên
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        # Tính xúc xắc thứ 3 để đạt target_total
        dice3 = target_total - dice1 - dice2
        
        # Đảm bảo dice3 trong khoảng 1-6
        if dice3 < 1:
            # Điều chỉnh lại nếu dice3 quá nhỏ
            dice1 = random.randint(1, min(6, target_total - 2))
            dice2 = random.randint(1, min(6, target_total - dice1 - 1))
            dice3 = target_total - dice1 - dice2
        elif dice3 > 6:
            # Điều chỉnh lại nếu dice3 quá lớn
            dice1 = random.randint(max(1, target_total - 12), 6)
            dice2 = random.randint(max(1, target_total - dice1 - 6), 6)
            dice3 = target_total - dice1 - dice2
        
        # Đảm bảo tất cả xúc xắc trong khoảng 1-6
        dice1 = max(1, min(6, dice1))
        dice2 = max(1, min(6, dice2))
        dice3 = max(1, min(6, dice3))
        
        return dice1, dice2, dice3
    
    def create_rolling_embed(self, user: discord.User, bet_type: str, bet_amount: int, step: int = 0) -> discord.Embed:
        """
        Tạo embed hiển thị animation quay xúc xắc
        
        Args:
            user: Người chơi
            bet_type: Loại cược (TÀI/XỈU)
            bet_amount: Số tiền cược
            step: Bước animation (0-6)
        
        Returns:
            discord.Embed: Embed animation
        """
        # Animation frames cho xúc xắc - tạo hiệu ứng quay thực tế
        dice_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
        
        if step == 0:
            dice_frames = ["🎲", "🎲", "🎲"]
        elif step == 1:
            dice_frames = ["🎯", "🎲", "🎲"]
        elif step == 2:
            dice_frames = [random.choice(dice_emojis), "🎯", "🎲"]
        elif step == 3:
            dice_frames = [random.choice(dice_emojis), random.choice(dice_emojis), "🎯"]
        elif step == 4:
            dice_frames = ["🎲", "🎲", "🎲"]
        elif step == 5:
            dice_frames = [random.choice(dice_emojis), "🎲", "🎲"]
        else:  # step == 6
            dice_frames = ["🎲", "🎲", "🎲"]
        
        embed = discord.Embed(
            title="🎲 TÀIXỈU - Đang quay xúc xắc...",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name=f"{user.display_name}",
            icon_url=user.avatar.url if user.avatar else user.default_avatar.url
        )
        
        # Hiển thị xúc xắc đang quay
        dice_display = f"{dice_frames[0]} {dice_frames[1]} {dice_frames[2]}"
        
        embed.add_field(
            name="🎲 Xúc xắc đang quay",
            value=f"{dice_display}\n**Đang tính toán...**",
            inline=True
        )
        
        # Thông tin cược
        bet_emoji = "🔴" if bet_type.upper() == "TÀI" else "🔵"
        embed.add_field(
            name="💰 Cược của bạn",
            value=f"{bet_emoji} **{bet_type.upper()}**\n{bet_amount:,} điểm",
            inline=True
        )
        
        # Animation text
        animation_texts = [
            "🎯 Chuẩn bị quay...",
            "🎲 Xúc xắc đang bay...",
            "⚡ Sắp có kết quả...",
            "🔥 Căng thẳng quá...",
            "💫 Gần xong rồi...",
            "🎊 Sắp ra kết quả...",
            "✨ Hoàn thành!"
        ]
        
        embed.add_field(
            name="⏳ Trạng thái",
            value=animation_texts[min(step, len(animation_texts) - 1)],
            inline=True
        )
        
        embed.set_footer(text="Vui lòng chờ kết quả... 🎲")
        
        return embed
    
    def create_game_embed(self, user: discord.User, bet_type: str, bet_amount: int, 
                         dice1: int, dice2: int, dice3: int, total: int, 
                         result: str, is_win: bool, money_change: int, 
                         current_money: int) -> discord.Embed:
        """
        Tạo embed hiển thị kết quả game
        
        Returns:
            discord.Embed: Embed kết quả game
        """
        # Màu embed dựa trên kết quả
        color = discord.Color.green() if is_win else discord.Color.red()
        
        # Title
        title = "🎲 TÀIXỈU - " + ("🎉 THẮNG!" if is_win else "💸 THUA!")
        
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.now()
        )
        
        # Thông tin người chơi
        embed.set_author(
            name=f"{user.display_name}",
            icon_url=user.avatar.url if user.avatar else user.default_avatar.url
        )
        
        # Kết quả xúc xắc
        dice_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
        dice_display = f"{dice_emojis[dice1-1]} {dice_emojis[dice2-1]} {dice_emojis[dice3-1]}"
        
        embed.add_field(
            name="🎲 Kết quả xúc xắc",
            value=f"{dice_display}\n**Tổng: {total} điểm**",
            inline=True
        )
        
        # Kết quả game
        result_emoji = "🔴" if result == "TÀI" else "🔵"
        embed.add_field(
            name="🎯 Kết quả",
            value=f"{result_emoji} **{result}**\n({total} điểm)",
            inline=True
        )
        
        # Thông tin cược
        bet_emoji = "🔴" if bet_type.upper() == "TÀI" else "🔵"
        embed.add_field(
            name="💰 Cược của bạn",
            value=f"{bet_emoji} **{bet_type.upper()}**\n{bet_amount:,} điểm",
            inline=True
        )
        
        # Kết quả tiền với mô tả rõ ràng
        if is_win:
            money_emoji = "💰"
            money_text = f"+{money_change:,}"
            money_desc = "CỘNG TIỀN"
        else:
            money_emoji = "💸"
            money_text = f"{money_change:,}"
            money_desc = "TRỪ TIỀN"
        
        embed.add_field(
            name=f"{money_emoji} {money_desc}",
            value=f"**{money_text}** điểm",
            inline=True
        )
        
        embed.add_field(
            name="🏦 Số dư hiện tại",
            value=f"**{current_money:,}** điểm",
            inline=True
        )
        
        # Tỷ lệ thắng hiện tại dựa trên số tiền THỰC TẾ từ shared wallet
        # Xóa hiển thị tỷ lệ thắng
        
        # Thống kê game
        user_stats = self.player_data.get(str(user.id), {})
        total_games = user_stats.get('total_games', 0)
        wins = user_stats.get('wins', 0)
        
        embed.add_field(
            name="📊 Thống kê",
            value=f"Thắng: **{wins}** trận\nTổng: **{total_games}** trận",
            inline=True
        )
        
        # Footer với hướng dẫn
        embed.set_footer(text="Sử dụng: ;taixiu tai/xiu <số tiền> • Tài: 11-17 điểm • Xỉu: 4-10 điểm")
        
        return embed
    
    def create_stats_embed(self, user: discord.User, guild_permissions=None) -> discord.Embed:
        """
        Tạo embed thống kê người chơi
        
        Returns:
            discord.Embed: Embed thống kê
        """
        user_id_str = str(user.id)
        
        if user_id_str not in self.player_data:
            # Tạo tài khoản mới
            self.get_player_money(user.id)
        
        stats = self.player_data[user_id_str]
        
        embed = discord.Embed(
            title="📊 Thống kê Tài Xỉu",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name=f"{user.display_name}",
            icon_url=user.avatar.url if user.avatar else user.default_avatar.url
        )
        
        # Thông tin cơ bản - hiển thị số tiền THỰC TẾ từ shared wallet
        is_admin = guild_permissions and self.is_admin(user.id, guild_permissions)
        actual_money = shared_wallet.get_balance(user.id)
        money_display = f"**{actual_money:,}** điểm"
        if is_admin:
            money_display += " 👑"
        
        embed.add_field(
            name="💰 Số dư hiện tại",
            value=money_display,
            inline=True
        )
        
        embed.add_field(
            name="🎮 Tổng số trận",
            value=f"**{stats['total_games']}** trận",
            inline=True
        )
        
        # Thống kê thắng thua
        embed.add_field(
            name="📈 Kết quả",
            value=f"Thắng: **{stats['wins']}**\nThua: **{stats['losses']}**",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Số trận thắng",
            value=f"**{stats['wins']}** trận",
            inline=True
        )
        
        embed.add_field(
            name="💔 Số trận thua",
            value=f"**{stats['losses']}** trận",
            inline=True
        )
        
        # Thống kê tiền
        total_profit = stats['total_win'] - stats['total_bet']
        profit_emoji = "📈" if total_profit >= 0 else "📉"
        profit_text = f"+{total_profit:,}" if total_profit >= 0 else f"{total_profit:,}"
        
        embed.add_field(
            name=f"{profit_emoji} Lãi/Lỗ tổng",
            value=f"**{profit_text}** điểm",
            inline=True
        )
        
        embed.add_field(
            name="💸 Tổng cược",
            value=f"**{stats['total_bet']:,}** điểm",
            inline=True
        )
        
        embed.add_field(
            name="💰 Tổng thắng",
            value=f"**{stats['total_win']:,}** điểm",
            inline=True
        )
        
        # Thời gian
        created_date = datetime.fromisoformat(stats['created_at']).strftime("%d/%m/%Y")
        last_played_date = datetime.fromisoformat(stats['last_played']).strftime("%d/%m/%Y %H:%M")
        
        embed.add_field(
            name="📅 Ngày tạo",
            value=created_date,
            inline=True
        )
        
        embed.add_field(
            name="⏰ Lần chơi cuối",
            value=last_played_date,
            inline=True
        )
        
        embed.add_field(
            name="🎯 Cấu hình game",
            value="Cược: **> 0** (không giới hạn tối đa)\nCó thể cược `all` để đặt hết",
            inline=True
        )
        
        embed.set_footer(text="Sử dụng: ;taixiu tai/xiu <số tiền> để chơi")
        
        return embed
    
    async def taixiu_stats_command(self, ctx, user: discord.Member = None):
        """Command để xem thống kê tài xỉu"""
        try:
            target_user = user or ctx.author
            embed = self.create_stats_embed(target_user)
            await ctx.reply(embed=embed, mention_author=True)
        except Exception as e:
            logger.error(f"Error in taixiu_stats_command: {e}")
            await ctx.reply("❌ Có lỗi xảy ra khi xem thống kê!", mention_author=True)
    
    def register_commands(self) -> None:
        """
        Đăng ký các commands cho TaiXiu
        """
        @self.bot.command(name='taixiu', aliases=['tx'])
        async def taixiu_command(ctx, bet_type: str = None, bet_amount: str = None):
            """
            Lệnh chơi tài xỉu
            
            Usage: ;taixiu tai/xiu <số tiền>
            """
            try:
                # Kiểm tra tham số
                if not bet_type or not bet_amount:
                    embed = discord.Embed(
                        title="🎲 Hướng dẫn Tài Xỉu",
                        description="Chơi tài xỉu với 3 xúc xắc!",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📝 Cách chơi",
                        value="Sử dụng: `;taixiu tai/xiu <số tiền>`\n"
                              "Ví dụ: `;taixiu tai 1000`\n"
                              "**Đặt hết:** `;taixiu tai all`",
                        inline=False
                    )
                    embed.add_field(
                        name="🎯 Luật chơi",
                        value="🔴 **TÀI**: Tổng 3 xúc xắc từ 11-17 điểm\n"
                              "🔵 **XỈU**: Tổng 3 xúc xắc từ 4-10 điểm",
                        inline=False
                    )
                    embed.add_field(
                        name="💰 Cược",
                        value="Giới hạn: **> 0** điểm (không giới hạn tối đa)\n"
                              "Có thể cược tất cả số dư bằng lệnh `all`",
                        inline=False
                    )
                    embed.add_field(
                        name="💰 Cơ chế tiền",
                        value="🟢 **Thắng**: Cộng tiền bằng số tiền cược\n🔴 **Thua**: Trừ tiền bằng số tiền cược",
                        inline=False
                    )
                    embed.add_field(
                        name="📊 Xem thống kê",
                        value="Sử dụng: `;taixiustats` để xem thống kê cá nhân",
                        inline=False
                    )
                    embed.set_footer(text="User: 5,000 điểm • Admin: 100,000 điểm • Không được cược vượt số dư!")
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Xử lý lệnh stats
                if bet_type.lower() == 'stats':
                    embed = self.create_stats_embed(ctx.author, ctx.author.guild_permissions)
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra bet_type hợp lệ
                if bet_type.lower() not in ['tai', 'tài', 'xiu', 'xỉu']:
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description="Vui lòng chọn **tai** hoặc **xiu**!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Ví dụ",
                        value="`/taixiu tai 1000` hoặc `/taixiu xiu 500`",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra xem user có đang chơi game không
                if self.is_user_playing(ctx.author.id):
                    embed = discord.Embed(
                        title="⏳ Game đang chạy",
                        description="Bạn đang có một ván tài xỉu chưa hoàn thành!\nVui lòng chờ ván hiện tại kết thúc trước khi bắt đầu ván mới.",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="💡 Lưu ý",
                        value="Mỗi người chơi chỉ có thể chơi một ván tại một thời điểm để tránh xung đột.",
                        inline=False
                    )
                    embed.set_footer(text="Vui lòng chờ khoảng 3-4 giây để ván hiện tại hoàn thành")
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Chuẩn hóa bet_type
                bet_type_normalized = "TÀI" if bet_type.lower() in ['tai', 'tài'] else "XỈU"
                
                # Parse bet amount với hỗ trợ "all" và auto-adjust
                bet_amount_int, is_adjusted, parse_message = shared_wallet.parse_bet_amount(ctx.author.id, bet_amount)
                
                # Kiểm tra lỗi parse
                if bet_amount_int <= 0:
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description=parse_message if parse_message else "Số tiền không hợp lệ!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Hiển thị thông báo nếu đã điều chỉnh
                if is_adjusted and parse_message:
                    await ctx.send(f"{ctx.author.mention} {parse_message}")
                
                # Bắt đầu game cho user (thêm vào active games)
                if not self.start_game_for_user(ctx.author.id):
                    # Nếu không thể bắt đầu game (user đã có game chạy)
                    embed = discord.Embed(
                        title="⚠️ Lỗi hệ thống",
                        description="Không thể bắt đầu game. Vui lòng thử lại!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Bắt đầu animation quay xúc xắc 3 giây
                rolling_embed = self.create_rolling_embed(ctx.author, bet_type_normalized, bet_amount_int, 0)
                message = await ctx.reply(embed=rolling_embed, mention_author=True)
                
                try:
                    # Animation 3 giây với 6 frames (mỗi frame 0.5 giây)
                    for step in range(1, 7):
                        await asyncio.sleep(0.5)  # Chờ 0.5 giây
                        rolling_embed = self.create_rolling_embed(ctx.author, bet_type_normalized, bet_amount_int, step)
                        try:
                            await message.edit(embed=rolling_embed)
                        except discord.NotFound:
                            # Nếu message bị xóa, thoát khỏi animation nhưng vẫn kết thúc game
                            break
                        except discord.Forbidden:
                            # Nếu không có quyền edit, tiếp tục
                            pass
                    
                    # Thực hiện game với tỷ lệ thắng tùy chỉnh
                    is_admin_player = self.is_admin(ctx.author.id, ctx.author.guild_permissions)
                    dice1, dice2, dice3, total, result = self.roll_dice(bet_type_normalized, is_admin_player, ctx.author.id)
                    is_win = (bet_type_normalized == result)
                    
                    # Tính toán tiền thắng/thua rõ ràng
                    if is_win:
                        money_change = bet_amount_int  # THẮNG: Cộng tiền bằng số tiền cược
                        logger.info(f"Player {ctx.author} WON: +{bet_amount_int} điểm")
                    else:
                        money_change = -bet_amount_int  # THUA: Trừ tiền bằng số tiền cược
                        logger.info(f"Player {ctx.author} LOST: -{bet_amount_int} điểm")
                    
                    # Cập nhật tiền người chơi
                    self.update_player_money(ctx.author.id, money_change, is_win, bet_amount_int, ctx.author.guild_permissions)
                    new_money = self.get_player_money(ctx.author.id, ctx.author.guild_permissions)
                    
                    # Tạo và gửi embed kết quả cuối cùng
                    final_embed = self.create_game_embed(
                        ctx.author, bet_type_normalized, bet_amount_int,
                        dice1, dice2, dice3, total, result,
                        is_win, money_change, new_money
                    )
                    
                    # Cập nhật message với kết quả cuối cùng
                    try:
                        await message.edit(embed=final_embed)
                    except discord.NotFound:
                        # Nếu message bị xóa, gửi message mới
                        await ctx.send(embed=final_embed)
                    except discord.Forbidden:
                        # Nếu không có quyền edit, gửi message mới
                        await ctx.send(embed=final_embed)
                    
                    # Log kết quả
                    admin_status = "admin" if is_admin_player else "user"
                    logger.info(f"TaiXiu game: {ctx.author} ({admin_status}) "
                               f"bet {bet_amount_int} on {bet_type_normalized}, result: {result} ({total}), "
                               f"{'won' if is_win else 'lost'} {abs(money_change)}")
                    
                finally:
                    # Luôn kết thúc game cho user (xóa khỏi active games)
                    self.end_game_for_user(ctx.author.id)
                
            except Exception as e:
                # Đảm bảo user được xóa khỏi active games nếu có lỗi
                self.end_game_for_user(ctx.author.id)
                logger.error(f"Lỗi trong taixiu command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi xử lý game. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='taixiumoney', aliases=['txmoney'])
        async def taixiu_money_command(ctx, action: str = None, user: discord.Member = None, amount: str = None):
            """
            Quản lý tiền tài xỉu (chỉ admin)
            
            Usage: 
            - /taixiumoney add @user <số tiền>
            - /taixiumoney remove @user <số tiền>
            - /taixiumoney set @user <số tiền>
            - /taixiumoney reset @user
            """
            try:
                # Kiểm tra quyền sử dụng dynamic permission system
                if hasattr(self.bot_instance, 'permission_manager'):
                    has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'taixiumoney')
                    if not has_permission:
                        embed = discord.Embed(
                            title="❌ Không có quyền",
                            description="Bạn không có quyền sử dụng lệnh này!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                else:
                    # Fallback: Kiểm tra quyền admin nếu không có permission system
                    if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                        embed = discord.Embed(
                            title="❌ Không có quyền",
                            description="Chỉ admin mới có thể sử dụng lệnh này!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                
                if not action:
                    embed = discord.Embed(
                        title="💰 Quản lý tiền Tài Xỉu",
                        description="Lệnh dành cho admin quản lý tiền người chơi",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📝 Cách sử dụng",
                        value="`/taixiumoney add @user <số tiền>` - Thêm tiền\n"
                              "`/taixiumoney remove @user <số tiền>` - Trừ tiền\n"
                              "`/taixiumoney set @user <số tiền>` - Đặt số tiền\n"
                              "`/taixiumoney reset @user` - Reset về 5,000",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                if action.lower() == 'reset' and user:
                    # Reset tiền về mặc định
                    user_id_str = str(user.id)
                    if user_id_str in self.player_data:
                        self.player_data[user_id_str]['money'] = self.starting_money
                        self.save_player_data()
                    else:
                        self.get_player_money(user.id)  # Tạo tài khoản mới
                    
                    embed = discord.Embed(
                        title="✅ Reset thành công",
                        description=f"Đã reset tiền của {user.mention} về **{self.starting_money:,}** điểm",
                        color=discord.Color.green()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                if not user or not amount:
                    embed = discord.Embed(
                        title="❌ Thiếu tham số",
                        description="Vui lòng cung cấp đầy đủ thông tin!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Ví dụ",
                        value="`/taixiumoney add @user 1000`",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                try:
                    amount_int = int(amount.replace(',', '').replace('.', ''))
                except ValueError:
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description="Số tiền phải là số nguyên!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Lấy số tiền hiện tại
                current_money = self.get_player_money(user.id)
                
                if action.lower() == 'add':
                    new_money = current_money + amount_int
                    self.player_data[str(user.id)]['money'] = new_money
                    action_text = f"Đã thêm **{amount_int:,}** điểm"
                elif action.lower() == 'remove':
                    new_money = max(0, current_money - amount_int)
                    self.player_data[str(user.id)]['money'] = new_money
                    action_text = f"Đã trừ **{amount_int:,}** điểm"
                elif action.lower() == 'set':
                    new_money = max(0, amount_int)
                    self.player_data[str(user.id)]['money'] = new_money
                    action_text = f"Đã đặt số tiền thành **{amount_int:,}** điểm"
                else:
                    embed = discord.Embed(
                        title="❌ Lệnh không hợp lệ",
                        description="Chỉ hỗ trợ: add, remove, set, reset",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                self.save_player_data()
                
                embed = discord.Embed(
                    title="✅ Cập nhật thành công",
                    description=f"{action_text} cho {user.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="💰 Số dư mới",
                    value=f"**{new_money:,}** điểm",
                    inline=True
                )
                embed.add_field(
                    name="📊 Thay đổi",
                    value=f"{current_money:,} → {new_money:,}",
                    inline=True
                )
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"Admin {ctx.author} {action} {amount_int} money for user {user}")
                
            except Exception as e:
                logger.error(f"Lỗi trong taixiumoney command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi xử lý lệnh. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='give')
        async def give_money_command(ctx, user: discord.Member = None, amount: str = None):
            """
            Lệnh give tiền cho member (chỉ admin)
            
            Usage: ;give @user <số tiền>
            """
            try:
                # Kiểm tra quyền sử dụng dynamic permission system
                if hasattr(self.bot_instance, 'permission_manager'):
                    has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'give')
                    if not has_permission:
                        embed = discord.Embed(
                            title="❌ Không có quyền",
                            description="Bạn không có quyền sử dụng lệnh này!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                else:
                    # Fallback: Kiểm tra quyền admin nếu không có permission system
                    if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                        embed = discord.Embed(
                            title="❌ Không có quyền",
                            description="Chỉ admin mới có thể sử dụng lệnh này!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                
                if not user or not amount:
                    embed = discord.Embed(
                        title="💰 Give Tiền Tài Xỉu",
                        description="Lệnh dành cho admin give tiền cho member",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📝 Cách sử dụng",
                        value="`/give @user <số tiền>` - Give tiền cho user\n"
                              "Ví dụ: `/give @member 5000`",
                        inline=False
                    )
                    embed.add_field(
                        name="💡 Lưu ý",
                        value="• Admin bắt đầu với 100,000 điểm\n"
                              "• Admin có thể give cho chính mình\n"
                              "• Số tiền phải là số nguyên dương\n"
                              "• **Admin**: Không giới hạn 👑\n"
                              "• **User thường**: Tối đa 36M xu/ngày 📊",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Admin có thể give cho chính mình, user thường thì không
                if user.id == ctx.author.id and not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description="User thường không thể give tiền cho chính mình!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="💡 Gợi ý",
                        value="Chỉ admin mới có thể give tiền cho chính mình.",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Validate số tiền
                try:
                    amount_int = int(amount.replace(',', '').replace('.', ''))
                    if amount_int <= 0:
                        raise ValueError("Số tiền phải dương")
                except ValueError:
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description="Số tiền phải là số nguyên dương!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Ví dụ",
                        value="`/give @user 1000` hoặc `/give @user 5000`",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra quyền admin
                is_admin = self.bot_instance.is_admin(ctx.author.id) or ctx.author.id == self.bot_instance.supreme_admin_id
                
                if not is_admin:
                    # User thường: Kiểm tra daily limit 36M xu
                    daily_limit = 36000000
                    today_given = self.get_daily_give_amount(ctx.author.id)
                    
                    if today_given + amount_int > daily_limit:
                        remaining = daily_limit - today_given
                        embed = discord.Embed(
                            title="❌ Vượt quá giới hạn hàng ngày",
                            description=f"User thường chỉ được give tối đa **{daily_limit:,}** xu/ngày!",
                            color=discord.Color.red()
                        )
                        embed.add_field(
                            name="📊 Thống kê hôm nay:",
                            value=f"• **Đã give:** {today_given:,} xu\n• **Còn lại:** {remaining:,} xu\n• **Đang cố give:** {amount_int:,} xu",
                            inline=False
                        )
                        embed.add_field(
                            name="💡 Gợi ý:",
                            value=f"Bạn chỉ có thể give tối đa **{remaining:,}** xu nữa hôm nay.",
                            inline=False
                        )
                        embed.add_field(
                            name="👑 Lưu ý:",
                            value="Admin không bị giới hạn này.",
                            inline=False
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                else:
                    # Admin: Không giới hạn, chỉ thông báo
                    logger.info(f"Admin {ctx.author.id} giving {amount_int:,} xu (no limit)")
                
                # Kiểm tra số dư người gửi
                sender_balance = shared_wallet.get_balance(ctx.author.id)
                if amount_int > sender_balance:
                    embed = discord.Embed(
                        title="❌ Không đủ tiền",
                        description=f"Bạn chỉ có **{sender_balance:,}** xu!\nKhông thể give **{amount_int:,}** xu.",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Trừ tiền từ người gửi
                shared_wallet.subtract_balance(ctx.author.id, amount_int)
                sender_new_balance = shared_wallet.get_balance(ctx.author.id)
                
                # Lấy số dư hiện tại của người nhận
                current_money = self.get_player_money(user.id)
                
                # Give tiền cho người nhận
                self.give_money_to_player(user.id, amount_int)
                new_money = self.get_player_money(user.id)
                
                # Tracking daily give amount cho user thường (không phải admin)
                if not is_admin:
                    self.add_daily_give_amount(ctx.author.id, amount_int)
                
                # Tạo embed thông báo thành công
                embed = discord.Embed(
                    title="💰 Give Tiền Thành Công!",
                    description=f"Đã give **{amount_int:,}** điểm cho {user.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.set_author(
                    name=f"Admin: {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                
                embed.set_thumbnail(
                    url=user.avatar.url if user.avatar else user.default_avatar.url
                )
                
                embed.add_field(
                    name="🎯 Người nhận",
                    value=f"{user.mention}\n({user.display_name})",
                    inline=True
                )
                
                embed.add_field(
                    name="💸 Số tiền give",
                    value=f"**+{amount_int:,}** điểm",
                    inline=True
                )
                
                embed.add_field(
                    name="🏦 Số dư người nhận",
                    value=f"**{new_money:,}** điểm",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Thay đổi người nhận",
                    value=f"{current_money:,} → {new_money:,}",
                    inline=True
                )
                
                embed.add_field(
                    name="💸 Số dư người gửi",
                    value=f"**{sender_new_balance:,}** xu (đã trừ {amount_int:,})",
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Thời gian",
                    value=datetime.now().strftime("%H:%M:%S"),
                    inline=True
                )
                
                embed.add_field(
                    name="💡 Gợi ý", 
                    value="Sử dụng `/taixiu tai/xiu <số tiền>` để chơi!",
                    inline=True
                )
                
                embed.set_footer(text=f"Give by {ctx.author.display_name} • Tài Xỉu System")
                
                await ctx.reply(embed=embed, mention_author=True)
                
                # Gửi DM thông báo cho user nhận tiền (nếu có thể)
                try:
                    dm_embed = discord.Embed(
                        title="🎉 Bạn đã nhận được tiền!",
                        description=f"Admin **{ctx.author.display_name}** đã give cho bạn **{amount_int:,}** điểm tài xỉu!",
                        color=discord.Color.gold()
                    )
                    dm_embed.add_field(
                        name="💰 Số dư hiện tại",
                        value=f"**{new_money:,}** điểm",
                        inline=True
                    )
                    dm_embed.add_field(
                        name="🎲 Bắt đầu chơi",
                        value="Sử dụng `/taixiu tai/xiu <số tiền>` để chơi!",
                        inline=False
                    )
                    dm_embed.set_footer(text=f"Server: {ctx.guild.name}")
                    
                    await user.send(embed=dm_embed)
                    logger.info(f"Sent DM notification to {user} about money gift")
                except:
                    # Không quan trọng nếu không gửi được DM
                    pass
                
                logger.info(f"Admin {ctx.author} gave {amount_int} money to user {user}")
                
            except Exception as e:
                logger.error(f"Lỗi trong give command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi give tiền. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='conbac', aliases=['gambler'])
        async def gambling_role_command(ctx):
            """
            Lệnh nhận role con bạc và 100k cash (lấy từ tài khoản Supreme Admin)
            
            Usage: ;conbac
            """
            try:
                # Kiểm tra xem user đã có role "Con Bạc" chưa
                gambler_role = discord.utils.get(ctx.guild.roles, name="Con Bạc")
                
                # Tạo role nếu chưa có
                if not gambler_role:
                    try:
                        gambler_role = await ctx.guild.create_role(
                            name="Con Bạc",
                            color=discord.Color.gold(),
                            reason="Role cho người chơi tài xỉu"
                        )
                        logger.info(f"Created 'Con Bạc' role in guild {ctx.guild.name}")
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="❌ Lỗi quyền",
                            description="Bot không có quyền tạo role trong server này!",
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                
                # Kiểm tra user đã có role chưa
                if gambler_role in ctx.author.roles:
                    embed = discord.Embed(
                        title="⚠️ Đã có role",
                        description="Bạn đã có role **Con Bạc** rồi!",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="💰 Số dư hiện tại",
                        value=f"**{self.get_player_money(ctx.author.id):,}** điểm",
                        inline=True
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra Supreme Admin có đủ tiền không
                supreme_admin_id = self.bot_instance.supreme_admin_id
                if not supreme_admin_id:
                    embed = discord.Embed(
                        title="❌ Lỗi hệ thống",
                        description="Chưa có Supreme Admin được thiết lập!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Import shared_wallet để kiểm tra số dư Supreme Admin
                from utils.shared_wallet import shared_wallet
                supreme_balance = shared_wallet.get_balance(supreme_admin_id)
                reward_amount = 100000  # 100k cash
                
                if supreme_balance < reward_amount:
                    embed = discord.Embed(
                        title="❌ Không đủ tiền",
                        description=f"Supreme Admin chỉ có **{supreme_balance:,}** xu, không đủ để cấp **{reward_amount:,}** xu!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Trừ tiền từ Supreme Admin
                shared_wallet.subtract_balance(supreme_admin_id, reward_amount)
                supreme_new_balance = shared_wallet.get_balance(supreme_admin_id)
                
                # Cấp role cho user
                try:
                    await ctx.author.add_roles(gambler_role, reason="Nhận role Con Bạc")
                except discord.Forbidden:
                    # Hoàn tiền nếu không thể cấp role
                    shared_wallet.add_balance(supreme_admin_id, reward_amount)
                    embed = discord.Embed(
                        title="❌ Lỗi quyền",
                        description="Bot không có quyền cấp role cho bạn!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Cấp tiền cho user
                user_old_balance = self.get_player_money(ctx.author.id)
                self.give_money_to_player(ctx.author.id, reward_amount)
                user_new_balance = self.get_player_money(ctx.author.id)
                
                # Tạo embed thông báo thành công
                embed = discord.Embed(
                    title="🎰 Chào mừng Con Bạc mới!",
                    description=f"Chúc mừng {ctx.author.mention} đã nhận được role **Con Bạc**!",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                embed.set_author(
                    name=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/741395075694338108.png")
                
                embed.add_field(
                    name="🎭 Role nhận được",
                    value=f"**{gambler_role.name}** {gambler_role.mention}",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Tiền thưởng",
                    value=f"**+{reward_amount:,}** điểm",
                    inline=True
                )
                
                embed.add_field(
                    name="🏦 Số dư mới",
                    value=f"**{user_new_balance:,}** điểm",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Thay đổi số dư",
                    value=f"{user_old_balance:,} → {user_new_balance:,}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎲 Bắt đầu chơi",
                    value="Sử dụng `;taixiu tai/xiu <số tiền>` để chơi!",
                    inline=True
                )
                
                embed.add_field(
                    name="⚠️ Lưu ý",
                    value="Role này chỉ nhận được **1 lần duy nhất**!",
                    inline=True
                )
                
                embed.set_footer(text=f"Tiền được chuyển từ tài khoản Supreme Admin • Số dư SA còn lại: {supreme_new_balance:,} xu")
                
                await ctx.reply(embed=embed, mention_author=True)
                
                # Gửi thông báo cho Supreme Admin (nếu có thể)
                try:
                    supreme_admin = self.bot.get_user(supreme_admin_id)
                    if supreme_admin:
                        admin_embed = discord.Embed(
                            title="💸 Thông báo chuyển tiền",
                            description=f"Đã chuyển **{reward_amount:,}** xu cho {ctx.author} ({ctx.author.mention}) để nhận role Con Bạc",
                            color=discord.Color.blue()
                        )
                        admin_embed.add_field(
                            name="🏦 Số dư còn lại",
                            value=f"**{supreme_new_balance:,}** xu",
                            inline=True
                        )
                        admin_embed.add_field(
                            name="📍 Server",
                            value=f"{ctx.guild.name}",
                            inline=True
                        )
                        admin_embed.set_footer(text="Hệ thống Con Bạc • Tự động chuyển tiền")
                        
                        await supreme_admin.send(embed=admin_embed)
                        logger.info(f"Sent notification to Supreme Admin about gambler role transfer")
                except:
                    # Không quan trọng nếu không gửi được thông báo
                    pass
                
                logger.info(f"User {ctx.author} received gambler role and {reward_amount} cash from Supreme Admin {supreme_admin_id}")
                
            except Exception as e:
                logger.error(f"Lỗi trong conbac command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi xử lý lệnh. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='resetuserdata', aliases=['resetdata'])
        async def reset_user_data_command(ctx):
            """
            Reset tất cả data của user (chỉ Supreme Admin)
            
            Usage: ;resetuserdata
            """
            try:
                # Chỉ Supreme Admin mới có thể sử dụng
                if ctx.author.id != self.bot_instance.supreme_admin_id:
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể reset data user!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Tạo embed xác nhận
                confirm_embed = discord.Embed(
                    title="⚠️ XÁC NHẬN RESET WALLET USER",
                    description="**CẢNH BÁO**: Hành động này sẽ xóa tất cả số dư xu của user!",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                
                confirm_embed.add_field(
                    name="📊 Dữ liệu sẽ bị xóa:",
                    value=(
                        "• **shared_wallet.json**: File lưu trữ số dư xu\n"
                        "• **Shared Wallet Memory**: Dữ liệu xu trong bộ nhớ\n"
                        "• **Tất cả số dư xu** của user sẽ về 0"
                    ),
                    inline=False
                )
                
                confirm_embed.add_field(
                    name="⚡ Tác động:",
                    value=(
                        "• Tất cả user sẽ về số dư 0 xu\n"
                        "• **Thống kê game KHÔNG bị ảnh hưởng**\n"
                        "• **KHÔNG THỂ HOÀN TÁC**"
                    ),
                    inline=False
                )
                
                confirm_embed.add_field(
                    name="✅ Xác nhận:",
                    value="Reply tin nhắn này với `CONFIRM RESET` để thực hiện",
                    inline=False
                )
                
                confirm_embed.set_footer(text="Supreme Admin Only • Không thể hoàn tác")
                
                confirm_message = await ctx.reply(embed=confirm_embed, mention_author=True)
                
                # Chờ xác nhận từ Supreme Admin
                def check(message):
                    return (message.author.id == ctx.author.id and 
                            message.reference and 
                            message.reference.message_id == confirm_message.id and
                            message.content.upper() == "CONFIRM RESET")
                
                try:
                    confirmation = await self.bot.wait_for('message', timeout=30.0, check=check)
                    
                    # Thực hiện reset wallet
                    reset_embed = discord.Embed(
                        title="🔄 Đang reset wallet user...",
                        description="Vui lòng chờ, đang reset tất cả số dư xu của user...",
                        color=discord.Color.yellow()
                    )
                    
                    status_message = await ctx.send(embed=reset_embed)
                    
                    # Chỉ xóa shared_wallet.json
                    files_reset = []
                    shared_wallet_file = 'data/shared_wallet.json'
                    
                    # Xóa file shared_wallet.json
                    if os.path.exists(shared_wallet_file):
                        try:
                            os.remove(shared_wallet_file)
                            files_reset.append("shared_wallet.json")
                            logger.info(f"Deleted file: {shared_wallet_file}")
                        except Exception as e:
                            logger.error(f"Could not delete {shared_wallet_file}: {e}")
                    
                    # Reset Shared Wallet trong memory
                    if hasattr(self.bot_instance, 'shared_wallet'):
                        shared_wallet.reset_all_balances()
                        files_reset.append("Shared Wallet (Memory)")
                    
                    logger.info(f"Reset completed. Files deleted: {files_reset}")
                    
                    # Tạo embed thành công
                    success_embed = discord.Embed(
                        title="✅ RESET WALLET USER THÀNH CÔNG!",
                        description="Đã reset tất cả số dư xu của user về 0",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    success_embed.add_field(
                        name="🗑️ Đã xóa:",
                        value="\n".join([f"• {file}" for file in files_reset]) if files_reset else "• Không có file nào cần xóa",
                        inline=False
                    )
                    
                    success_embed.add_field(
                        name="📊 Kết quả:",
                        value=(
                            "• Tất cả user về số dư 0 xu\n"
                            "• **Thống kê game được giữ nguyên**\n"
                            "• Chỉ reset wallet, không ảnh hưởng data khác"
                        ),
                        inline=False
                    )
                    
                    success_embed.add_field(
                        name="🔄 Tiếp theo:",
                        value="User có thể tiếp tục chơi với số dư khởi tạo, thống kê game vẫn được bảo toàn",
                        inline=False
                    )
                    
                    success_embed.set_footer(text=f"Reset by {ctx.author.display_name} • Supreme Admin")
                    
                    await status_message.edit(embed=success_embed)
                    
                    logger.info(f"Supreme Admin {ctx.author} reset user wallet. Files reset: {files_reset}")
                    
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        title="⏰ Hết thời gian",
                        description="Không nhận được xác nhận trong 30 giây. Hủy reset wallet.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=timeout_embed)
                    
            except Exception as e:
                logger.error(f"Lỗi trong reset wallet command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi reset wallet. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        logger.info("Đã đăng ký TaiXiu commands: taixiu, taixiumoney, give, conbac, resetuserdata")
