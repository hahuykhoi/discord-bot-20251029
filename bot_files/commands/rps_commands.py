import discord
from discord.ext import commands
from .base import BaseCommand
import random
import json
import os
from datetime import datetime
import logging
import asyncio
from utils.shared_wallet import shared_wallet

logger = logging.getLogger(__name__)

class RPSCommands(BaseCommand):
    """Class chứa lệnh Rock Paper Scissors (Kéo Búa Bao)"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.data_file = "data/rps_data.json"
        self.rps_data = self.load_rps_data()
        
        # Tracking game đang chạy
        self.active_games = set()  # Set chứa user_id của những user đang có game chạy
        
        # Player data file riêng cho RPS
        self.player_data_file = 'data/rps_players.json'
        self.player_data = self.load_player_data()
    
    def load_rps_data(self):
        """Load dữ liệu RPS từ file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load RPS data: {e}")
            return {}
    
    def save_rps_data(self):
        """Lưu dữ liệu RPS vào file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.rps_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save RPS data: {e}")
    
    def load_player_data(self):
        """Load dữ liệu người chơi từ file JSON"""
        try:
            if os.path.exists(self.player_data_file):
                with open(self.player_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load player data: {e}")
            return {}
    
    def save_player_data(self):
        """Lưu dữ liệu người chơi vào file JSON"""
        try:
            os.makedirs(os.path.dirname(self.player_data_file), exist_ok=True)
            with open(self.player_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.player_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save player data: {e}")
    
    def is_user_playing(self, user_id: int) -> bool:
        """Kiểm tra xem user có đang chơi game không"""
        return user_id in self.active_games
    
    def start_game_for_user(self, user_id: int) -> bool:
        """Bắt đầu game cho user (thêm vào active games)"""
        if user_id in self.active_games:
            return False
        self.active_games.add(user_id)
        logger.info(f"Started RPS game for user {user_id}. Active games: {len(self.active_games)}")
        return True
    
    def end_game_for_user(self, user_id: int) -> None:
        """Kết thúc game cho user (xóa khỏi active games)"""
        if user_id in self.active_games:
            self.active_games.remove(user_id)
            logger.info(f"Ended RPS game for user {user_id}. Active games: {len(self.active_games)}")
    
    def get_user_data(self, user_id):
        """Lấy dữ liệu user, tạo mới nếu chưa có"""
        user_id = str(user_id)
        if user_id not in self.rps_data:
            self.rps_data[user_id] = {
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'total_bet': 0,
                'total_won': 0,
                'total_lost': 0,
                'balance': 0,  # Thêm balance (sẽ sync từ shared wallet)
                'games_10m_plus': 0,  # Số game với cược >= 10M
                'created_at': datetime.now().isoformat()
            }
            self.save_rps_data()
        return self.rps_data[user_id]
    
    def update_user_stats(self, user_id, result, bet_amount):
        """Cập nhật thống kê user"""
        user_data = self.get_user_data(user_id)
        user_data['total_games'] += 1
        user_data['total_bet'] += bet_amount
        
        # Tracking game với cược >= 10M
        if bet_amount >= 10_000_000:
            if 'games_10m_plus' not in user_data:
                user_data['games_10m_plus'] = 0
            user_data['games_10m_plus'] += 1
        
        if result == "win":
            user_data['wins'] += 1
            winnings = bet_amount * 2
            user_data['total_won'] += winnings
            
            # Reset lose streak khi thắng
            user_data['lose_streak'] = 0
            logger.info(f"User {user_id} won RPS - reset lose streak to 0")
            
            # Weekly leaderboard đã bị xóa
        elif result == "lose":
            user_data['losses'] += 1
            user_data['total_lost'] += bet_amount
            
            # Tăng lose streak khi thua
            current_streak = user_data.get('lose_streak', 0)
            user_data['lose_streak'] = current_streak + 1
            logger.info(f"User {user_id} lost RPS - lose streak: {user_data['lose_streak']}")
        else:  # draw
            user_data['draws'] += 1
            # Hòa không ảnh hưởng streak
        
        self.save_rps_data()
    
    def get_winner(self, player_choice, bot_choice):
        """Xác định người thắng"""
        if player_choice == bot_choice:
            return "draw"
        
        win_conditions = {
            "kéo": "bao",    # Kéo thắng bao
            "búa": "kéo",    # Búa thắng kéo
            "bao": "búa"     # Bao thắng búa
        }
        
        if win_conditions[player_choice] == bot_choice:
            return "win"
        else:
            return "lose"
    
    def get_emoji(self, choice):
        """Lấy emoji cho lựa chọn"""
        emojis = {
            "kéo": "✂️",
            "búa": "🔨", 
            "bao": "📄"
        }
        return emojis.get(choice, "❓")
    
    def register_commands(self):
        """Register RPS commands"""
        
        @self.bot.command(name='rps', aliases=['kbb', 'keobubao'])
        async def rock_paper_scissors(ctx, choice=None, amount=None):
            """
            Rock Paper Scissors game với buttons
            Usage: ;rps <số tiền>
            """
            try:
                # Kiểm tra xem user có đang chơi game không
                if self.is_user_playing(ctx.author.id):
                    embed = discord.Embed(
                        title="⏳ Game đang chạy",
                        description="Bạn đang có một ván RPS chưa hoàn thành!\nVui lòng chờ ván hiện tại kết thúc trước khi bắt đầu ván mới.",
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
                
                # Nếu không có argument, hiển thị hướng dẫn
                if not choice:
                    embed = discord.Embed(
                        title="✂️ Kéo Búa Bao - Hướng dẫn",
                        description="Trò chơi kéo búa bao cổ điển!",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="📋 Cách chơi",
                        value=(
                            "`;rps <số tiền>` - Bắt đầu ván mới\n"
                            "Sau đó chọn kéo/búa/bao bằng buttons"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="🎯 Luật chơi",
                        value=(
                            "✂️ **Kéo** thắng 📄 **Bao**\n"
                            "🔨 **Búa** thắng ✂️ **Kéo**\n"
                            "📄 **Bao** thắng 🔨 **Búa**"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="💰 Phần thưởng",
                        value="**Thắng:** x2 tiền cược\n**Hòa:** Hoàn lại tiền cược",
                        inline=False
                    )
                    embed.set_footer(text="Chơi với ;rps <số tiền>")
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Parse bet amount từ argument đầu tiên
                try:
                    bet_amount_int = int(choice)
                except ValueError:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Số tiền không hợp lệ! Sử dụng: `;rps <số tiền>`",
                        mention_author=True
                    )
                    return
                
                # Parse bet amount using shared wallet
                bet_amount, is_adjusted, parse_message = shared_wallet.parse_bet_amount(ctx.author.id, choice)
                
                # Kiểm tra lỗi parse
                if bet_amount <= 0:
                    await ctx.reply(
                        f"{ctx.author.mention} {parse_message if parse_message else '❌ Số tiền không hợp lệ!'}",
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
                
                # Hiển thị thông báo nếu đã điều chỉnh
                if is_adjusted and parse_message:
                    await ctx.send(f"{ctx.author.mention} {parse_message}")
                
                # Tạo embed hỏi lựa chọn
                embed = discord.Embed(
                    title="✂️ Kéo Búa Bao",
                    description=f"**Tiền cược:** {bet_amount:,} xu\n\nChọn lựa chọn của bạn:",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                embed.set_author(
                    name=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                embed.set_footer(text="Nhấn button để chọn!")
                
                # Tạo view với buttons
                view = RPSButtonView(self, ctx.author.id, bet_amount)
                await ctx.reply(embed=embed, view=view, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong RPS command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi chơi kéo búa bao!",
                    mention_author=True
                )
        
        @self.bot.command(name='rpsstats', aliases=['kbbstats'])
        async def rps_stats(ctx, user: discord.Member = None):
            """Xem thống kê RPS"""
            try:
                target_user = user or ctx.author
                user_data = self.get_user_data(target_user.id)
                
                total_games = user_data['total_games']
                if total_games == 0:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ {target_user.display_name} chưa chơi kéo búa bao lần nào!",
                        mention_author=True
                    )
                    return
                
                # Xóa hiển thị tỷ lệ thắng
                
                embed = discord.Embed(
                    title="✂️ Thống Kê Kéo Búa Bao",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                
                # Lấy số tiền THỰC TẾ từ shared wallet
                actual_balance = shared_wallet.get_balance(target_user.id)
                embed.add_field(
                    name="💰 Tài chính",
                    value=(
                        f"**Số dư:** {actual_balance:,} xu\n"
                        f"**Tổng thắng:** {user_data.get('total_won', 0):,} xu\n"
                        f"**Tổng thua:** {user_data.get('total_lost', 0):,} xu"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Thành tích",
                    value=(
                        f"**Tổng ván:** {total_games:,}\n"
                        f"**Thắng:** {user_data['wins']:,}\n"
                        f"**Thua:** {user_data['losses']:,}\n"
                        f"**Hòa:** {user_data['draws']:,}"
                    ),
                    inline=True
                )
                
                embed.set_author(
                    name=target_user.display_name,
                    icon_url=target_user.avatar.url if target_user.avatar else None
                )
                embed.set_footer(text="Chơi với ;rps <kéo/búa/bao> <số tiền>")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong RPS stats command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem thống kê!",
                    mention_author=True
                )
        
        @self.bot.command(name='rpsleaderboard', aliases=['kbbleaderboard'])
        async def rps_leaderboard(ctx):
            """Bảng xếp hạng RPS"""
            try:
                if not self.rps_data:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ Chưa có dữ liệu người chơi!",
                        mention_author=True
                    )
                    return
                
                # Sort by balance
                sorted_users = sorted(
                    self.rps_data.items(),
                    key=lambda x: x[1]['balance'],
                    reverse=True
                )[:10]
                
                embed = discord.Embed(
                    title="🏆 Bảng Xếp Hạng Kéo Búa Bao",
                    description="Top 10 người chơi giàu nhất",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
                
                leaderboard_text = ""
                for i, (user_id, data) in enumerate(sorted_users):
                    try:
                        user = self.bot.get_user(int(user_id))
                        username = user.display_name if user else f"User {user_id}"
                        
                        win_rate = 0
                        if data['total_games'] > 0:
                            win_rate = (data['wins'] / data['total_games']) * 100
                        
                        # Lấy số tiền THỰC TẾ từ shared wallet
                        actual_balance = shared_wallet.get_balance(int(user_id))
                        leaderboard_text += (
                            f"{medals[i]} **{username}**\n"
                            f"💰 {actual_balance:,} xu | "
                            f"🎯 {data['total_games']} ván | "
                            f"📊 {win_rate:.1f}%\n\n"
                        )
                    except:
                        continue
                
                embed.description = leaderboard_text or "Không có dữ liệu"
                embed.set_footer(text="Chơi ;rps để tham gia bảng xếp hạng!")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong RPS leaderboard command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem bảng xếp hạng!",
                    mention_author=True
                )

class RPSButtonView(discord.ui.View):
    """View chứa buttons cho RPS game"""
    
    def __init__(self, rps_commands_instance, user_id, bet_amount):
        super().__init__(timeout=60)
        self.rps_commands = rps_commands_instance
        self.user_id = user_id
        self.bet_amount = bet_amount
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Chỉ cho phép người đặt cược tương tác"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải lượt chơi của bạn!",
                ephemeral=True
            )
            return False
        return True
    
    async def play_game(self, interaction: discord.Interaction, player_choice: str):
        """Xử lý logic chơi game"""
        try:
            # Bắt đầu game cho user (thêm vào active games)
            if not self.rps_commands.start_game_for_user(self.user_id):
                await interaction.response.send_message(
                    "❌ Bạn đang có game khác chưa hoàn thành!",
                    ephemeral=True
                )
                return
            
            # Disable tất cả buttons
            for item in self.children:
                item.disabled = True
            
            try:
                # Thêm delay 1 giây trước khi xử lý
                await asyncio.sleep(1)
                
                # Kiểm tra unluck system trước tiên
                is_unlucky = False
                if hasattr(self.rps_commands.bot_instance, 'unluck_commands'):
                    is_unlucky = self.rps_commands.bot_instance.unluck_commands.is_user_unlucky(self.user_id)
                    if is_unlucky:
                        # Tăng số game bị ảnh hưởng
                        self.rps_commands.bot_instance.unluck_commands.increment_game_affected(self.user_id)
                        logger.info(f"User {self.user_id} is unlucky - forcing RPS loss")
                
                # Lấy số dư hiện tại để xác định tỉ lệ thắng
                current_balance = shared_wallet.get_balance(self.user_id)
                
                # Bot makes choice
                if is_unlucky:
                    # Unlucky user luôn thua - chọn bot_choice để thắng player
                    if player_choice == "kéo":
                        bot_choice = "búa"  # Búa thắng kéo
                    elif player_choice == "búa":
                        bot_choice = "bao"  # Bao thắng búa
                    else:  # bao
                        bot_choice = "kéo"  # Kéo thắng bao
                    logger.info(f"Unlucky user {self.user_id} - bot chose {bot_choice} to beat {player_choice}")
                else:
                    # Dynamic win rate: Base 40%, +20% mỗi lần thua liên tiếp
                    user_data = self.rps_commands.get_user_data(self.user_id)
                    base_rate = 0.4  # 40% base
                    lose_streak = user_data.get('lose_streak', 0)
                    win_rate = min(base_rate + (lose_streak * 0.2), 0.9)  # Max 90%
                    logger.info(f"User {self.user_id} - Dynamic rate {win_rate*100:.0f}% (streak: {lose_streak})")
                    
                    should_win = random.random() < win_rate
                    if should_win:
                        # Chọn bot_choice để người chơi thắng
                        if player_choice == "kéo":
                            bot_choice = "bao"  # Kéo thắng bao
                        elif player_choice == "búa":
                            bot_choice = "kéo"  # Búa thắng kéo  
                        else:  # bao
                            bot_choice = "búa"  # Bao thắng búa
                    else:
                        # Chọn bot_choice để người chơi thua
                        if player_choice == "kéo":
                            bot_choice = "búa"  # Búa thắng kéo
                        elif player_choice == "búa":
                            bot_choice = "bao"  # Bao thắng búa
                        else:  # bao
                            bot_choice = "kéo"  # Kéo thắng bao
                
                result = self.rps_commands.get_winner(player_choice, bot_choice)
                
                # Create result embed
                if result == "win":
                    color = discord.Color.green()
                    result_text = "🎉 **BẠN THẮNG!**"
                    money_change = f"+{self.bet_amount:,}"
                elif result == "lose":
                    color = discord.Color.red()
                    result_text = "😢 **BẠN THUA!**"
                    money_change = f"-{self.bet_amount:,}"
                else:
                    color = discord.Color.yellow()
                    result_text = "🤝 **HÒA!**"
                    money_change = "±0"
                
                # Trừ tiền cược trước
                shared_wallet.subtract_balance(self.user_id, self.bet_amount)
                
                # Update shared wallet dựa trên kết quả
                if result == "win":
                    # Thắng: Hoàn lại tiền cược + tiền thắng (tổng = cược x2)
                    new_balance = shared_wallet.add_balance(self.user_id, self.bet_amount * 2)
                elif result == "lose":
                    # Thua: Đã trừ tiền rồi, chỉ lấy số dư mới
                    new_balance = shared_wallet.get_balance(self.user_id)
                else:  # draw
                    # Hòa: Hoàn lại tiền cược
                    new_balance = shared_wallet.add_balance(self.user_id, self.bet_amount)
                
                self.rps_commands.update_user_stats(self.user_id, result, self.bet_amount)
                
                embed = discord.Embed(
                    title="✂️ Kéo Búa Bao",
                    description=result_text,
                    color=color,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🎯 Lựa chọn",
                    value=(
                        f"**Bạn**: {self.rps_commands.get_emoji(player_choice)} {player_choice.title()}\n"
                        f"**Bot**: {self.rps_commands.get_emoji(bot_choice)} {bot_choice.title()}"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Tiền cược",
                    value=f"**{self.bet_amount:,} xu**",
                    inline=True
                )
                
                embed.add_field(
                    name="💳 Thay đổi",
                    value=f"**{money_change} xu**",
                    inline=True
                )
                
                embed.add_field(
                    name="💵 Số dư mới",
                    value=f"**{new_balance:,} xu**",
                    inline=False
                )
                
                embed.set_author(
                    name=f"{interaction.user.display_name}",
                    icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                )
                embed.set_footer(text="Chơi tiếp với ;rps <số tiền>")
                
                await interaction.response.edit_message(embed=embed, view=self)
                
            finally:
                # Luôn kết thúc game cho user (xóa khỏi active games)
                self.rps_commands.end_game_for_user(self.user_id)
                
        except Exception as e:
            # Đảm bảo user được xóa khỏi active games nếu có lỗi
            self.rps_commands.end_game_for_user(self.user_id)
            logger.error(f"Lỗi trong RPS button: {e}")
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi xử lý kéo búa bao!",
                ephemeral=True
            )
    
    @discord.ui.button(label='Kéo', emoji='✂️', style=discord.ButtonStyle.primary)
    async def scissors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_game(interaction, "kéo")
    
    @discord.ui.button(label='Búa', emoji='🔨', style=discord.ButtonStyle.primary)
    async def rock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_game(interaction, "búa")
    
    @discord.ui.button(label='Bao', emoji='📄', style=discord.ButtonStyle.primary)
    async def paper_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_game(interaction, "bao")
