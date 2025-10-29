"""
Game Modals - Modal popup forms cho tất cả games
Cho phép người chơi nhập số tiền qua textbox thay vì command
"""
import discord
from discord import ui
from utils.shared_wallet import shared_wallet
import logging

logger = logging.getLogger(__name__)

class RPSBetModal(ui.Modal, title='🎮 Rock Paper Scissors - Đặt Cược'):
    """Modal để nhập số tiền cược cho RPS game"""
    
    bet_amount = ui.TextInput(
        label='Số tiền cược',
        placeholder='Nhập số tiền muốn cược (10-10000 xu)',
        required=True,
        min_length=2,
        max_length=5,
        style=discord.TextStyle.short
    )
    
    def __init__(self, rps_commands):
        super().__init__()
        self.rps_commands = rps_commands
    
    async def on_submit(self, interaction: discord.Interaction):
        """Xử lý khi user submit modal"""
        try:
            # Validate số tiền
            try:
                bet_amount_int = int(self.bet_amount.value)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Số tiền không hợp lệ! Vui lòng nhập số nguyên.",
                    ephemeral=True
                )
                return
            
            if bet_amount_int < 10:
                await interaction.response.send_message(
                    "❌ Số tiền tối thiểu là **10 xu**!",
                    ephemeral=True
                )
                return
            
            if bet_amount_int > 10000:
                await interaction.response.send_message(
                    "❌ Số tiền tối đa là **10,000 xu**!",
                    ephemeral=True
                )
                return
            
            # Kiểm tra số dư
            if not shared_wallet.has_sufficient_balance(interaction.user.id, bet_amount_int):
                current_balance = shared_wallet.get_balance(interaction.user.id)
                await interaction.response.send_message(
                    f"❌ Không đủ tiền! Số dư hiện tại: **{current_balance:,} xu**",
                    ephemeral=True
                )
                return
            
            # Hiển thị buttons để chọn kéo/búa/bao
            embed = discord.Embed(
                title="✂️ Rock Paper Scissors",
                description=f"Bạn đã đặt cược **{bet_amount_int:,} xu**\n\nChọn lựa chọn của bạn:",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            
            embed.set_footer(text="Nhấn button để chọn!")
            
            # Create RPS choice view
            view = RPSChoiceView(self.rps_commands, interaction.user.id, bet_amount_int)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Lỗi trong RPS modal: {e}")
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi xử lý!",
                ephemeral=True
            )

