import discord
from discord.ext import commands
from .base import BaseCommand
import random
import json
import os
from datetime import datetime
import logging
from utils.shared_wallet import shared_wallet

logger = logging.getLogger(__name__)

class SlotCommands(BaseCommand):
    """Class chứa lệnh Slot Machine"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.data_file = "data/slot_data.json"
        self.slot_data = self.load_slot_data()
        
        # Tracking game đang chạy
        self.active_games = set()  # Set chứa user_id của những user đang có game chạy
        
        # Slot symbols với tỷ lệ xuất hiện khác nhau
        self.symbols = {
            "🍒": {"weight": 30, "multiplier": 2},    # Cherry - thường gặp, x2
            "🍋": {"weight": 25, "multiplier": 3},    # Lemon - x3
            "🍊": {"weight": 20, "multiplier": 4},    # Orange - x4
            "🍇": {"weight": 15, "multiplier": 5},    # Grape - x5
            "🔔": {"weight": 8, "multiplier": 10},    # Bell - hiếm, x10
            "💎": {"weight": 2, "multiplier": 50}     # Diamond - rất hiếm, x50
        }
        
        # Tạo weighted list
        self.weighted_symbols = []
        for symbol, data in self.symbols.items():
            self.weighted_symbols.extend([symbol] * data["weight"])
    
    def load_slot_data(self):
        """Load dữ liệu slot từ file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load slot data: {e}")
            return {}
    
    def save_slot_data(self):
        """Lưu dữ liệu slot vào file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.slot_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save slot data: {e}")
    
    def is_user_playing(self, user_id: int) -> bool:
        """Kiểm tra xem user có đang chơi game không"""
        return user_id in self.active_games
    
    def start_game_for_user(self, user_id: int) -> bool:
        """Bắt đầu game cho user (thêm vào active games)"""
        if user_id in self.active_games:
            return False
        self.active_games.add(user_id)
        logger.info(f"Started slot game for user {user_id}. Active games: {len(self.active_games)}")
        return True
    
    def end_game_for_user(self, user_id: int) -> None:
        """Kết thúc game cho user (xóa khỏi active games)"""
        if user_id in self.active_games:
            self.active_games.remove(user_id)
            logger.info(f"Ended slot game for user {user_id}. Active games: {len(self.active_games)}")
    
    def get_user_data(self, user_id):
        """Lấy dữ liệu user, tạo mới nếu chưa có"""
        user_id = str(user_id)
        if user_id not in self.slot_data:
            self.slot_data[user_id] = {
                'total_games': 0,
                'total_bet': 0,
                'total_won': 0,
                'biggest_win': 0,
                'jackpots': 0,
                'balance': 0,  # Thêm balance (sẽ sync từ shared wallet)
                'games_10m_plus': 0,  # Số game với cược >= 10M
                'created_at': datetime.now().isoformat()
            }
            self.save_slot_data()
        return self.slot_data[user_id]
    
    def spin_slots(self, user_id=None, force_win=False, force_lose=False, force_draw=False):
        """Quay slot machine với khả năng force win/lose/draw"""
        # Kiểm tra unluck system
        if user_id and hasattr(self.bot_instance, 'unluck_commands'):
            is_unlucky = self.bot_instance.unluck_commands.is_user_unlucky(user_id)
            if is_unlucky:
                # Tăng số game bị ảnh hưởng
                self.bot_instance.unluck_commands.increment_game_affected(user_id)
                force_lose = True
                logger.info(f"User {user_id} is unlucky - forcing slot loss")
        # Slot Machine: Dynamic win rate system
        if user_id and not force_lose and not force_win and not force_draw:
            # Kiểm tra admin
            is_admin = self.bot_instance.is_admin(user_id) or self.bot_instance.is_supreme_admin(user_id)
            
            # Lấy user data để check streak
            user_data = self.get_user_data(user_id)
            
            # Tính dynamic win rate: Base 40%, +20% mỗi lần thua liên tiếp
            base_rate = 0.4  # 40% base
            lose_streak = user_data.get('lose_streak', 0)
            dynamic_rate = min(base_rate + (lose_streak * 0.2), 0.9)  # Max 90%
            
            win_chance = random.random()
            if win_chance < dynamic_rate:
                force_win = True
                logger.info(f"User {user_id} - Dynamic rate {dynamic_rate*100:.0f}% (streak: {lose_streak}) - WIN!")
            else:
                logger.info(f"User {user_id} - Dynamic rate {dynamic_rate*100:.0f}% (streak: {lose_streak}) - LOSE")
        
        if force_lose:
            # Force lose: tạo kết quả thua (không có 3 of a kind hoặc jackpot)
            symbols = []
            for i in range(3):
                # Đảm bảo không có 3 giống nhau
                available_symbols = list(self.symbols.keys())
                if i == 2 and symbols[0] == symbols[1]:
                    # Nếu 2 symbol đầu giống nhau, symbol thứ 3 phải khác
                    available_symbols.remove(symbols[0])
                symbols.append(random.choice(available_symbols))
            return symbols, "LOSE"
        elif force_win and user_id:
            # Force win: Kiểm tra admin hay user
            is_admin = self.bot_instance.is_admin(user_id) or self.bot_instance.is_supreme_admin(user_id)
            
            if is_admin:
                # Admin: Kiểm tra loại thắng dựa trên log gần nhất
                # Nếu log gần nhất là jackpot thì tạo jackpot, ngược lại tạo thắng thường
                win_chance = random.random()
                if win_chance < 0.2:  # 20% trong 50% thắng là jackpot
                    return ["💎", "💎", "💎"], "JACKPOT"
                else:
                    # Thắng thường với 3 of a kind
                    winning_symbols = ["🍒", "🍋", "🍊"]
                    chosen_symbol = random.choice(winning_symbols)
                    return [chosen_symbol, chosen_symbol, chosen_symbol], "WIN"
            else:
                # User thường: Tạo 3 of a kind nhỏ (Cherry x2)
                return ["🍒", "🍒", "🍒"], "WIN"
        elif force_draw:
            # Force draw: KHÔNG CÒN HÒA - Chuyển thành thua
            symbols = []
            for i in range(3):
                # Đảm bảo không có 3 giống nhau và không có 2 giống nhau
                available_symbols = list(self.symbols.keys())
                if i >= 1 and symbols[0] in available_symbols:
                    available_symbols.remove(symbols[0])
                if i == 2 and len(symbols) > 1 and symbols[1] in available_symbols:
                    available_symbols.remove(symbols[1])
                symbols.append(random.choice(available_symbols))
            return symbols, "LOSE"
        else:
            # Normal spin: CŨNG LUÔN THUA
            symbols = []
            for i in range(3):
                # Đảm bảo không có 3 giống nhau và không có 2 giống nhau
                available_symbols = list(self.symbols.keys())
                if i >= 1 and symbols[0] in available_symbols:
                    available_symbols.remove(symbols[0])
                if i == 2 and len(symbols) > 1 and symbols[1] in available_symbols:
                    available_symbols.remove(symbols[1])
                symbols.append(random.choice(available_symbols))
            return symbols, "LOSE"
    
    def calculate_winnings(self, symbols, bet_amount, is_draw=False):
        """Tính tiền thắng - Admin jackpot x100, User 3 of a kind"""
        # Nếu là hòa, trả lại tiền cược
        if is_draw:
            return bet_amount, "DRAW"
        
        # Check for jackpot (3 diamonds) - CHỈ ADMIN MỚI CÓ THỂ ĐẠT ĐƯỢC
        if symbols == ["💎", "💎", "💎"]:
            return bet_amount * 100, "JACKPOT"
        
        # Check for 3 of a kind (cho user thường mỗi 30 ván)
        if symbols[0] == symbols[1] == symbols[2]:
            multiplier = self.symbols[symbols[0]]["multiplier"]
            return bet_amount * multiplier, "3_OF_KIND"
        
        # Tất cả trường hợp khác đều thua
        return 0, "LOSE"
    
    def update_user_stats(self, user_id, bet_amount, winnings, win_type):
        """Cập nhật thống kê user"""
        user_data = self.get_user_data(user_id)
        user_data['total_games'] += 1
        user_data['total_bet'] += bet_amount
        
        # Tracking game với cược >= 10M
        if bet_amount >= 10_000_000:
            if 'games_10m_plus' not in user_data:
                user_data['games_10m_plus'] = 0
            user_data['games_10m_plus'] += 1
        
        if winnings > 0 and win_type != "DRAW":
            user_data['total_won'] += winnings
            if winnings > user_data['biggest_win']:
                user_data['biggest_win'] = winnings
            if win_type == "JACKPOT":
                user_data['jackpots'] += 1
            
            # Reset lose streak khi thắng
            user_data['lose_streak'] = 0
            logger.info(f"User {user_id} won slot - reset lose streak to 0")
            
            # Weekly leaderboard đã bị xóa
        else:
            # Tăng lose streak khi thua
            current_streak = user_data.get('lose_streak', 0)
            user_data['lose_streak'] = current_streak + 1
            logger.info(f"User {user_id} lost slot - lose streak: {user_data['lose_streak']}")
        
        self.save_slot_data()
    
    def register_commands(self):
        """Register slot commands"""
        
        @self.bot.command(name='slot', aliases=['slots'])
        async def slot_machine(ctx, amount=None):
            """
            Slot Machine game
            Usage: ;slot <số tiền>
            """
            try:
                # Validate arguments
                if not amount:
                    embed = discord.Embed(
                        title="🎰 Slot Machine - Hướng dẫn",
                        description="Máy đánh bạc với 6 loại biểu tượng!",
                        color=discord.Color.purple(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="📋 Cách chơi",
                        value=(
                            "`;slot <số tiền>`\n"
                            "`;slot 100` - Đặt cược 100 xu\n"
                            "`;slot 500` - Đặt cược 500 xu"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="🎯 Biểu tượng",
                        value=(
                            "🍒 **Cherry** - Biểu tượng trang trí\n"
                            "🍋 **Lemon** - Biểu tượng trang trí\n"
                            "🍊 **Orange** - Biểu tượng trang trí\n"
                            "🍇 **Grape** - Biểu tượng trang trí\n"
                            "🔔 **Bell** - Biểu tượng trang trí\n"
                            "💎 **Diamond** - Biểu tượng trang trí"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="🏆 Jackpot",
                        value=(
                            "💎💎💎 = **x100 JACKPOT!**\n"
                            "Cơ hội rất hiếm nhưng giải thưởng khổng lồ!"
                        ),
                        inline=False
                    )
                    embed.set_footer(text="Chơi với ;slot <số tiền>")
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra xem user có đang chơi game không
                if self.is_user_playing(ctx.author.id):
                    embed = discord.Embed(
                        title="⏳ Game đang chạy",
                        description="Bạn đang có một ván slot machine chưa hoàn thành!\nVui lòng chờ ván hiện tại kết thúc trước khi bắt đầu ván mới.",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="💡 Lưu ý",
                        value="Mỗi người chơi chỉ có thể chơi một ván tại một thời điểm để tránh xung đột.",
                        inline=False
                    )
                    embed.set_footer(text="Vui lòng chờ ván hiện tại hoàn thành")
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Validate amount
                try:
                    bet_amount = int(amount)
                    if bet_amount <= 0:
                        await ctx.reply(
                            f"{ctx.author.mention} ❌ Số tiền phải lớn hơn 0!",
                            mention_author=True
                        )
                        return
                except ValueError:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Số tiền không hợp lệ!",
                        mention_author=True
                    )
                    return
                
                # Kiểm tra giới hạn max bet 250k
                if bet_amount > 250000:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Số tiền cược tối đa là 250,000 xu!",
                        mention_author=True
                    )
                    return
                
                # Check balance from shared wallet
                if not shared_wallet.has_sufficient_balance(ctx.author.id, bet_amount):
                    current_balance = shared_wallet.get_balance(ctx.author.id)
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Không đủ tiền! Số dư hiện tại: **{current_balance:,} xu**",
                        mention_author=True
                    )
                    return
                
                # Bắt đầu game cho user (thêm vào active games)
                if not self.start_game_for_user(ctx.author.id):
                    embed = discord.Embed(
                        title="⚠️ Lỗi hệ thống",
                        description="Không thể bắt đầu game. Vui lòng thử lại!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                try:
                    # Spin the slots
                    symbols, spin_result = self.spin_slots(ctx.author.id)
                    
                    # Tính tiền thắng dựa trên kết quả spin
                    if spin_result == "DRAW":
                        winnings, win_type = self.calculate_winnings(symbols, bet_amount, is_draw=True)
                    else:
                        winnings, win_type = self.calculate_winnings(symbols, bet_amount)
                
                    # Create result embed
                    if win_type == "JACKPOT":
                        color = discord.Color.gold()
                        result_text = "🎉 **JACKPOT! SIÊU THẮNG!** 🎉"
                    elif win_type == "DRAW":
                        color = discord.Color.blue()
                        result_text = "🤝 **HÒA - TRẢ LẠI TIỀN CƯỢC!**"
                    elif winnings > 0:
                        color = discord.Color.green()
                        if win_type == "3_OF_KIND":
                            result_text = "🎊 **3 GIỐNG NHAU!**"
                        else:
                            result_text = "✨ **2 GIỐNG NHAU!**"
                    else:
                        color = discord.Color.red()
                        result_text = "😢 **KHÔNG TRÚNG**"
                    
                    # Update shared wallet
                    if win_type == "DRAW":
                        # Hòa: không thay đổi số dư (đã trả lại tiền cược)
                        new_balance = shared_wallet.get_balance(ctx.author.id)
                    elif winnings > 0:
                        # Player wins: subtract bet, add winnings
                        shared_wallet.subtract_balance(ctx.author.id, bet_amount)
                        new_balance = shared_wallet.add_balance(ctx.author.id, winnings)
                    else:
                        # Player loses: just subtract bet
                        new_balance = shared_wallet.subtract_balance(ctx.author.id, bet_amount)
                    
                    # Update stats
                    self.update_user_stats(ctx.author.id, bet_amount, winnings, win_type)
                    
                    embed = discord.Embed(
                        title="🎰 Slot Machine",
                        description=result_text,
                        color=color,
                        timestamp=datetime.now()
                    )
                    
                    # Slot display
                    slot_display = f"┌─────────────┐\n│ {symbols[0]} │ {symbols[1]} │ {symbols[2]} │\n└─────────────┘"
                    embed.add_field(
                        name="🎲 Kết quả",
                        value=f"```{slot_display}```",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="💰 Tiền cược",
                        value=f"**{bet_amount:,} xu**",
                        inline=True
                    )
                    
                    if win_type == "DRAW":
                        embed.add_field(
                            name="🤝 Kết quả",
                            value=f"**Trả lại {bet_amount:,} xu**",
                            inline=True
                        )
                        embed.add_field(
                            name="💵 Lợi nhuận",
                            value="**±0 xu**",
                            inline=True
                        )
                    elif winnings > 0:
                        profit = winnings - bet_amount
                        embed.add_field(
                            name="🎁 Tiền thắng",
                            value=f"**{winnings:,} xu**",
                            inline=True
                        )
                        embed.add_field(
                            name="💵 Lợi nhuận",
                            value=f"**+{profit:,} xu**",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name="💸 Mất tiền",
                            value=f"**-{bet_amount:,} xu**",
                            inline=True
                        )
                        embed.add_field(
                            name="😔 Lợi nhuận",
                            value=f"**-{bet_amount:,} xu**",
                            inline=True
                        )
                    
                    embed.add_field(
                        name="💳 Số dư mới",
                        value=f"**{new_balance:,} xu**",
                        inline=False
                    )
                    
                    embed.set_author(
                        name=f"{ctx.author.display_name}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                    )
                    embed.set_footer(text="Chơi tiếp với ;slot <số tiền>")
                    
                    await ctx.reply(embed=embed, mention_author=True)
                    
                finally:
                    # Luôn kết thúc game cho user (xóa khỏi active games)
                    self.end_game_for_user(ctx.author.id)
                
            except Exception as e:
                # Đảm bảo user được xóa khỏi active games nếu có lỗi
                self.end_game_for_user(ctx.author.id)
                logger.error(f"Lỗi trong slot command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi chơi slot!",
                    mention_author=True
                )
        
        @self.bot.command(name='slotstats')
        async def slot_stats(ctx, user: discord.Member = None):
            """Xem thống kê slot"""
            try:
                target_user = user or ctx.author
                user_data = self.get_user_data(target_user.id)
                
                total_games = user_data['total_games']
                if total_games == 0:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ {target_user.display_name} chưa chơi slot lần nào!",
                        mention_author=True
                    )
                    return
                
                # Calculate stats
                total_profit = user_data['total_won'] - user_data['total_bet']
                
                embed = discord.Embed(
                    title="🎰 Thống Kê Slot Machine",
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                
                # Lấy số tiền THỰC TẾ từ shared wallet
                actual_balance = shared_wallet.get_balance(target_user.id)
                embed.add_field(
                    name="💰 Tài chính",
                    value=(
                        f"**Số dư:** {actual_balance:,} xu\n"
                        f"**Tổng cược:** {user_data['total_bet']:,} xu\n"
                        f"**Tổng thắng:** {user_data['total_won']:,} xu\n"
                        f"**Lợi nhuận:** {total_profit:+,} xu"
                    ),
                    inline=True
                )
                embed.add_field(
                    name="🎯 Thành tích",
                    value=(
                        f"**Tổng ván:** {total_games:,}\n"
                        f"**Thắng lớn nhất:** {user_data['biggest_win']:,} xu\n"
                        f"**Jackpots:** {user_data['jackpots']:,} lần\n"
                        f"**Tổng thua:** {total_games:,} ván"
                    ),
                    inline=True
                )
                
                embed.set_author(
                    name=target_user.display_name,
                    icon_url=target_user.avatar.url if target_user.avatar else None
                )
                embed.set_footer(text="Chơi với ;slot <số tiền>")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong slot stats command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem thống kê!",
                    mention_author=True
                )
        
        @self.bot.command(name='slotleaderboard')
        async def slot_leaderboard(ctx):
            """Bảng xếp hạng slot"""
            try:
                if not self.slot_data:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ Chưa có dữ liệu người chơi!",
                        mention_author=True
                    )
                    return
                
                # Sort by biggest win
                sorted_users = sorted(
                    self.slot_data.items(),
                    key=lambda x: x[1]['biggest_win'],
                    reverse=True
                )[:10]
                
                embed = discord.Embed(
                    title="🏆 Bảng Xếp Hạng Slot Machine",
                    description="Top 10 người thắng lớn nhất",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
                
                leaderboard_text = ""
                for i, (user_id, data) in enumerate(sorted_users):
                    try:
                        user = self.bot.get_user(int(user_id))
                        username = user.display_name if user else f"User {user_id}"
                        
                        # Lấy số tiền THỰC TẾ từ shared wallet
                        actual_balance = shared_wallet.get_balance(int(user_id))
                        leaderboard_text += (
                            f"{medals[i]} **{username}**\n"
                            f"🎰 Thắng lớn: {data['biggest_win']:,} xu | "
                            f"🏆 Jackpots: {data['jackpots']} | "
                            f"💰 Số dư: {actual_balance:,} xu\n\n"
                        )
                    except:
                        continue
                
                embed.description = leaderboard_text or "Không có dữ liệu"
                embed.set_footer(text="Chơi ;slot để tham gia bảng xếp hạng!")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong slot leaderboard command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem bảng xếp hạng!",
                    mention_author=True
                )
