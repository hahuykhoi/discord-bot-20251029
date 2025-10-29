import discord
import random
import json
import os
from datetime import datetime
from .base import BaseCommand
import logging
from utils.shared_wallet import shared_wallet

logger = logging.getLogger(__name__)

class FlipCommands(BaseCommand):
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.data_file = 'flip_data.json'
        self.flip_data = self.load_flip_data()
        
        # Tracking game đang chạy
        self.active_games = set()  # Set chứa user_id của những user đang có game chạy
        
        self.register_commands()
    
    def load_flip_data(self):
        """Load flip game data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Lỗi khi load flip data: {e}")
            return {}
    
    def save_flip_data(self):
        """Save flip game data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.flip_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Lỗi khi save flip data: {e}")
    
    def is_user_playing(self, user_id: int) -> bool:
        """Kiểm tra xem user có đang chơi game không"""
        return user_id in self.active_games
    
    def start_game_for_user(self, user_id: int) -> bool:
        """Bắt đầu game cho user (thêm vào active games)"""
        if user_id in self.active_games:
            return False
        self.active_games.add(user_id)
        logger.info(f"Started flip game for user {user_id}. Active games: {len(self.active_games)}")
        return True
    
    def end_game_for_user(self, user_id: int) -> None:
        """Kết thúc game cho user (xóa khỏi active games)"""
        if user_id in self.active_games:
            self.active_games.remove(user_id)
            logger.info(f"Ended flip game for user {user_id}. Active games: {len(self.active_games)}")
    
    def get_user_balance(self, user_id):
        """Get user's coin balance từ shared wallet"""
        user_id_str = str(user_id)
        if user_id_str not in self.flip_data:
            self.flip_data[user_id_str] = {
                'balance': 1000,  # Starting balance (chỉ để stats)
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'total_won': 0,
                'total_lost': 0
            }
            self.save_flip_data()
        # Trả về số tiền THỰC TẾ từ shared wallet
        return shared_wallet.get_balance(user_id)
    
    def update_user_stats(self, user_id, bet_amount, won):
        """Update user statistics (không động đến balance vì dùng shared wallet)"""
        user_id_str = str(user_id)
        if user_id_str not in self.flip_data:
            self.get_user_balance(user_id)  # Initialize user
        
        user_data = self.flip_data[user_id_str]
        user_data['total_games'] += 1
        
        if won:
            user_data['wins'] += 1
            user_data['total_won'] += bet_amount
        else:
            user_data['losses'] += 1
            user_data['total_lost'] += bet_amount
        
        # Đồng bộ balance từ shared wallet
        user_data['balance'] = shared_wallet.get_balance(user_id)
        
        self.save_flip_data()
    
    def register_commands(self):
        """Register flip game commands"""
        
        @self.bot.command(name='flipcoin', aliases=['flip', 'coin'])
        async def flip_coin(ctx, amount=None):
            """
            Flip coin game - Đặt cược úp hoặc ngửa
            Usage: ;flipcoin <số tiền>
            """
            try:
                # Validate amount
                if not amount:
                    embed = discord.Embed(
                        title="🪙 Flip Coin - Hướng dẫn",
                        description="Đặt cược vào kết quả tung đồng xu!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(
                        name="📋 Cách chơi",
                        value=(
                            "; <số tiền>`\n"
                            "; 100` - Đặt cược 100 xu\n"
                            "; 500` - Đặt cược 500 xu\n\n"
                            "**Sau đó chọn bằng buttons:** 👤 Heads | 🔰 Tails"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="💰 Thông tin",
                        value=(
                            "• **Tỷ lệ thắng:** 50/50\n"
                            "• **Thắng:** Nhận lại gấp đôi số tiền đặt\n"
                            "• **Thua:** Mất số tiền đã đặt\n"
                            "• **Số dư ban đầu:** 1,000 xu"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="📊 Commands khác",
                        value=(
                            ";` - Xem thống kê cá nhân\n"
                            ";` - Xem số dư hiện tại\n"
                            ";` - Bảng xếp hạng"
                        ),
                        inline=False
                    )
                    embed.set_footer(text="Chơi có trách nhiệm!")
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
                
                # Parse bet amount với hỗ trợ "all" và auto-adjust
                bet_amount, is_adjusted, parse_message = shared_wallet.parse_bet_amount(ctx.author.id, amount)
                
                # Kiểm tra lỗi parse
                if bet_amount <= 0:
                    await ctx.reply(
                        f"{ctx.author.mention} {parse_message if parse_message else '❌ Số tiền không hợp lệ!'}",
                        mention_author=True
                    )
                    return
                
                # Hiển thị thông báo nếu đã điều chỉnh
                if is_adjusted and parse_message:
                    await ctx.send(f"{ctx.author.mention} {parse_message}")
                
                # Tạo embed hỏi lựa chọn
                embed = discord.Embed(
                    title="🪙 Flip Coin - Tung Đồng Xu",
                    description=f"**Tiền cược:** {bet_amount:,} xu\n\nChọn mặt đồng xu:",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                embed.set_author(
                    name=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                embed.set_footer(text="Nhấn button để chọn!")
                
                # Tạo view với buttons
                view = FlipCoinButtonView(self, ctx.author.id, bet_amount)
                await ctx.reply(embed=embed, view=view, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong flip command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi chơi flip coin!",
                    mention_author=True
                )
        
        @self.bot.command(name='flipstats', aliases=['fs'])
        async def flip_stats(ctx, user: discord.Member = None):
            """Xem thống kê flip coin của bản thân hoặc người khác"""
            try:
                target_user = user or ctx.author
                user_id_str = str(target_user.id)
                
                if user_id_str not in self.flip_data:
                    if target_user == ctx.author:
                        await ctx.reply(
                            f"{ctx.author.mention} ❌ Bạn chưa chơi flip coin lần nào!",
                            mention_author=True
                        )
                    else:
                        await ctx.reply(
                            f"{ctx.author.mention} ❌ {target_user.display_name} chưa chơi flip coin lần nào!",
                            mention_author=True
                        )
                    return
                
                user_data = self.flip_data[user_id_str]
                win_rate = (user_data['wins'] / user_data['total_games'] * 100) if user_data['total_games'] > 0 else 0
                
                embed = discord.Embed(
                    title=f"📊 Thống kê Flip Coin - {target_user.display_name}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                # Lấy số tiền THỰC TẾ từ shared wallet
                actual_balance = shared_wallet.get_balance(target_user.id)
                embed.add_field(
                    name="💰 Tài chính",
                    value=(
                        f"**Số dư hiện tại:** {actual_balance:,} xu\n"
                        f"**Tổng thắng:** {user_data['total_won']:,} xu\n"
                        f"**Tổng thua:** {user_data['total_lost']:,} xu\n"
                        f"**Lãi/Lỗ:** {user_data['total_won'] - user_data['total_lost']:+,} xu"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 Thống kê game",
                    value=(
                        f"**Tổng ván:** {user_data['total_games']:,}\n"
                        f"**Thắng:** {user_data['wins']:,}\n"
                        f"**Thua:** {user_data['losses']:,}\n"
                        f"**Tỷ lệ thắng:** {win_rate:.1f}%"
                    ),
                    inline=False
                )
                
                embed.set_author(
                    name=target_user.display_name,
                    icon_url=target_user.avatar.url if target_user.avatar else None
                )
                embed.set_footer(text="Chơi với ;xu <úp/ngửa> <số tiền>")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong flipstats command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem thống kê!",
                    mention_author=True
                )
        
        @self.bot.command(name='flipbalance', aliases=['fb'])
        async def flip_balance(ctx):
            """Xem số dư flip coin hiện tại"""
            try:
                balance = self.get_user_balance(ctx.author.id)
                await ctx.reply(
                    f"{ctx.author.mention} 💰 Số dư hiện tại: **{balance:,} xu**",
                    mention_author=True
                )
            except Exception as e:
                logger.error(f"Lỗi trong flipbalance command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem số dư!",
                    mention_author=True
                )
        
        @self.bot.command(name='flipleaderboard', aliases=['flb'])
        async def flip_leaderboard(ctx):
            """Xem bảng xếp hạng flip coin"""
            try:
                if not self.flip_data:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Chưa có ai chơi flip coin!",
                        mention_author=True
                    )
                    return
                
                # Sort by balance
                sorted_users = sorted(
                    self.flip_data.items(),
                    key=lambda x: x[1]['balance'],
                    reverse=True
                )[:10]  # Top 10
                
                embed = discord.Embed(
                    title="🏆 Bảng xếp hạng Flip Coin",
                    description="Top 10 người chơi giàu nhất",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                leaderboard_text = ""
                for i, (user_id, data) in enumerate(sorted_users, 1):
                    try:
                        user = self.bot.get_user(int(user_id))
                        username = user.display_name if user else f"User {user_id}"
                        
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        win_rate = (data['wins'] / data['total_games'] * 100) if data['total_games'] > 0 else 0
                        
                        # Lấy số tiền THỰC TẾ từ shared wallet
                        actual_balance = shared_wallet.get_balance(int(user_id))
                        leaderboard_text += (
                            f"{medal} **{username}**\n"
                            f"💰 {actual_balance:,} xu | "
                            f"🎮 {data['total_games']} ván | "
                            f"📈 {win_rate:.1f}%\n\n"
                        )
                    except:
                        continue
                
                embed.description = leaderboard_text or "Không có dữ liệu"
                embed.set_footer(text="Chơi với ;flip để lên bảng xếp hạng!")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong flipleaderboard command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem bảng xếp hạng!",
                    mention_author=True
                )

        logger.info("Đã đăng ký Flip commands: flipcoin, flipstats, flipbalance, flipleaderboard")

class FlipCoinButtonView(discord.ui.View):
    """View chứa buttons cho Flip Coin game"""
    
    def __init__(self, flip_commands_instance, user_id, bet_amount):
        super().__init__(timeout=60)
        self.flip_commands = flip_commands_instance
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
    
    async def play_game(self, interaction: discord.Interaction, user_choice: str):
        """Xử lý logic chơi game"""
        try:
            # Bắt đầu game cho user (thêm vào active games)
            if not self.flip_commands.start_game_for_user(self.user_id):
                await interaction.response.send_message(
                    "❌ Bạn đang có game khác chưa hoàn thành!",
                    ephemeral=True
                )
                return
            
            # Disable tất cả buttons
            for item in self.children:
                item.disabled = True
            
            try:
                # Flip the coin với 70% tỷ lệ thắng
                should_win = random.random() < 0.7
                if should_win:
                    coin_result = user_choice  # Người chơi thắng
                else:
                    coin_result = 'tails' if user_choice == 'heads' else 'heads'  # Người chơi thua
                won = (user_choice == coin_result)
                
                # Create result embed
                embed = discord.Embed(
                    title="🪙 Kết quả Flip Coin",
                    color=discord.Color.green() if won else discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                # Coin animation
                user_emoji = "👤" if user_choice == 'heads' else "🔰"
                result_emoji = "👤" if coin_result == 'heads' else "🔰"
                user_text = "Heads (Ngửa)" if user_choice == 'heads' else "Tails (Sấp)"
                result_text = "Heads (Ngửa)" if coin_result == 'heads' else "Tails (Sấp)"
                
                embed.add_field(
                    name="🎯 Lựa chọn của bạn",
                    value=f"{user_emoji} **{user_text}**",
                    inline=True
                )
                embed.add_field(
                    name="🪙 Kết quả",
                    value=f"{result_emoji} **{result_text}**",
                    inline=True
                )
                embed.add_field(
                    name="💰 Số tiền đặt",
                    value=f"**{self.bet_amount:,} xu**",
                    inline=True
                )
                
                # Trừ tiền cược trước
                shared_wallet.subtract_balance(self.user_id, self.bet_amount)
                
                # Update balance dựa trên kết quả
                if won:
                    # Thắng: Hoàn lại tiền cược + tiền thắng (tổng = cược x2)
                    new_balance = shared_wallet.add_balance(self.user_id, self.bet_amount * 2)
                else:
                    # Thua: Đã trừ tiền rồi, chỉ lấy số dư mới
                    new_balance = shared_wallet.get_balance(self.user_id)
                
                # Update stats
                self.flip_commands.update_user_stats(self.user_id, self.bet_amount, won)
                
                if won:
                    embed.add_field(
                        name="🎉 Kết quả",
                        value=f"**THẮNG!** +{self.bet_amount:,} xu",
                        inline=False
                    )
                    embed.add_field(
                        name="💳 Số dư mới",
                        value=f"**{new_balance:,} xu** (+{self.bet_amount:,})",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="😢 Kết quả",
                        value=f"**THUA!** -{self.bet_amount:,} xu",
                        inline=False
                    )
                    embed.add_field(
                        name="💳 Số dư mới",
                        value=f"**{new_balance:,} xu** (-{self.bet_amount:,})",
                        inline=False
                    )
                
                embed.set_author(
                    name=f"{interaction.user.display_name}",
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
    
    @discord.ui.button(label='Heads (Ngửa)', emoji='👤', style=discord.ButtonStyle.primary)
    async def heads_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_game(interaction, 'heads')
    
    @discord.ui.button(label='Tails (Sấp)', emoji='🔰', style=discord.ButtonStyle.primary)
    async def tails_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_game(interaction, 'tails')