class SlotBetModal(ui.Modal, title='🎰 Slot Machine - Đặt Cược'):
    """Modal để nhập số tiền cược cho Slot game"""
    
    bet_amount = ui.TextInput(
        label='Số tiền cược',
        placeholder='Nhập số tiền muốn cược (10-10000 xu)',
        required=True,
        min_length=2,
        max_length=5,
        style=discord.TextStyle.short
    )
    
    def __init__(self, slot_commands):
        super().__init__()
        self.slot_commands = slot_commands
    
    async def on_submit(self, interaction: discord.Interaction):
        """Xử lý khi user submit modal"""
        try:
            # Validate số tiền
            try:
                bet_amount_int = int(self.bet_amount.value)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Số tiền không hợp lệ! Vui lòng nhập số nguyên.",
                    ephemeral=True
                )
                return
            
            if bet_amount_int < 10:
                await interaction.response.send_message(
                    "❌ Số tiền tối thiểu là **10 xu**!",
                    ephemeral=True
                )
                return
            
            if bet_amount_int > 10000:
                await interaction.response.send_message(
                    "❌ Số tiền tối đa là **10,000 xu**!",
                    ephemeral=True
                )
                return
            
            # Kiểm tra số dư
            if not shared_wallet.has_sufficient_balance(interaction.user.id, bet_amount_int):
                current_balance = shared_wallet.get_balance(interaction.user.id)
                await interaction.response.send_message(
                    f"❌ Không đủ tiền! Số dú hiện tại: **{current_balance:,} xu**",
                    ephemeral=True
                )
                return
            
            # Slot Machine - xử lý với animation
            import random
            import asyncio
            from datetime import datetime
            
            # Defer response
            await interaction.response.defer()
            
            # Slot symbols
            symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎']
            symbol_multipliers = {
                '🍒': 2,    # Cherry
                '🍋': 3,    # Lemon  
                '🍊': 4,    # Orange
                '🍇': 5,    # Grape
                '🔔': 10,   # Bell
                '💎': 50    # Diamond (Jackpot symbol)
            }
            
            # Animation quay slot
            loading_embed = discord.Embed(
                title="🎰 Slot Machine",
                description="⚡ **Đang quay...** ⚡",
                color=discord.Color.purple()
            )
            loading_msg = await interaction.followup.send(embed=loading_embed)
            
            # Animation: Hiển thị icon ngẫu nhiên 8 lần
            for i in range(8):
                random_reels = [random.choice(symbols) for _ in range(3)]
                
                anim_embed = discord.Embed(
                    title="🎰 Slot Machine - Đang quay...",
                    description=f"**{random_reels[0]} {random_reels[1]} {random_reels[2]}**",
                    color=discord.Color.gold()
                )
                anim_embed.add_field(
                    name="💰 Tiền cược",
                    value=f"**{bet_amount_int:,} xu**",
                    inline=False
                )
                await loading_msg.edit(embed=anim_embed)
                await asyncio.sleep(0.3)
            
            # Quay kết quả cuối cùng
            reel1 = random.choice(symbols)
            reel2 = random.choice(symbols)
            reel3 = random.choice(symbols)
            
            # Check win condition
            won = False
            winnings = 0
            multiplier = 0
            
            if reel1 == reel2 == reel3:
                multiplier = symbol_multipliers[reel1]
                if reel1 == '💎':
                    multiplier = 100  # JACKPOT!
                winnings = bet_amount_int * multiplier
                won = True
            
            # Update wallet
            if won:
                new_balance = shared_wallet.add_balance(interaction.user.id, winnings - bet_amount_int)
            else:
                new_balance = shared_wallet.subtract_balance(interaction.user.id, bet_amount_int)
            
            # Update stats
            user_data = self.slot_commands.get_user_data(interaction.user.id)
            
            # Đảm bảo user_data có đầy đủ keys
            if 'total_spins' not in user_data:
                user_data['total_spins'] = 0
            if 'total_bet' not in user_data:
                user_data['total_bet'] = 0
            if 'wins' not in user_data:
                user_data['wins'] = 0
            if 'losses' not in user_data:
                user_data['losses'] = 0
            if 'total_won' not in user_data:
                user_data['total_won'] = 0
            if 'jackpots' not in user_data:
                user_data['jackpots'] = 0
            if 'biggest_win' not in user_data:
                user_data['biggest_win'] = 0
            
            user_data['total_spins'] += 1
            user_data['total_bet'] += bet_amount_int
            
            if won:
                user_data['wins'] += 1
                user_data['total_won'] += winnings
                if reel1 == '💎':
                    user_data['jackpots'] += 1
                if winnings > user_data['biggest_win']:
                    user_data['biggest_win'] = winnings
            else:
                user_data['losses'] += 1
            
            self.slot_commands.save_slot_data()
            
            # Hiển thị kết quả cuối trong 2 giây
            final_anim_embed = discord.Embed(
                title="🎰 Slot Machine - Kết quả!",
                description=f"✨ **{reel1} {reel2} {reel3}** ✨",
                color=discord.Color.purple()
            )
            await loading_msg.edit(embed=final_anim_embed)
            await asyncio.sleep(2)
            
            # Xóa animation
            try:
                await loading_msg.delete()
            except Exception as del_error:
                logger.warning(f"Không thể xóa animation message: {del_error}")
            
            # Create result embed
            logger.info(f"Slot result: {reel1} {reel2} {reel3} - Won: {won}, Winnings: {winnings}")
            
            if won:
                color = discord.Color.gold() if reel1 == '💎' else discord.Color.green()
                if reel1 == '💎':
                    result_text = f"💎 **JACKPOT! THẮNG {winnings:,} xu!** 💎"
                else:
                    result_text = f"🎉 **THẮNG {winnings:,} xu!**"
            else:
                color = discord.Color.red()
                result_text = f"😢 **THUA {bet_amount_int:,} xu!**"
            
            embed = discord.Embed(
                title="🎰 Slot Machine - Kết quả",
                description=result_text,
                color=color,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎰 Kết quả quay",
                value=f"**{reel1} {reel2} {reel3}**",
                inline=False
            )
            
            if won:
                embed.add_field(
                    name="✨ Multiplier",
                    value=f"**x{multiplier}**",
                    inline=True
                )
            
            embed.add_field(
                name="💰 Tiền cược",
                value=f"**{bet_amount_int:,} xu**",
                inline=True
            )
            
            if won:
                embed.add_field(
                    name="🎁 Tiền thắng",
                    value=f"**+{winnings - bet_amount_int:,} xu**",
                    inline=True
                )
            else:
                embed.add_field(
                    name="💸 Tiền thua",
                    value=f"**-{bet_amount_int:,} xu**",
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
            
            embed.set_footer(text="Chơi lại bằng ;game!")
            
            logger.info(f"Sending slot result embed to user {interaction.user.id}")
            await interaction.followup.send(embed=embed)
            logger.info(f"Slot result sent successfully")
            
        except Exception as e:
            logger.error(f"Lỗi trong Slot modal: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send(
                    "❌ Có lỗi xảy ra khi xử lý!",
                    ephemeral=True
                )
            except:
                pass

class BlackjackBetModal(ui.Modal, title='🃏 Blackjack - Đặt Cược'):
    """Modal để nhập số tiền cược cho Blackjack game"""
    
    bet_amount = ui.TextInput(
        label='Số tiền cược',
        placeholder='Nhập số tiền muốn cược (10-10000 xu)',
        required=True,
        min_length=2,
        max_length=5,
        style=discord.TextStyle.short
    )
    
    def __init__(self, blackjack_commands):
        super().__init__()
        self.blackjack_commands = blackjack_commands
    
    async def on_submit(self, interaction: discord.Interaction):
        """Xử lý khi user submit modal"""
        try:
            # Validate số tiền
            try:
                bet_amount_int = int(self.bet_amount.value)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Số tiền không hợp lệ! Vui lòng nhập số nguyên.",
                    ephemeral=True
                )
                return
            
            if bet_amount_int < 10:
                await interaction.response.send_message(
                    "❌ Số tiền tối thiểu là **10 xu**!",
                    ephemeral=True
                )
                return
            
            if bet_amount_int > 10000:
                await interaction.response.send_message(
                    "❌ Số tiền tối đa là **10,000 xu**!",
                    ephemeral=True
                )
                return
            
            # Kiểm tra số dư
            if not shared_wallet.has_sufficient_balance(interaction.user.id, bet_amount_int):
                current_balance = shared_wallet.get_balance(interaction.user.id)
                await interaction.response.send_message(
                    f"❌ Không đủ tiền! Số dư hiện tại: **{current_balance:,} xu**",
                    ephemeral=True
                )
                return
            
            # Start Blackjack - gọi command với số tiền đã nhập
            # Tạo fake message context
            await interaction.response.defer()
            
            # Gọi command blackjack với số tiền
            ctx = await interaction.client.get_context(interaction.message) if hasattr(interaction, 'message') else None
            
            # Fallback: Thông báo dùng lệnh
            embed = discord.Embed(
                title="🃏 Blackjack",
                description=f"Bạn đã chọn **{bet_amount_int:,} xu**",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="ℹ️ Hướng dẫn",
                value=(
                    f"Sử dụng lệnh sau để chơi:\n"
                    f"**; {bet_amount_int}`**\n\n"
                    f"Hoặc: **; {bet_amount_int}`**"
                ),
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Lỗi trong Blackjack modal: {e}")
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi xử lý!",
                ephemeral=True
            )

