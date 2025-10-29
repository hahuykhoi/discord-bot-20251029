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

class BlackjackCommands(BaseCommand):
    """Class chứa lệnh Blackjack"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.data_file = "blackjack_data.json"
        self.blackjack_data = self.load_blackjack_data()
        self.active_games = {}  # Store active games
        
        # Card deck
        self.suits = ["♠️", "♥️", "♦️", "♣️"]
        self.ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.card_values = {
            "A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
            "J": 10, "Q": 10, "K": 10
        }
    
    def load_blackjack_data(self):
        """Load dữ liệu blackjack từ file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load blackjack data: {e}")
            return {}
    
    def save_blackjack_data(self):
        """Lưu dữ liệu blackjack vào file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.blackjack_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save blackjack data: {e}")
    
    def get_user_data(self, user_id):
        """Lấy dữ liệu user, tạo mới nếu chưa có"""
        user_id = str(user_id)
        if user_id not in self.blackjack_data:
            self.blackjack_data[user_id] = {
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'blackjacks': 0,
                'total_bet': 0,
                'total_won': 0,
                'balance': 0,  # Thêm balance (sẽ sync từ shared wallet)
                'lose_streak': 0,  # Streak thua liên tiếp
                'auto_wins_left': 0,  # Số trận auto win còn lại
                'games_10m_plus': 0,  # Số game với cược >= 10M
                'created_at': datetime.now().isoformat()
            }
        return self.blackjack_data[user_id]
    
    def create_deck(self):
        """Tạo bộ bài mới"""
        deck = []
        for suit in self.suits:
            for rank in self.ranks:
                deck.append(f"{rank}{suit}")
        random.shuffle(deck)
        return deck
    
    def get_card_value(self, card):
        """Lấy giá trị của thẻ bài"""
        rank = card[:-2] if card[:-2] in self.card_values else card[:-1]
        return self.card_values[rank]
    
    def calculate_hand_value(self, hand):
        """Tính giá trị tay bài"""
        value = 0
        aces = 0
        
        for card in hand:
            card_value = self.get_card_value(card)
            if card_value == 11:  # Ace
                aces += 1
            value += card_value
        
        # Adjust for aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def format_hand(self, hand, hide_first=False):
        """Format tay bài để hiển thị"""
        if hide_first and len(hand) > 0:
            return "🂠 " + " ".join(hand[1:])
        return " ".join(hand)
    
    def is_blackjack(self, hand):
        """Kiểm tra blackjack (21 với 2 lá đầu)"""
        return len(hand) == 2 and self.calculate_hand_value(hand) == 21
    
    def update_user_stats(self, user_id, result, bet_amount, winnings=0):
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
            user_data['total_won'] += winnings
            # Reset lose streak khi thắng
            user_data['lose_streak'] = 0
            # Giảm auto wins left nếu có
            if user_data.get('auto_wins_left', 0) > 0:
                user_data['auto_wins_left'] -= 1
                logger.info(f"User {user_id} used auto win in Blackjack, {user_data['auto_wins_left']} left")
            
            # Weekly leaderboard đã bị xóa
        elif result == "lose":
            user_data['losses'] += 1
            # Tăng lose streak khi thua (chỉ khi không phải auto win)
            if user_data.get('auto_wins_left', 0) == 0:
                current_streak = user_data.get('lose_streak', 0)
                user_data['lose_streak'] = current_streak + 1
                logger.info(f"User {user_id} Blackjack lose streak: {user_data['lose_streak']}")
        elif result == "draw":
            user_data['draws'] += 1
            # Hòa không ảnh hưởng streak
        elif result == "blackjack":
            user_data['wins'] += 1
            user_data['blackjacks'] += 1
            user_data['total_won'] += winnings
            # Reset lose streak khi thắng
            user_data['lose_streak'] = 0
            # Giảm auto wins left nếu có
            if user_data.get('auto_wins_left', 0) > 0:
                user_data['auto_wins_left'] -= 1
                logger.info(f"User {user_id} used auto win in Blackjack (blackjack), {user_data['auto_wins_left']} left")
        
        self.save_blackjack_data()
    
    def register_commands(self):
        """Register blackjack commands"""
        
        @self.bot.command(name='blackjack', aliases=['bj', 'xidach'])
        async def blackjack_game(ctx, amount=None):
            """
            Blackjack game
            Usage: ;blackjack <số tiền>
            """
            try:
                # Check if user already has active game
                if ctx.author.id in self.active_games:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Bạn đang có ván blackjack chưa hoàn thành! Dùng ;`, ;` hoặc ;`",
                        mention_author=True
                    )
                    return
                
                # Validate arguments
                if not amount:
                    embed = discord.Embed(
                        title="🃏 Blackjack - Hướng dẫn",
                        description="Trò chơi xì dách chuẩn casino!",
                        color=discord.Color.dark_red(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="📋 Cách chơi",
                        value=(
                            "; <số tiền>` - Bắt đầu ván mới\n"
                            ";` - Rút thêm bài\n"
                            ";` - Dừng lại\n"
                            ";` - Thoát ván (mất tiền cược)"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="🎯 Luật chơi",
                        value=(
                            "• **Mục tiêu**: Đạt 21 điểm hoặc gần nhất mà không vượt quá\n"
                            "• **Blackjack**: 21 điểm với 2 lá đầu (A + 10/J/Q/K)\n"
                            "• **Bust**: Vượt quá 21 điểm = thua\n"
                            "• **Ace**: Có thể là 1 hoặc 11 điểm"
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="💰 Tỷ lệ thắng",
                        value=(
                            "• **Blackjack**: x2.5 (150% tiền cược)\n"
                            "• **Thắng thường**: x2 (100% tiền cược)\n"
                            "• **Hòa**: Hoàn lại tiền cược\n"
                            "• **Thua**: Mất tiền cược"
                        ),
                        inline=False
                    )
                    embed.set_footer(text="Chơi với ;blackjack <số tiền>")
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
                if bet_amount > 250_000:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Số tiền cược tối đa là 250,000 xu!",
                        mention_author=True
                    )
                    return
                
                # Start new game
                deck = self.create_deck()
                
                # Kiểm tra unluck system
                is_unlucky = False
                if hasattr(self.bot_instance, 'unluck_commands'):
                    is_unlucky = self.bot_instance.unluck_commands.is_user_unlucky(ctx.author.id)
                    if is_unlucky:
                        # Tăng số game bị ảnh hưởng
                        self.bot_instance.unluck_commands.increment_game_affected(ctx.author.id)
                        logger.info(f"User {ctx.author.id} is unlucky - rigging blackjack deck")
                
                if is_unlucky:
                    # Unlucky user: Tạo deck để dễ bị bust
                    # Đưa các lá bài cao (10, J, Q, K) lên đầu deck
                    high_cards = [card for card in deck if card[:-2] in ['10', 'J', 'Q', 'K'] or card[:-1] in ['10', 'J', 'Q', 'K']]
                    other_cards = [card for card in deck if card not in high_cards]
                    deck = high_cards + other_cards
                
                player_hand = [deck.pop(), deck.pop()]
                dealer_hand = [deck.pop(), deck.pop()]
                
                # Store game state
                self.active_games[ctx.author.id] = {
                    'deck': deck,
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'bet_amount': bet_amount,
                    'channel_id': ctx.channel.id
                }
                
                player_value = self.calculate_hand_value(player_hand)
                dealer_value = self.calculate_hand_value([dealer_hand[0]])  # Only show first card
                
                # Check for immediate blackjack
                if self.is_blackjack(player_hand):
                    if self.is_blackjack(dealer_hand):
                        # Both have blackjack - draw (no money change)
                        new_balance = shared_wallet.get_balance(ctx.author.id)
                        self.update_user_stats(ctx.author.id, "draw", bet_amount)
                        result_text = "🤝 **HÒA! Cả hai đều có Blackjack!**"
                        color = discord.Color.yellow()
                    else:
                        # Player blackjack wins
                        winnings = int(bet_amount * 2.5)
                        new_balance = shared_wallet.add_balance(ctx.author.id, winnings - bet_amount)
                        self.update_user_stats(ctx.author.id, "blackjack", bet_amount, winnings)
                        result_text = f"🎉 **BLACKJACK! Bạn thắng {winnings:,} xu!**"
                        color = discord.Color.gold()
                    
                    del self.active_games[ctx.author.id]
                    
                    embed = discord.Embed(
                        title="🃏 Blackjack - Kết thúc",
                        description=result_text,
                        color=color,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="🎴 Bài của bạn",
                        value=f"{self.format_hand(player_hand)} = **{player_value}**",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="🎴 Bài của dealer",
                        value=f"{self.format_hand(dealer_hand)} = **{self.calculate_hand_value(dealer_hand)}**",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="💳 Số dư mới",
                        value=f"**{new_balance:,} xu**",
                        inline=False
                    )
                    
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Regular game start
                embed = discord.Embed(
                    title="🃏 Blackjack - Ván mới",
                    description="Chọn hành động của bạn!",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🎴 Bài của bạn",
                    value=f"{self.format_hand(player_hand)} = **{player_value}**",
                    inline=False
                )
                
                embed.add_field(
                    name="🎴 Bài của dealer",
                    value=f"{self.format_hand(dealer_hand, hide_first=True)} = **{dealer_value}**",
                    inline=False
                )
                
                embed.add_field(
                    name="💰 Tiền cược",
                    value=f"**{bet_amount:,} xu**",
                    inline=True
                )
                
                embed.set_author(
                    name=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                embed.set_footer(text="Nhấn buttons để tiếp tục")
                
                # Create buttons view
                view = BlackjackView(ctx.author.id, self)
                
                await ctx.reply(embed=embed, view=view, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong blackjack command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi chơi blackjack!",
                    mention_author=True
                )
        
        
        @self.bot.command(name='bjstats')
        async def blackjack_stats(ctx, user: discord.Member = None):
            """Xem thống kê blackjack"""
            try:
                target_user = user or ctx.author
                user_data = self.get_user_data(target_user.id)
                
                total_games = user_data['total_games']
                if total_games == 0:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ {target_user.display_name} chưa chơi blackjack lần nào!",
                        mention_author=True
                    )
                    return
                
                win_rate = (user_data['wins'] / total_games) * 100
                
                embed = discord.Embed(
                    title="🃏 Thống Kê Blackjack",
                    color=discord.Color.dark_red(),
                    timestamp=datetime.now()
                )
                
                # Lấy số tiền THỰC TẾ từ shared wallet
                actual_balance = shared_wallet.get_balance(target_user.id)
                embed.add_field(
                    name="💰 Tài chính",
                    value=(
                        f"**Số dư:** {actual_balance:,} xu\n"
                        f"**Tổng cược:** {user_data['total_bet']:,} xu\n"
                        f"**Tổng thắng:** {user_data['total_won']:,} xu"
                    ),
                    inline=True
                )
                
                # Thêm trường thống kê số dư hiện tại
                embed.add_field(
                    name="🎯 Thành tích",
                    value=(
                        f"**Tổng ván:** {total_games:,}\n"
                        f"**Thắng:** {user_data['wins']:,}\n"
                        f"**Thua:** {user_data['losses']:,}\n"
                        f"**Hòa:** {user_data['draws']:,}\n"
                        f"**Blackjacks:** {user_data['blackjacks']:,}\n"
                        f"**Tỷ lệ thắng:** {win_rate:.1f}%"
                    ),
                    inline=True
                )
                
                embed.set_author(
                    name=target_user.display_name,
                    icon_url=target_user.avatar.url if target_user.avatar else None
                )
                embed.set_footer(text="Chơi với ;blackjack <số tiền>")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong blackjack stats command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem thống kê!",
                    mention_author=True
                )

class BlackjackView(discord.ui.View):
    """View chứa buttons cho blackjack game"""
    
    def __init__(self, user_id, blackjack_commands_instance):
        super().__init__(timeout=300)  # 5 phút timeout
        self.user_id = user_id
        self.blackjack_commands = blackjack_commands_instance
    
    @discord.ui.button(label='🃏 Hit', style=discord.ButtonStyle.primary, custom_id='hit')
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button Hit - Rút thêm bài"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Chỉ người chơi mới có thể sử dụng buttons này!", ephemeral=True)
            return
        
        if self.user_id not in self.blackjack_commands.active_games:
            await interaction.response.send_message("❌ Bạn không có ván blackjack nào đang chơi!", ephemeral=True)
            return
        
        game = self.blackjack_commands.active_games[self.user_id]
        
        # Draw card
        new_card = game['deck'].pop()
        game['player_hand'].append(new_card)
        
        player_value = self.blackjack_commands.calculate_hand_value(game['player_hand'])
        
        # Check for bust
        if player_value > 21:
            # Player busts - dealer wins
            shared_wallet.subtract_balance(self.user_id, game['bet_amount'])
            self.blackjack_commands.update_user_stats(self.user_id, "lose", game['bet_amount'])
            del self.blackjack_commands.active_games[self.user_id]
            
            embed = discord.Embed(
                title="🃏 Blackjack - Bust!",
                description="💥 **BẠN BỊ BUST! Dealer thắng!**",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎴 Bài của bạn",
                value=f"{self.blackjack_commands.format_hand(game['player_hand'])} = **{player_value}** (BUST)",
                inline=False
            )
            
            embed.add_field(
                name="💸 Mất tiền",
                value=f"**-{game['bet_amount']:,} xu**",
                inline=True
            )
            
            new_balance = shared_wallet.get_balance(self.user_id)
            embed.add_field(
                name="💳 Số dư mới",
                value=f"**{new_balance:,} xu**",
                inline=True
            )
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        # Continue game
        embed = discord.Embed(
            title="🃏 Blackjack - Rút bài",
            description=f"Bạn rút được: **{new_card}**",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎴 Bài của bạn",
            value=f"{self.blackjack_commands.format_hand(game['player_hand'])} = **{player_value}**",
            inline=False
        )
        
        dealer_value = self.blackjack_commands.calculate_hand_value([game['dealer_hand'][0]])
        embed.add_field(
            name="🎴 Bài của dealer",
            value=f"{self.blackjack_commands.format_hand(game['dealer_hand'], hide_first=True)} = **{dealer_value}**",
            inline=False
        )
        
        embed.set_footer(text="Nhấn Hit hoặc Stand để tiếp tục")
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='✋ Stand', style=discord.ButtonStyle.secondary, custom_id='stand')
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button Stand - Dừng lại"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Chỉ người chơi mới có thể sử dụng buttons này!", ephemeral=True)
            return
        
        if self.user_id not in self.blackjack_commands.active_games:
            await interaction.response.send_message("❌ Bạn không có ván blackjack nào đang chơi!", ephemeral=True)
            return
        
        game = self.blackjack_commands.active_games[self.user_id]
        
        # Kiểm tra unlucky system
        should_auto_win = False
        if hasattr(self.blackjack_commands.bot_instance, 'unluck_commands'):
            is_unlucky = self.blackjack_commands.bot_instance.unluck_commands.is_user_unlucky(self.user_id)
            if is_unlucky:
                # Unlucky user luôn thua
                should_auto_win = False
                logger.info(f"User {self.user_id} is unlucky - forcing blackjack loss")
            else:
                # Kiểm tra admin hay user thường
                is_admin = self.blackjack_commands.bot_instance.is_admin(self.user_id) or self.blackjack_commands.bot_instance.is_supreme_admin(self.user_id)
                
                # Tất cả user 60% tỷ lệ thắng
                should_win = random.random() < 0.6
                should_auto_win = should_win
                logger.info(f"User {self.user_id} - 60% win rate - {'WIN' if should_win else 'LOSE'}")
        else:
            # Fallback nếu không có unluck system
            is_admin = self.blackjack_commands.bot_instance.is_admin(self.user_id) or self.blackjack_commands.bot_instance.is_supreme_admin(self.user_id)
            # Tất cả user 60% tỷ lệ thắng (fallback)
            should_auto_win = random.random() < 0.6
            logger.info(f"User {self.user_id} - 60% win rate (fallback) - {'WIN' if should_auto_win else 'LOSE'}")
        
        # Dealer play logic
        if should_auto_win:
            # Force dealer to bust hoặc stay low
            while self.blackjack_commands.calculate_hand_value(game['dealer_hand']) < 17:
                if game['deck']:
                    game['dealer_hand'].append(game['deck'].pop())
                    dealer_value = self.blackjack_commands.calculate_hand_value(game['dealer_hand'])
                    if dealer_value >= 22:  # Dealer bust, player wins
                        break
                else:
                    break
        else:
            # Normal dealer play
            while self.blackjack_commands.calculate_hand_value(game['dealer_hand']) < 17:
                if game['deck']:
                    game['dealer_hand'].append(game['deck'].pop())
                else:
                    break
        
        player_value = self.blackjack_commands.calculate_hand_value(game['player_hand'])
        dealer_value = self.blackjack_commands.calculate_hand_value(game['dealer_hand'])
        
        # Determine winner and update wallet
        if dealer_value > 21:
            # Dealer busts - player wins
            winnings = game['bet_amount'] * 2
            new_balance = shared_wallet.add_balance(self.user_id, winnings - game['bet_amount'])
            self.blackjack_commands.update_user_stats(self.user_id, "win", game['bet_amount'], winnings)
            result_text = f"🎉 **Dealer BUST! Bạn thắng {winnings:,} xu!**"
            color = discord.Color.green()
        elif player_value > dealer_value:
            # Player wins
            winnings = game['bet_amount'] * 2
            new_balance = shared_wallet.add_balance(self.user_id, winnings - game['bet_amount'])
            self.blackjack_commands.update_user_stats(self.user_id, "win", game['bet_amount'], winnings)
            result_text = f"🎉 **Bạn thắng {winnings:,} xu!**"
            color = discord.Color.green()
        elif player_value < dealer_value:
            # Dealer wins
            new_balance = shared_wallet.subtract_balance(self.user_id, game['bet_amount'])
            self.blackjack_commands.update_user_stats(self.user_id, "lose", game['bet_amount'])
            result_text = f"😢 **Dealer thắng! Bạn mất {game['bet_amount']:,} xu!**"
            color = discord.Color.red()
        else:
            # Draw (no money change)
            new_balance = shared_wallet.get_balance(self.user_id)
            self.blackjack_commands.update_user_stats(self.user_id, "draw", game['bet_amount'])
            result_text = "🤝 **HÒA!**"
            color = discord.Color.yellow()
        
        del self.blackjack_commands.active_games[self.user_id]
        
        embed = discord.Embed(
            title="🃏 Blackjack - Kết thúc",
            description=result_text,
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎴 Bài của bạn",
            value=f"{self.blackjack_commands.format_hand(game['player_hand'])} = **{player_value}**",
            inline=False
        )
        
        embed.add_field(
            name="🎴 Bài của dealer",
            value=f"{self.blackjack_commands.format_hand(game['dealer_hand'])} = **{dealer_value}**",
            inline=False
        )
        
        embed.add_field(
            name="💳 Số dư mới",
            value=f"**{new_balance:,} xu**",
            inline=False
        )
        
        embed.set_footer(text="Chơi lại với ;blackjack <số tiền>")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='❌ Quit', style=discord.ButtonStyle.danger, custom_id='quit')
    async def quit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button Quit - Thoát ván"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Chỉ người chơi mới có thể sử dụng buttons này!", ephemeral=True)
            return
        
        if self.user_id not in self.blackjack_commands.active_games:
            await interaction.response.send_message("❌ Bạn không có ván blackjack nào đang chơi!", ephemeral=True)
            return
        
        game = self.blackjack_commands.active_games[self.user_id]
        new_balance = shared_wallet.subtract_balance(self.user_id, game['bet_amount'])
        self.blackjack_commands.update_user_stats(self.user_id, "lose", game['bet_amount'])
        del self.blackjack_commands.active_games[self.user_id]
        
        embed = discord.Embed(
            title="🃏 Blackjack - Thoát ván",
            description=f"❌ **Bạn đã thoát ván và mất {game['bet_amount']:,} xu!**",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="💳 Số dư mới",
            value=f"**{new_balance:,} xu**",
            inline=False
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
