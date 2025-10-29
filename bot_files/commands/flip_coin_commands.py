"""
Flip Coin Commands - Game tung đồng xu cho Discord bot
Lệnh: ;flipcoin heads/tails <số tiền>
"""
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

class FlipCoinCommands(BaseCommand):
    """Class chứa lệnh Flip Coin game"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.data_file = "flip_coin_data.json"
        self.flip_data = self.load_flip_data()
        
        # Tracking game đang chạy
        self.active_games = set()  # Set chứa user_id của những user đang có game chạy
    
    def load_flip_data(self):
        """Load dữ liệu flip coin từ file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load flip coin data: {e}")
            return {}
    
    def save_flip_data(self):
        """Lưu dữ liệu flip coin vào file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.flip_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save flip coin data: {e}")
    
    def is_user_playing(self, user_id: int) -> bool:
        """Kiểm tra xem user có đang chơi game không"""
        return user_id in self.active_games
    
    def start_game_for_user(self, user_id: int) -> bool:
        """Bắt đầu game cho user (thêm vào active games)"""
        if user_id in self.active_games:
            return False
        self.active_games.add(user_id)
        logger.info(f"Started flip coin game for user {user_id}. Active games: {len(self.active_games)}")
        return True
    
    def end_game_for_user(self, user_id: int) -> None:
        """Kết thúc game cho user (xóa khỏi active games)"""
        if user_id in self.active_games:
            self.active_games.remove(user_id)
            logger.info(f"Ended flip coin game for user {user_id}. Active games: {len(self.active_games)}")
    
    def get_user_data(self, user_id):
        """Lấy dữ liệu user, tạo mới nếu chưa có"""
        user_id = str(user_id)
        if user_id not in self.flip_data:
            self.flip_data[user_id] = {
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'total_bet': 0,
                'total_won': 0,
                'biggest_win': 0,
                'games_10m_plus': 0,  # Số game với cược >= 10M
                'created_at': datetime.now().isoformat()
            }
            self.save_flip_data()
        return self.flip_data[user_id]
    
    def flip_coin(self, user_id=None, player_choice=None, force_win=False, force_lose=False):
        """Tung đồng xu - trả về 'heads' hoặc 'tails'"""
        # Kiểm tra unluck system
        if user_id and hasattr(self.bot_instance, 'unluck_commands'):
            is_unlucky = self.bot_instance.unluck_commands.is_user_unlucky(user_id)
            if is_unlucky:
                # Tăng số game bị ảnh hưởng
                self.bot_instance.unluck_commands.increment_game_affected(user_id)
                force_lose = True
        # Logic game: Dynamic win rate system
        if user_id and not force_lose and not force_win:
            is_admin = self.bot_instance.is_admin(user_id) or self.bot_instance.is_supreme_admin(user_id)
            
            # Lấy user data để check streak
            user_data = self.get_user_data(user_id)
            
            # Dynamic win rate: Base 40%, +20% mỗi lần thua liên tiếp
            base_rate = 0.4  # 40% base
            lose_streak = user_data.get('lose_streak', 0)
            dynamic_rate = min(base_rate + (lose_streak * 0.2), 0.9)  # Max 90%
            
            should_win = random.random() < dynamic_rate
            logger.info(f"User {user_id} - Dynamic rate {dynamic_rate*100:.0f}% (streak: {lose_streak}) - {'WIN' if should_win else 'LOSE'}")
            if should_win:
                force_win = True
            else:
                force_lose = True
        
        if force_lose and player_choice:
            # Force lose: trả về kết quả ngược với lựa chọn của player
            return 'tails' if player_choice == 'heads' else 'heads'
        elif force_win and player_choice:
            # Force win: trả về kết quả giống với lựa chọn của player
            return player_choice
        else:
            # Normal flip
            return random.choice(['heads', 'tails'])
    
    def update_user_stats(self, user_id, bet_amount, won):
        """Cập nhật thống kê user"""
        user_data = self.get_user_data(user_id)
        user_data['total_games'] += 1
        user_data['total_bet'] += bet_amount
        
        # Tracking game với cược >= 10M
        if bet_amount >= 10_000_000:
            if 'games_10m_plus' not in user_data:
                user_data['games_10m_plus'] = 0
            user_data['games_10m_plus'] += 1
        
        if won:
            user_data['wins'] += 1
            winnings = bet_amount * 2
            user_data['total_won'] += winnings
            if winnings > user_data['biggest_win']:
                user_data['biggest_win'] = winnings
            
            # Reset lose streak khi thắng
            user_data['lose_streak'] = 0
            logger.info(f"User {user_id} won flip - reset lose streak to 0")
            
            # Weekly leaderboard đã bị xóa
        else:
            user_data['losses'] += 1
            
            # Tăng lose streak khi thua
            current_streak = user_data.get('lose_streak', 0)
            user_data['lose_streak'] = current_streak + 1
            logger.info(f"User {user_id} lost flip - lose streak: {user_data['lose_streak']}")
        
        self.save_flip_data()
    
    def register_commands(self):
        """Register flip coin commands"""
        
        @self.bot.command(name='flipcoin', aliases=['flip', 'coin'])
        async def flip_coin_game(ctx, amount=None):
            """
            Flip Coin game - Tung đồng xu với buttons
            
            Usage: ;flipcoin <số tiền>
            Example: ;flipcoin 100
            """
            try:
                # Validate amount first
                if not amount:
                    embed = discord.Embed(
                        title="🪙 Flip Coin - Hướng dẫn",
                        description="Chọn mặt đồng xu và đặt cược!",
                        color=discord.Color.blue()
                    )
                    
                    embed.add_field(
                        name="📋 Cách chơi:",
                        value=(
                            "; <số tiền>`\n\n"
                            "**Bước 1:** Nhập lệnh với số tiền cược\n"
                            "**Bước 2:** Chọn mặt đồng xu bằng buttons\n"
                            "• 👤 **Heads** (Mặt ngửa)\n"
                            "• 🔰 **Tails** (Mặt sấp)\n\n"
                            "**Ví dụ:**\n"
                            "; 100` - Đặt cược 100 xu\n"
                            "; 500` - Đặt cược 500 xu"
                        ),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="💰 Phần thượng:",
                        value="**Thắng:** x2 tiền cược\n**Thua:** Mất tiền cược",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📊 Commands khác:",
                        value=(
                            ";` - Xem thống kê\n"
                            ";` - Xem số dư"
                        ),
                        inline=False
                    )
                    
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra xem user có đang chơi game không
                if self.is_user_playing(ctx.author.id):
                    embed = discord.Embed(
                        title="⏳ Game đang chạy",
                        description="Bạn đang có một ván flip coin chưa hoàn thành!\nVui lòng chờ ván hiện tại kết thúc trước khi bắt đầu ván mới.",
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
                    if bet_amount < 10:
                        await ctx.reply(
                            f"{ctx.author.mention} ❌ Số tiền cược tối thiểu là **10 xu**!",
                            mention_author=True
                        )
                        return
                    if bet_amount > 250000:
                        await ctx.reply(
                            f"{ctx.author.mention} ❌ Số tiền cược tối đa là **250,000 xu**!",
                            mention_author=True
                        )
                        return
                except ValueError:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Số tiền không hợp lệ!",
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
                
                # Show choice buttons
                embed = discord.Embed(
                    title="🪙 Flip Coin - Chọn mặt đồng xu",
                    description=f"Bạn đã đặt cược **{bet_amount:,} xu**\n\nChọn mặt đồng xu:",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 Heads",
                    value="Mặt ngửa",
                    inline=True
                )
                
                embed.add_field(
                    name="🔰 Tails",
                    value="Mặt sấp",
                    inline=True
                )
                
                embed.set_author(
                    name=ctx.author.display_name,
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                
                embed.set_footer(text="Nhấn button để chọn!")
                
                # Create view with buttons
                view = FlipCoinView(self, ctx.author.id, bet_amount)
                
                await ctx.reply(embed=embed, view=view, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong flip coin command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi chơi flip coin!",
                    mention_author=True
                )
        
        @self.bot.command(name='flipstats', aliases=['flipcoinstats'])
        async def flip_coin_stats(ctx, user: discord.Member = None):
            """Xem thống kê flip coin"""
            try:
                target_user = user or ctx.author
                user_data = self.get_user_data(target_user.id)
                
                total_games = user_data['total_games']
                if total_games == 0:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ {'Người này' if user else 'Bạn'} chưa chơi flip coin lần nào!",
                        mention_author=True
                    )
                    return
                
                wins = user_data['wins']
                losses = user_data['losses']
                win_rate = (wins / total_games * 100) if total_games > 0 else 0
                total_profit = user_data['total_won'] - user_data['total_bet']
                
                embed = discord.Embed(
                    title="🪙 Thống Kê Flip Coin",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                embed.set_author(
                    name=target_user.display_name,
                    icon_url=target_user.avatar.url if target_user.avatar else None
                )
                
                embed.add_field(
                    name="🎮 Trò chơi",
                    value=(
                        f"**Tổng số ván:** {total_games:,}\n"
                        f"**Thắng:** {wins:,} ({win_rate:.1f}%)\n"
                        f"**Thua:** {losses:,}"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Tài chính",
                    value=(
                        f"**Tổng cược:** {user_data['total_bet']:,} xu\n"
                        f"**Tổng thắng:** {user_data['total_won']:,} xu\n"
                        f"**Lợi nhuận:** {total_profit:+,} xu"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Thành tích",
                    value=f"**Thắng lớn nhất:** {user_data['biggest_win']:,} xu",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong flip stats command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem thống kê!",
                    mention_author=True
                )
        
        @self.bot.command(name='flipleaderboard', aliases=['fliptop'])
        async def flip_leaderboard(ctx):
            """Bảng xếp hạng flip coin"""
            try:
                if not self.flip_data:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ Chưa có dữ liệu người chơi!",
                        mention_author=True
                    )
                    return
                
                # Sort by profit
                sorted_users = []
                for user_id, data in self.flip_data.items():
                    if data['total_games'] > 0:
                        profit = data['total_won'] - data['total_bet']
                        sorted_users.append({
                            'user_id': int(user_id),
                            'profit': profit,
                            'wins': data['wins'],
                            'total_games': data['total_games'],
                            'biggest_win': data['biggest_win']
                        })
                
                sorted_users.sort(key=lambda x: x['profit'], reverse=True)
                top_10 = sorted_users[:10]
                
                embed = discord.Embed(
                    title="🏆 Bảng Xếp Hạng Flip Coin",
                    description="Top 10 người chơi có lợi nhuận cao nhất",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
                
                leaderboard_text = ""
                for i, user_info in enumerate(top_10):
                    try:
                        user = await self.bot.fetch_user(user_info['user_id'])
                        username = user.display_name if user else f"User {user_info['user_id']}"
                        
                        leaderboard_text += (
                            f"{medals[i]} **{username}**\n"
                            f"💰 Lợi nhuận: {user_info['profit']:+,} xu | "
                            f"🏆 Thắng: {user_info['wins']}/{user_info['total_games']} | "
                            f"🎁 Lớn nhất: {user_info['biggest_win']:,} xu\n\n"
                        )
                    except:
                        continue
                
                if leaderboard_text:
                    embed.description = leaderboard_text
                else:
                    embed.description = "Chưa có dữ liệu xếp hạng!"
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong flip leaderboard command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem bảng xếp hạng!",
                    mention_author=True
                )

class FlipCoinView(discord.ui.View):
    """View chứa buttons cho Flip Coin game"""
    
    def __init__(self, flip_commands, user_id, bet_amount):
        super().__init__(timeout=60)  # 60 giây timeout
        self.flip_commands = flip_commands
        self.user_id = user_id
        self.bet_amount = bet_amount
    
    @discord.ui.button(label='👤 Heads', style=discord.ButtonStyle.primary, custom_id='heads')
    async def heads_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button chọn Heads"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải game của bạn!",
                ephemeral=True
            )
            return
        
        await self.process_flip(interaction, 'heads')
    
    @discord.ui.button(label='🔰 Tails', style=discord.ButtonStyle.danger, custom_id='tails')
    async def tails_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button chọn Tails"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải game của bạn!",
                ephemeral=True
            )
            return
        
        await self.process_flip(interaction, 'tails')
    
    async def process_flip(self, interaction: discord.Interaction, choice: str):
        """Xử lý flip coin"""
        try:
            import asyncio
            
            # Bắt đầu game cho user (thêm vào active games)
            if not self.flip_commands.start_game_for_user(self.user_id):
                await interaction.response.send_message(
                    "❌ Bạn đang có game khác chưa hoàn thành!",
                    ephemeral=True
                )
                return
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            # Defer response
            await interaction.response.defer()
            
            try:
                # Animation tung đồng xu
                loading_embed = discord.Embed(
                    title="🪙 Flip Coin",
                    description="⚡ **Đang tung...** ⚡",
                    color=discord.Color.blue()
                )
                loading_msg = await interaction.followup.send(embed=loading_embed)
                
                # Animation: Đồng xu "quay" 8 lần
                coin_sides = ['👤', '🔰']
                for i in range(8):
                    random_side = random.choice(coin_sides)
                    side_name = "Heads" if random_side == '👤' else "Tails"
                    
                    anim_embed = discord.Embed(
                        title="🪙 Flip Coin - Đang quay...",
                        description=f"🪙 **{random_side} {side_name}**",
                        color=discord.Color.gold()
                    )
                    await loading_msg.edit(embed=anim_embed)
                    await asyncio.sleep(0.25)
                
                # Kiểm tra streak thua liên tiếp và auto win
                user_data = self.flip_commands.get_user_data(self.user_id)
                lose_streak = user_data.get('lose_streak', 0)
                auto_wins_left = user_data.get('auto_wins_left', 0)
                
                should_auto_win = False
                # Nếu có auto wins còn lại, force win
                if auto_wins_left > 0:
                    should_auto_win = True
                    logger.info(f"User {self.user_id} has {auto_wins_left} auto wins left in Flip Coin")
                # Nếu thua 5 lần liên tiếp, kích hoạt auto win 2 trận
                elif lose_streak >= 5:
                    should_auto_win = True
                    # Set auto wins cho trận tiếp theo (trận này + 1 trận nữa = 2 trận)
                    user_data['auto_wins_left'] = 1
                    user_data['lose_streak'] = 0  # Reset streak
                    self.flip_commands.save_flip_data()
                    logger.info(f"User {self.user_id} triggered auto win in Flip Coin after {lose_streak} losses")
                
                # Flip the coin - kết quả cuối
                result = self.flip_commands.flip_coin(self.user_id, choice, should_auto_win)
                won = (result == choice)
                
                # Hiển thị kết quả cuối 1.5 giây
                result_coin = "👤" if result == "heads" else "🔰"
                result_name = "Heads" if result == "heads" else "Tails"
                final_flip_embed = discord.Embed(
                    title="🪙 Flip Coin - Đã rơi!",
                    description=f"🪙 **{result_coin} {result_name}**",
                    color=discord.Color.purple()
                )
                await loading_msg.edit(embed=final_flip_embed)
                await asyncio.sleep(1.5)
                
                # Xóa animation
                try:
                    await loading_msg.delete()
                except:
                    pass
                
                # Update shared wallet
                if won:
                    winnings = self.bet_amount * 2
                    new_balance = shared_wallet.add_balance(self.user_id, self.bet_amount)
                else:
                    new_balance = shared_wallet.subtract_balance(self.user_id, self.bet_amount)
                
                # Update stats
                self.flip_commands.update_user_stats(self.user_id, self.bet_amount, won)
                
                # Create result embed
                if won:
                    color = discord.Color.green()
                    result_text = f"🎉 **BẠN THẮNG {self.bet_amount * 2:,} xu!**"
                else:
                    color = discord.Color.red()
                    result_text = f"😢 **BẠN THUA {self.bet_amount:,} xu!**"
                
                embed = discord.Embed(
                    title="🪙 Flip Coin - Kết quả",
                    description=result_text,
                    color=color,
                    timestamp=datetime.now()
                )
                
                # Coin display
                coin_display = "👤" if result == "heads" else "🔰"
                choice_display = "👤 Heads (Ngửa)" if choice == "heads" else "🔰 Tails (Sấp)"
                result_display = "👤 Heads (Ngửa)" if result == "heads" else "🔰 Tails (Sấp)"
                
                embed.add_field(
                    name="🎯 Bạn chọn",
                    value=choice_display,
                    inline=True
                )
                
                embed.add_field(
                    name="🪙 Kết quả",
                    value=f"{coin_display} **{result_display}**",
                    inline=True
                )
                
                embed.add_field(
                    name="\u200b",
                    value="\u200b",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Tiền cược",
                    value=f"**{self.bet_amount:,} xu**",
                    inline=True
                )
                
                if won:
                    embed.add_field(
                        name="🎁 Tiền thắng",
                        value=f"**+{self.bet_amount:,} xu**",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="💸 Tiền thua",
                        value=f"**-{self.bet_amount:,} xu**",
                        inline=True
                    )
                
                embed.add_field(
                    name="\u200b",
                    value="\u200b",
                    inline=True
                )
                
                embed.add_field(
                    name="💳 Số dư mới",
                    value=f"**{new_balance:,} xu**",
                    inline=False
                )
                
                embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                )
                
                embed.set_footer(text="Chơi tiếp với ;flipcoin <số tiền>")
                
                await interaction.response.edit_message(embed=embed, view=self)
                
            finally:
                # Luôn kết thúc game cho user (xóa khỏi active games)
                self.flip_commands.end_game_for_user(self.user_id)
            
        except Exception as e:
            # Đảm bảo user được xóa khỏi active games nếu có lỗi
            self.flip_commands.end_game_for_user(self.user_id)
            logger.error(f"Lỗi trong flip coin button: {e}")
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi xử lý flip coin!",
                ephemeral=True
            )
    
    async def on_timeout(self):
        """Xử lý khi view timeout"""
        # Disable tất cả buttons
        for item in self.children:
            item.disabled = True