class FlipCoinBetModal(ui.Modal, title='🪙 Flip Coin - Đặt Cược'):
    """Modal để nhập số tiền cược cho Flip Coin game"""
    
    bet_amount = ui.TextInput(
        label='Số tiền cược',
        placeholder='Nhập số tiền muốn cược (10-10000 xu)',
        required=True,
        min_length=2,
        max_length=5,
        style=discord.TextStyle.short
    )
    
    def __init__(self, flip_commands):
        super().__init__()
        self.flip_commands = flip_commands
    
    async def on_submit(self, interaction: discord.Interaction):
        """Xử lý khi user submit modal"""
        try:
            # Validate số tiền
            try:
                bet_amount_int = int(self.bet_amount.value)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Số tiền không hợp lệ! Vui lòng nhập số nguyên.",
                    ephemeral=True
                )
                return
            
            if bet_amount_int < 10:
                await interaction.response.send_message(
                    "❌ Số tiền tối thiểu là **10 xu**!",
                    ephemeral=True
                )
                return
            
            if bet_amount_int > 10000:
                await interaction.response.send_message(
                    "❌ Số tiền tối đa là **10,000 xu**!",
                    ephemeral=True
                )
                return
            
            # Kiểm tra số dư
            if not shared_wallet.has_sufficient_balance(interaction.user.id, bet_amount_int):
                current_balance = shared_wallet.get_balance(interaction.user.id)
                await interaction.response.send_message(
                    f"❌ Không đủ tiền! Số dư hiện tại: **{current_balance:,} xu**",
                    ephemeral=True
                )
                return
            
            # Show heads/tails choice buttons
            embed = discord.Embed(
                title="🪙 Flip Coin - Chọn mặt đồng xu",
                description=f"Bạn đã đặt cược **{bet_amount_int:,} xu**\n\nChọn mặt đồng xu:",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
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
                name=interaction.user.display_name,
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            
            embed.set_footer(text="Nhấn button để chọn!")
            
            # Flip Coin đã có button system - dùng luôn
            from .flip_coin_commands import FlipCoinView
            view = FlipCoinView(self.flip_commands, interaction.user.id, bet_amount_int)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Lỗi trong Flip Coin modal: {e}")
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi xử lý!",
                ephemeral=True
            )

class TaiXiuBetModal(ui.Modal, title='🎲 Tài Xỉu - Đặt Cược'):
    """Modal để nhập số tiền cược cho Tài Xỉu game"""
    
    bet_amount = ui.TextInput(
        label='Số tiền cược',
        placeholder='Nhập số tiền muốn cược (100-10000 xu)',
        required=True,
        min_length=3,
        max_length=5,
        style=discord.TextStyle.short
    )
    
    def __init__(self, taixiu_commands):
        super().__init__()
        self.taixiu_commands = taixiu_commands
    
    async def on_submit(self, interaction: discord.Interaction):
        """Xử lý khi user submit modal"""
        try:
            # Validate số tiền
            try:
                bet_amount_int = int(self.bet_amount.value)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Số tiền không hợp lệ! Vui lòng nhập số nguyên.",
                    ephemeral=True
                )
                return
            
            if bet_amount_int < 100:
                await interaction.response.send_message(
                    "❌ Số tiền tối thiểu là **100 xu**!",
                    ephemeral=True
                )
                return
            
            if bet_amount_int > 10000:
                await interaction.response.send_message(
                    "❌ Số tiền tối đa là **10,000 xu**!",
                    ephemeral=True
                )
                return
            
            # Kiểm tra số dư
            current_balance = shared_wallet.get_balance(interaction.user.id)
            if not shared_wallet.has_sufficient_balance(interaction.user.id, bet_amount_int):
                await interaction.response.send_message(
                    f"❌ Không đủ tiền! Số dư hiện tại: **{current_balance:,} xu**",
                    ephemeral=True
                )
                return
            
            # Show TÀI/XỈU choice buttons
            embed = discord.Embed(
                title="🎲 Tài Xỉu - Chọn Tài hoặc Xỉu",
                description=f"Bạn đã đặt cược **{bet_amount_int:,} xu**\n\nChọn Tài hoặc Xỉu:",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📈 TÀI",
                value="Tổng 11-17 điểm",
                inline=True
            )
            
            embed.add_field(
                name="📉 XỈU",
                value="Tổng 4-10 điểm",
                inline=True
            )
            
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            
            embed.set_footer(text="Nhấn button để chọn!")
            
            # Create choice buttons view
            view = TaiXiuChoiceView(self.taixiu_commands, interaction.user.id, bet_amount_int)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Lỗi trong Tài Xỉu modal: {e}")
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi xử lý!",
                ephemeral=True
            )

class TaiXiuChoiceView(discord.ui.View):
    """View với buttons cho Tài Xỉu choice"""
    
    def __init__(self, taixiu_commands, user_id, bet_amount):
        super().__init__(timeout=60)
        self.taixiu_commands = taixiu_commands
        self.user_id = user_id
        self.bet_amount = bet_amount
    
    @discord.ui.button(label='📈 TÀI', style=discord.ButtonStyle.success, custom_id='tai')
    async def tai_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button chọn Tài"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải game của bạn!",
                ephemeral=True
            )
            return
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        
        # Play Tài Xỉu với TÀI
        await self.play_taixiu(interaction, "TÀI")
    
    @discord.ui.button(label='📉 XỈU', style=discord.ButtonStyle.danger, custom_id='xiu')
    async def xiu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button chọn Xỉu"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải game của bạn!",
                ephemeral=True
            )
            return
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        
        # Play Tài Xỉu với XỈU
        await self.play_taixiu(interaction, "XỈU")
    
    async def play_taixiu(self, interaction: discord.Interaction, choice: str):
        """Xử lý Tài Xỉu game"""
        try:
            import random
            import asyncio
            from datetime import datetime
            
            # Defer response để có thời gian xử lý
            await interaction.response.defer()
            
            # Animation với số ngẫu nhiên đổi liên tục
            loading_embed = discord.Embed(
                title="🎲 Tài Xỉu - Đang quay...",
                description="⚡ **Đang quay xúc xắc...** ⚡",
                color=discord.Color.blue()
            )
            loading_msg = await interaction.followup.send(embed=loading_embed)
            
            # Animation: Hiển thị số ngẫu nhiên thay đổi 10 lần
            for i in range(10):
                random_nums = [random.randint(1, 6) for _ in range(3)]
                random_total = sum(random_nums)
                
                anim_embed = discord.Embed(
                    title="🎲 Tài Xỉu - Đang quay...",
                    description=f"🎲 **{random_nums[0]}** 🎲 **{random_nums[1]}** 🎲 **{random_nums[2]}**\n\n💫 Tổng: **{random_total}** 💫",
                    color=discord.Color.gold()
                )
                await loading_msg.edit(embed=anim_embed)
                await asyncio.sleep(0.3)  # Delay 0.3s giữa mỗi lần đổi
            
            # Quay kết quả cuối cùng
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)
            dice3 = random.randint(1, 6)
            total = dice1 + dice2 + dice3
            
            # Hiển thị kết quả cuối trong 2 giây
            final_anim_embed = discord.Embed(
                title="🎲 Tài Xỉu - Kết quả!",
                description=f"🎲 **{dice1}** 🎲 **{dice2}** 🎲 **{dice3}**\n\n✨ Tổng: **{total}** ✨",
                color=discord.Color.purple()
            )
            await loading_msg.edit(embed=final_anim_embed)
            await asyncio.sleep(2)
            
            # Xóa animation message
            try:
                await loading_msg.delete()
            except:
                pass
            
            # Xác định TÀI hoặc XỈU
            result = "TÀI" if total >= 11 else "XỈU"
            won = (choice == result)
            
            # Cập nhật tiền
            if won:
                new_balance = shared_wallet.add_balance(self.user_id, self.bet_amount)
                money_change = self.bet_amount
            else:
                new_balance = shared_wallet.subtract_balance(self.user_id, self.bet_amount)
                money_change = -self.bet_amount
            
            # Update stats
            self.taixiu_commands._ensure_player_data(self.user_id)
            self.taixiu_commands.update_player_money(self.user_id, money_change, won, self.bet_amount)
            
            # Create result embed
            if won:
                color = discord.Color.green()
                result_text = f"🎉 **BẠN THẮNG {self.bet_amount * 2:,} xu!**"
            else:
                color = discord.Color.red()
                result_text = f"😢 **BẠN THUA {self.bet_amount:,} xu!**"
            
            embed = discord.Embed(
                title="🎲 Tài Xỉu - Kết quả",
                description=result_text,
                color=color,
                timestamp=datetime.now()
            )
            
            # Dice emojis
            dice_emoji = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
            
            embed.add_field(
                name="🎲 Kết quả xúc xắc",
                value=f"{dice_emoji[dice1]} {dice_emoji[dice2]} {dice_emoji[dice3]}\n**Tổng: {total} điểm**",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Bạn chọn",
                value=f"**{choice}**",
                inline=True
            )
            
            embed.add_field(
                name="🎲 Kết quả",
                value=f"**{result}** ({total} điểm)",
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
            
            embed.set_footer(text="Chơi lại bằng ;game!")
            
            # Edit message ban đầu với kết quả
            await interaction.edit_original_response(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Lỗi trong Tài Xỉu game: {e}")
            try:
                await interaction.followup.send(
                    "❌ Có lỗi xảy ra khi chơi!",
                    ephemeral=True
                )
            except:
                pass
    
    async def on_timeout(self):
        """Xử lý khi view timeout"""
        for item in self.children:
            item.disabled = True

# ==================== CHOICE VIEWS ====================

class RPSChoiceView(discord.ui.View):
    """View với buttons cho RPS choice"""
    
    def __init__(self, rps_commands, user_id, bet_amount):
        super().__init__(timeout=60)
        self.rps_commands = rps_commands
        self.user_id = user_id
        self.bet_amount = bet_amount
    
    @discord.ui.button(label='✂️ Kéo', style=discord.ButtonStyle.primary, custom_id='scissors')
    async def scissors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button chọn Kéo"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải game của bạn!",
                ephemeral=True
            )
            return
        
        await self.play_rps(interaction, 'scissors')
    
    @discord.ui.button(label='🔨 Búa', style=discord.ButtonStyle.danger, custom_id='rock')
    async def rock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button chọn Búa"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải game của bạn!",
                ephemeral=True
            )
            return
        
        await self.play_rps(interaction, 'rock')
    
    @discord.ui.button(label='📄 Bao', style=discord.ButtonStyle.success, custom_id='paper')
    async def paper_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button chọn Bao"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Đây không phải game của bạn!",
                ephemeral=True
            )
            return
        
        await self.play_rps(interaction, 'paper')
    
    async def play_rps(self, interaction: discord.Interaction, player_choice: str):
        """Xử lý RPS game"""
        try:
            import random
            import asyncio
            from datetime import datetime
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            # Defer response
            await interaction.response.defer()
            
            # Animation
            choices = ['rock', 'paper', 'scissors']
            choice_emoji = {
                'rock': '🔨',
                'paper': '📄',
                'scissors': '✂️'
            }
            
            loading_embed = discord.Embed(
                title="✂️ Kéo Búa Bao",
                description="⚡ **Đang chọn...** ⚡",
                color=discord.Color.blue()
            )
            loading_msg = await interaction.followup.send(embed=loading_embed)
            
            # Animation: Bot "suy nghĩ" 6 lần
            for i in range(6):
                random_choice = random.choice(choices)
                
                anim_embed = discord.Embed(
                    title="✂️ Kéo Búa Bao - Bot đang chọn...",
                    description=f"🤖 Bot: **{choice_emoji[random_choice]}**",
                    color=discord.Color.gold()
                )
                await loading_msg.edit(embed=anim_embed)
                await asyncio.sleep(0.25)
            
            # Bot chọn kết quả cuối cùng
            bot_choice = random.choice(choices)
            
            # Hiển thị lựa chọn cuối 1.5 giây
            final_choice_embed = discord.Embed(
                title="✂️ Kéo Búa Bao - Đã chọn!",
                description=f"🤖 Bot: **{choice_emoji[bot_choice]}**\n👤 Bạn: **{choice_emoji[player_choice]}**",
                color=discord.Color.purple()
            )
            await loading_msg.edit(embed=final_choice_embed)
            await asyncio.sleep(1.5)
            
            # Xóa animation
            try:
                await loading_msg.delete()
            except:
                pass
            
            # Xác định kết quả
            choice_map = {
                'rock': '🔨 Búa',
                'paper': '📄 Bao',
                'scissors': '✂️ Kéo'
            }
            
            win_conditions = {
                'rock': 'scissors',
                'paper': 'rock',
                'scissors': 'paper'
            }
            
            if player_choice == bot_choice:
                result = 'draw'
                color = discord.Color.blue()
                result_text = "🤝 **HÒA!**"
                money_change = 0
            elif win_conditions[player_choice] == bot_choice:
                result = 'win'
                color = discord.Color.green()
                result_text = f"🎉 **BẠN THẮNG {self.bet_amount * 2:,} xu!**"
                money_change = self.bet_amount
            else:
                result = 'loss'
                color = discord.Color.red()
                result_text = f"😢 **BẠN THUA {self.bet_amount:,} xu!**"
                money_change = -self.bet_amount
            
            # Cập nhật tiền và stats
            if money_change > 0:
                new_balance = shared_wallet.add_balance(self.user_id, money_change)
            elif money_change < 0:
                new_balance = shared_wallet.subtract_balance(self.user_id, abs(money_change))
            else:
                new_balance = shared_wallet.get_balance(self.user_id)
            
            # Update stats
            user_data = self.rps_commands.get_user_data(self.user_id)
            user_data['total_games'] += 1
            user_data['total_bet'] += self.bet_amount
            
            if result == 'win':
                user_data['wins'] += 1
                user_data['total_won'] += money_change
            elif result == 'loss':
                user_data['losses'] += 1
            else:
                user_data['draws'] += 1
            
            self.rps_commands.save_rps_data()
            
            # Create result embed
            embed = discord.Embed(
                title="✂️ Rock Paper Scissors - Kết quả",
                description=result_text,
                color=color,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎯 Bạn chọn",
                value=choice_map[player_choice],
                inline=True
            )
            
            embed.add_field(
                name="🤖 Bot chọn",
                value=choice_map[bot_choice],
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
            
            if result == 'win':
                embed.add_field(
                    name="🎁 Tiền thắng",
                    value=f"**+{money_change:,} xu**",
                    inline=True
                )
            elif result == 'loss':
                embed.add_field(
                    name="💸 Tiền thua",
                    value=f"**{money_change:,} xu**",
                    inline=True
                )
            else:
                embed.add_field(
                    name="🤝 Hòa",
                    value="**0 xu**",
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
            
            embed.set_footer(text="Chơi lại bằng ;game!")
            
            # Gửi kết quả mới
            await interaction.followup.send(embed=embed)
            
            # Xóa tin nhắn đặt cược ban đầu
            try:
                await interaction.message.delete()
            except:
                pass
            
        except Exception as e:
            logger.error(f"Lỗi trong RPS game: {e}")
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi chơi!",
                ephemeral=True
            )
    
    async def on_timeout(self):
        """Xử lý khi view timeout"""
        for item in self.children:
            item.disabled = True
