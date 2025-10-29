import discord
import json
import os
import random
import time
from datetime import datetime
from utils.shared_wallet import SharedWallet

class FishingCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        
        # File lưu trữ dữ liệu câu cá
        self.fishing_data_file = 'data/fishing_data.json'
        self.fishing_data = self.load_fishing_data()
        
        # Cấu hình game câu cá
        self.FISHING_COOLDOWN = 300  # 5 phút cooldown
        self.FISHING_COST = 1000     # Chi phí mỗi lần câu: 1000 xu
        self.FREE_FISHING_COOLDOWN = 600  # 10 phút cooldown cho câu miễn phí
        
        # Hệ thống cần câu - càng xịn càng dễ ra cá hiếm
        self.FISHING_RODS = {
            "basic": {
                "name": "🎣 Cần Câu Cơ Bản", 
                "price": 0, 
                "trash_bonus": 0, 
                "common_bonus": 0, 
                "rare_bonus": 0, 
                "epic_bonus": 0, 
                "legendary_bonus": 0,
                "description": "Cần câu miễn phí - tỷ lệ cá thường 100%"
            },
            "iron": {
                "name": "⚙️ Cần Câu Sắt", 
                "price": 50000, 
                "trash_bonus": -10, 
                "common_bonus": +5, 
                "rare_bonus": +3, 
                "epic_bonus": +1, 
                "legendary_bonus": +1,
                "description": "Giảm 10% cá rác, tăng 5% cá thường, 3% cá hiếm"
            },
            "gold": {
                "name": "🥇 Cần Câu Vàng", 
                "price": 200000, 
                "trash_bonus": -20, 
                "common_bonus": +10, 
                "rare_bonus": +7, 
                "epic_bonus": +2, 
                "legendary_bonus": +1,
                "description": "Giảm 20% cá rác, tăng 10% cá thường, 7% cá hiếm"
            },
            "diamond": {
                "name": "💎 Cần Câu Kim Cương", 
                "price": 500000, 
                "trash_bonus": -30, 
                "common_bonus": +15, 
                "rare_bonus": +10, 
                "epic_bonus": +3, 
                "legendary_bonus": +2,
                "description": "Giảm 30% cá rác, tăng 15% cá thường, 10% cá hiếm"
            },
            "legendary": {
                "name": "🌟 Cần Câu Huyền Thoại", 
                "price": 1000000, 
                "trash_bonus": -40, 
                "common_bonus": +20, 
                "rare_bonus": +15, 
                "epic_bonus": +4, 
                "legendary_bonus": +3,
                "description": "Giảm 40% cá rác, tăng 20% cá thường, 15% cá hiếm, 3% huyền thoại"
            }
        }
        
        # Danh sách cá và tỷ lệ xuất hiện
        self.FISH_TYPES = {
            # Cá rất thường (60% tỷ lệ) - Giá rẻ nhất
            "🦐": {"name": "Tôm Nhỏ", "price": 10, "rarity": "trash", "chance": 18},
            "🐚": {"name": "Ốc Biển", "price": 15, "rarity": "trash", "chance": 15},
            "🦀": {"name": "Cua Nhỏ", "price": 20, "rarity": "trash", "chance": 15},
            "🪼": {"name": "Sứa", "price": 25, "rarity": "trash", "chance": 12},
            
            # Cá thường (25% tỷ lệ) - Giá trung bình thấp  
            "🐟": {"name": "Cá Nhỏ", "price": 50, "rarity": "common", "chance": 6},
            "🐠": {"name": "Cá Nhiệt Đới", "price": 80, "rarity": "common", "chance": 5},
            "🎣": {"name": "Cá Cần Câu", "price": 120, "rarity": "common", "chance": 4},
            "🐡": {"name": "Cá Nóc", "price": 150, "rarity": "common", "chance": 3},
            "🐝": {"name": "Cá Vàng", "price": 200, "rarity": "common", "chance": 2.5},
            "🦑": {"name": "Mực Nhỏ", "price": 180, "rarity": "common", "chance": 2},
            "🐛": {"name": "Giun Biển", "price": 30, "rarity": "common", "chance": 1.5},
            "🦋": {"name": "Cá Bướm", "price": 250, "rarity": "common", "chance": 1},
            "🐌": {"name": "Ốc Sên Biển", "price": 40, "rarity": "common", "chance": 0.5},
            
            # Cá hiếm (25% tỷ lệ) - Giá trung bình
            "🦈": {"name": "Cá Mập", "price": 500, "rarity": "rare", "chance": 4},
            "🐙": {"name": "Bạch Tuộc", "price": 450, "rarity": "rare", "chance": 3.5},
            "🦞": {"name": "Tôm Hùm", "price": 600, "rarity": "rare", "chance": 3},
            "🐋": {"name": "Cá Voi", "price": 800, "rarity": "rare", "chance": 2.5},
            "🐢": {"name": "Rùa Biển", "price": 700, "rarity": "rare", "chance": 2},
            "🦭": {"name": "Hải Cẩu", "price": 650, "rarity": "rare", "chance": 2},
            "🐧": {"name": "Chim Cánh Cụt", "price": 550, "rarity": "rare", "chance": 1.5},
            "🦆": {"name": "Vịt Biển", "price": 400, "rarity": "rare", "chance": 1.5},
            "🐊": {"name": "Cá Sấu Biển", "price": 900, "rarity": "rare", "chance": 1},
            "🦎": {"name": "Thằn Lằn Biển", "price": 350, "rarity": "rare", "chance": 1},
            "🐍": {"name": "Rắn Biển", "price": 750, "rarity": "rare", "chance": 1},
            "🕷️": {"name": "Nhện Biển", "price": 300, "rarity": "rare", "chance": 1},
            "🦂": {"name": "Bọ Cạp Biển", "price": 850, "rarity": "rare", "chance": 0.5},
            
            # Cá siêu hiếm (8% tỷ lệ) - Giá cao
            "🐉": {"name": "Rồng Biển", "price": 2000, "rarity": "epic", "chance": 2},
            "🧜": {"name": "Nàng Tiên Cá", "price": 2500, "rarity": "epic", "chance": 1.5},
            "🦄": {"name": "Kỳ Lân Biển", "price": 3000, "rarity": "epic", "chance": 1},
            "👑": {"name": "Vua Biển", "price": 3500, "rarity": "epic", "chance": 1},
            "💎": {"name": "Cá Kim Cương", "price": 4000, "rarity": "epic", "chance": 0.8},
            "🌟": {"name": "Cá Ngôi Sao", "price": 4500, "rarity": "epic", "chance": 0.7},
            
            # Cá huyền thoại (2% tỷ lệ) - Giá cực cao
            "⭐": {"name": "Cá Sao Vàng", "price": 10000, "rarity": "legendary", "chance": 0.5},
            "🔥": {"name": "Phượng Hoàng Biển", "price": 15000, "rarity": "legendary", "chance": 0.3},
            "⚡": {"name": "Sấm Sét Biển", "price": 20000, "rarity": "legendary", "chance": 0.2},
            "🌈": {"name": "Cầu Vồng Biển", "price": 25000, "rarity": "legendary", "chance": 0.1},
            "💫": {"name": "Thiên Thần Biển", "price": 50000, "rarity": "legendary", "chance": 0.05}
        }
        
        # Màu sắc theo độ hiếm
        self.RARITY_COLORS = {
            "trash": discord.Color.light_grey(),      # Cá rác - Xám nhạt
            "common": discord.Color.green(),          # Cá thường - Xanh lá
            "rare": discord.Color.blue(),             # Cá hiếm - Xanh dương
            "epic": discord.Color.purple(),           # Cá siêu hiếm - Tím
            "legendary": discord.Color.gold()         # Cá huyền thoại - Vàng
        }
        
    def load_fishing_data(self):
        """Load dữ liệu câu cá"""
        if os.path.exists(self.fishing_data_file):
            try:
                with open(self.fishing_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_fishing_data(self):
        """Save dữ liệu câu cá"""
        os.makedirs(os.path.dirname(self.fishing_data_file), exist_ok=True)
        with open(self.fishing_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.fishing_data, f, ensure_ascii=False, indent=2)
    
    def get_user_fishing_data(self, user_id):
        """Lấy dữ liệu câu cá của user"""
        user_id_str = str(user_id)
        if user_id_str not in self.fishing_data:
            self.fishing_data[user_id_str] = {
                'fish_inventory': {},
                'total_fished': 0,
                'total_sold': 0,
                'total_earned': 0,
                'last_fishing_time': 0,
                'last_free_fishing_time': 0,  # Thời gian câu miễn phí lần cuối
                'fishing_level': 1,
                'fishing_exp': 0,
                'current_rod': 'basic',  # Cần câu hiện tại
                'owned_rods': ['basic']  # Danh sách cần câu đã mua
            }
        return self.fishing_data[user_id_str]
    
    def get_random_fish(self, user_level=1, rod_type="basic"):
        """Random cá dựa trên tỷ lệ, level và loại cần câu"""
        # Tăng tỷ lệ cá hiếm theo level
        level_bonus = min(user_level * 2, 20)  # Tối đa +20% cho cá hiếm
        
        # Bonus từ cần câu
        rod_bonus = self.FISHING_RODS.get(rod_type, self.FISHING_RODS["basic"])
        
        # Tạo danh sách weighted choices
        choices = []
        weights = []
        
        for fish_emoji, fish_data in self.FISH_TYPES.items():
            base_chance = fish_data["chance"]
            rarity = fish_data["rarity"]
            
            # Áp dụng bonus từ cần câu
            rod_multiplier = 1.0
            if rarity == "trash":
                rod_multiplier += rod_bonus["trash_bonus"] / 100.0
            elif rarity == "common":
                rod_multiplier += rod_bonus["common_bonus"] / 100.0
            elif rarity == "rare":
                rod_multiplier += rod_bonus["rare_bonus"] / 100.0
            elif rarity == "epic":
                rod_multiplier += rod_bonus["epic_bonus"] / 100.0
            elif rarity == "legendary":
                rod_multiplier += rod_bonus["legendary_bonus"] / 100.0
            
            # Tăng tỷ lệ cá hiếm theo level
            if rarity in ["rare", "epic", "legendary"]:
                level_multiplier = 1 + (level_bonus * 0.01)
            else:
                level_multiplier = 1.0
                
            # Tính tỷ lệ cuối cùng
            adjusted_chance = base_chance * rod_multiplier * level_multiplier
            adjusted_chance = max(0.1, adjusted_chance)  # Tối thiểu 0.1%
                
            choices.append(fish_emoji)
            weights.append(adjusted_chance)
        
        return random.choices(choices, weights=weights)[0]
    
    def add_fishing_exp(self, user_data, fish_rarity):
        """Thêm EXP câu cá"""
        exp_gain = {
            "trash": 5,        # Cá rác - 5 EXP
            "common": 10,      # Cá thường - 10 EXP
            "rare": 25,        # Cá hiếm - 25 EXP
            "epic": 50,        # Cá siêu hiếm - 50 EXP
            "legendary": 100   # Cá huyền thoại - 100 EXP
        }
        user_data['fishing_exp'] += exp_gain.get(fish_rarity, 5)
        
        # Kiểm tra level up
        exp_needed = user_data['fishing_level'] * 100
        if user_data['fishing_exp'] >= exp_needed:
            user_data['fishing_level'] += 1
            user_data['fishing_exp'] = 0
            return True  # Level up
        return False
    
    def register_commands(self):
        """Đăng ký các lệnh câu cá"""
        
        @self.bot.command(name='cauca', aliases=['fishing', 'fish'])
        async def fishing_command(ctx):
            """Lệnh câu cá"""
            user_id = ctx.author.id
            current_time = int(time.time())
            
            # Lấy dữ liệu user
            user_data = self.get_user_fishing_data(user_id)
            
            # Bỏ cooldown - có thể câu cá liên tục
            # last_fishing = user_data.get('last_fishing_time', 0)
            # if current_time - last_fishing < self.FISHING_COOLDOWN:
            #     remaining = self.FISHING_COOLDOWN - (current_time - last_fishing)
            #     minutes = remaining // 60
            #     seconds = remaining % 60
            #     
            #     embed = discord.Embed(
            #         title="⏰ Cooldown Câu Cá",
            #         description=f"Bạn cần nghỉ ngơi trước khi câu cá tiếp!",
            #         color=discord.Color.orange()
            #     )
            #     embed.add_field(
            #         name="⏳ Thời gian còn lại:",
            #         value=f"{minutes}m {seconds}s",
            #         inline=False
            #     )
            #     embed.add_field(
            #         name="💡 Lưu ý:",
            #         value="Mỗi lần câu cá cách nhau 5 phút để cá có thời gian tập trung lại!",
            #         inline=False
            #     )
            #     await ctx.reply(embed=embed, mention_author=True)
            #     return
            
            # Câu cá giờ đã miễn phí - không cần kiểm tra tiền
            # if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
            #     current_balance = self.bot_instance.shared_wallet.get_balance(user_id)
            #     if current_balance < self.FISHING_COST:
            #         embed = discord.Embed(
            #             title="💸 Không Đủ Tiền",
            #             description=f"Bạn cần **{self.FISHING_COST:,} xu** để thuê dụng cụ câu cá!",
            #             color=discord.Color.red()
            #         )
            #         embed.add_field(
            #             name="💰 Số dư hiện tại:",
            #             value=f"{current_balance:,} xu",
            #             inline=True
            #         )
            #         embed.add_field(
            #             name="💡 Gợi ý:",
            #             value="Chơi các game khác để kiếm thêm xu!",
            #             inline=True
            #         )
            #         await ctx.reply(embed=embed, mention_author=True)
            #         return
            #     
            #     # Trừ tiền thuê dụng cụ
            #     self.bot_instance.shared_wallet.subtract_balance(user_id, self.FISHING_COST)
            
            # Bắt đầu câu cá
            fishing_embed = discord.Embed(
                title="🎣 Đang Câu Cá...",
                description=f"{ctx.author.mention} đang thả câu xuống nước...",
                color=discord.Color.blue()
            )
            fishing_embed.add_field(
                name="⚡ Trạng thái:",
                value="Đang chờ cá cắn câu... 🐟",
                inline=False
            )
            fishing_embed.set_footer(text="Vui lòng chờ kết quả...")
            
            message = await ctx.reply(embed=fishing_embed, mention_author=True)
            
            # Bỏ delay để câu cá nhanh hơn
            # import asyncio
            # await asyncio.sleep(3)
            
            # Random cá với cần câu hiện tại
            current_rod = user_data.get('current_rod', 'basic')
            fish_emoji = self.get_random_fish(user_data['fishing_level'], current_rod)
            fish_info = self.FISH_TYPES[fish_emoji]
            
            # Cập nhật inventory
            if fish_emoji not in user_data['fish_inventory']:
                user_data['fish_inventory'][fish_emoji] = 0
            user_data['fish_inventory'][fish_emoji] += 1
            
            # Cập nhật thống kê
            user_data['total_fished'] += 1
            user_data['last_fishing_time'] = current_time
            
            # Thêm EXP và kiểm tra level up
            leveled_up = self.add_fishing_exp(user_data, fish_info['rarity'])
            
            # Lưu dữ liệu
            self.save_fishing_data()
            
            # Tạo embed kết quả
            result_embed = discord.Embed(
                title="🎉 Câu Cá Thành Công!",
                description=f"{ctx.author.mention} đã câu được:",
                color=self.RARITY_COLORS[fish_info['rarity']]
            )
            
            rarity_text = {
                "trash": "⚪ Rác",
                "common": "🟢 Thường",
                "rare": "🔵 Hiếm", 
                "epic": "🟣 Siêu Hiếm",
                "legendary": "🟡 Huyền Thoại"
            }
            
            result_embed.add_field(
                name="🐟 Loại cá:",
                value=f"{fish_emoji} **{fish_info['name']}**",
                inline=True
            )
            result_embed.add_field(
                name="💎 Độ hiếm:",
                value=rarity_text[fish_info['rarity']],
                inline=True
            )
            result_embed.add_field(
                name="💰 Giá bán:",
                value=f"{fish_info['price']:,} xu",
                inline=True
            )
            
            # Thông tin level
            result_embed.add_field(
                name="🎯 Level câu cá:",
                value=f"Level {user_data['fishing_level']} ({user_data['fishing_exp']}/100 EXP)",
                inline=False
            )
            
            if leveled_up:
                result_embed.add_field(
                    name="🎊 LEVEL UP!",
                    value=f"Chúc mừng! Bạn đã lên Level {user_data['fishing_level']}!\nTỷ lệ câu cá hiếm tăng lên!",
                    inline=False
                )
            
            result_embed.add_field(
                name="📊 Thống kê:",
                value=f"Tổng cá đã câu: **{user_data['total_fished']}** con",
                inline=False
            )
            
            result_embed.add_field(
                name="💡 Lưu ý:",
                value="• Không có cooldown - câu cá liên tục!\n• Dùng `;sell` để bán cá lấy xu hoặc `;kho` để xem kho cá!\n• Dùng `;rodshop` để mua cần câu tốt hơn!",
                inline=False
            )
            
            result_embed.set_footer(text="🆓 Câu cá miễn phí - Không cooldown - Mua cần câu tốt hơn để tăng tỷ lệ cá hiếm!")
            
            await message.edit(embed=result_embed)
        
        @self.bot.command(name='freefishing', aliases=['caucafree', 'fishfree'])
        async def free_fishing_command(ctx):
            """Lệnh câu cá miễn phí với cần câu cơ bản"""
            user_id = ctx.author.id
            current_time = int(time.time())
            
            # Lấy dữ liệu user
            user_data = self.get_user_fishing_data(user_id)
            
            # Bỏ cooldown cho câu miễn phí - có thể câu liên tục
            # last_free_fishing = user_data.get('last_free_fishing_time', 0)
            # if current_time - last_free_fishing < self.FREE_FISHING_COOLDOWN:
            #     remaining = self.FREE_FISHING_COOLDOWN - (current_time - last_free_fishing)
            #     minutes = remaining // 60
            #     seconds = remaining % 60
            #     
            #     embed = discord.Embed(
            #         title="⏰ Câu Cá Miễn Phí - Cooldown",
            #         description=f"Bạn cần đợi **{minutes}m {seconds}s** nữa để câu cá miễn phí!",
            #         color=discord.Color.orange()
            #     )
            #     embed.add_field(
            #         name="💡 Gợi ý:",
            #         value="• Dùng `;cauca` để câu cá trả phí (cooldown 5 phút)\n• Mua cần câu tốt hơn để tăng tỷ lệ cá hiếm!",
            #         inline=False
            #     )
            #     await ctx.reply(embed=embed, mention_author=True)
            #     return
            
            # Tạo embed câu cá
            fishing_embed = discord.Embed(
                title="🎣 Câu Cá Miễn Phí",
                description=f"🌊 **{ctx.author.display_name}** đang câu cá với cần câu cơ bản...",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            rod_info = self.FISHING_RODS["basic"]
            fishing_embed.add_field(
                name="🎣 Cần câu:",
                value=f"{rod_info['name']}\n*{rod_info['description']}*",
                inline=False
            )
            fishing_embed.add_field(
                name="⚡ Trạng thái:",
                value="Đang chờ cá cắn câu... 🐟",
                inline=False
            )
            fishing_embed.set_footer(text="Câu cá miễn phí - Cần câu cơ bản")
            
            message = await ctx.reply(embed=fishing_embed, mention_author=True)
            
            # Bỏ delay để câu cá nhanh hơn
            # import asyncio
            # await asyncio.sleep(3)
            
            # Random cá với cần câu cơ bản (100% cá thường)
            fish_emoji = self.get_random_fish(user_data['fishing_level'], "basic")
            fish_info = self.FISH_TYPES[fish_emoji]
            
            # Cập nhật inventory
            if fish_emoji not in user_data['fish_inventory']:
                user_data['fish_inventory'][fish_emoji] = 0
            user_data['fish_inventory'][fish_emoji] += 1
            
            # Cập nhật thống kê
            user_data['total_fished'] += 1
            user_data['last_free_fishing_time'] = current_time
            
            # Thêm EXP
            leveled_up = self.add_fishing_exp(user_data, fish_info['rarity'])
            
            # Lưu dữ liệu
            self.save_fishing_data()
            
            # Tạo embed kết quả
            rarity_colors = {
                "trash": discord.Color.grey(),
                "common": discord.Color.green(),
                "rare": discord.Color.blue(),
                "epic": discord.Color.purple(),
                "legendary": discord.Color.gold()
            }
            
            result_embed = discord.Embed(
                title="🎣 Kết Quả Câu Cá Miễn Phí",
                description=f"🎉 **{ctx.author.display_name}** đã câu được:",
                color=rarity_colors.get(fish_info['rarity'], discord.Color.blue()),
                timestamp=datetime.now()
            )
            
            result_embed.add_field(
                name="🐟 Cá câu được:",
                value=f"{fish_emoji} **{fish_info['name']}**\n💰 Giá trị: {fish_info['price']:,} xu",
                inline=True
            )
            
            result_embed.add_field(
                name="⭐ Độ hiếm:",
                value=f"**{fish_info['rarity'].title()}**",
                inline=True
            )
            
            result_embed.add_field(
                name="📊 Thống kê:",
                value=f"🎣 Tổng câu: {user_data['total_fished']}\n🏆 Level: {user_data['fishing_level']}",
                inline=True
            )
            
            if leveled_up:
                result_embed.add_field(
                    name="🎊 Level Up!",
                    value=f"Chúc mừng! Bạn đã lên **Level {user_data['fishing_level']}**!",
                    inline=False
                )
            
            result_embed.set_footer(text="🆓 Câu cá miễn phí - Không cooldown - Cần câu cơ bản")
            
            await message.edit(embed=result_embed)
        
        @self.bot.command(name='sell', aliases=['bancar', 'sellfish'])
        async def sell_fish_command(ctx, fish_type=None, amount=None):
            """Lệnh bán cá"""
            user_id = ctx.author.id
            user_data = self.get_user_fishing_data(user_id)
            
            # Nếu không có tham số, hiển thị hướng dẫn
            if not fish_type:
                embed = discord.Embed(
                    title="🏪 Hướng Dẫn Bán Cá",
                    description="Cách sử dụng lệnh bán cá:",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="📝 Cú pháp:",
                    value=(
                        "`;sell <loại_cá> [số_lượng]`\n"
                        "`;sell all` - Bán tất cả cá\n"
                        "`;sell 🐟 5` - Bán 5 con cá nhỏ\n"
                        "`;sell 🦈` - Bán 1 con cá mập"
                    ),
                    inline=False
                )
                
                # Hiển thị kho cá hiện tại
                if user_data['fish_inventory']:
                    inventory_text = ""
                    total_value = 0
                    
                    for fish_emoji, count in user_data['fish_inventory'].items():
                        if count > 0:
                            fish_info = self.FISH_TYPES[fish_emoji]
                            value = fish_info['price'] * count
                            total_value += value
                            inventory_text += f"{fish_emoji} **{fish_info['name']}**: {count} con ({fish_info['price']:,} xu/con)\n"
                    
                    embed.add_field(
                        name="🎒 Kho cá của bạn:",
                        value=inventory_text or "Trống",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="💰 Tổng giá trị:",
                        value=f"{total_value:,} xu",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="🎒 Kho cá:",
                        value="Bạn chưa có cá nào! Dùng `;cauca` để câu cá.",
                        inline=False
                    )
                
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Xử lý bán tất cả
            if fish_type.lower() == "all":
                if not user_data['fish_inventory'] or all(count == 0 for count in user_data['fish_inventory'].values()):
                    await ctx.reply("❌ Bạn không có cá nào để bán!", mention_author=True)
                    return
                
                total_earned = 0
                sold_fish = []
                
                for fish_emoji, count in user_data['fish_inventory'].items():
                    if count > 0:
                        fish_info = self.FISH_TYPES[fish_emoji]
                        earned = fish_info['price'] * count
                        total_earned += earned
                        sold_fish.append(f"{fish_emoji} {fish_info['name']}: {count} con = {earned:,} xu")
                        user_data['fish_inventory'][fish_emoji] = 0
                
                # Thêm tiền vào ví
                if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
                    self.bot_instance.shared_wallet.add_balance(user_id, total_earned)
                
                # Cập nhật thống kê
                user_data['total_sold'] += sum(user_data['fish_inventory'].values())
                user_data['total_earned'] += total_earned
                
                self.save_fishing_data()
                
                embed = discord.Embed(
                    title="💰 Bán Cá Thành Công!",
                    description=f"{ctx.author.mention} đã bán tất cả cá!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🐟 Cá đã bán:",
                    value="\n".join(sold_fish),
                    inline=False
                )
                
                embed.add_field(
                    name="💵 Tổng thu nhập:",
                    value=f"**+{total_earned:,} xu**",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Thống kê tổng:",
                    value=f"Đã bán: {user_data['total_sold']} con\nTổng kiếm: {user_data['total_earned']:,} xu",
                    inline=True
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Xử lý bán cá cụ thể
            # Tìm fish emoji từ input
            target_fish = None
            for fish_emoji in self.FISH_TYPES.keys():
                if fish_type == fish_emoji or fish_type.lower() in self.FISH_TYPES[fish_emoji]['name'].lower():
                    target_fish = fish_emoji
                    break
            
            if not target_fish:
                await ctx.reply(
                    f"❌ Không tìm thấy loại cá '{fish_type}'!\n"
                    "💡 Dùng `;sell` để xem danh sách cá có thể bán.",
                    mention_author=True
                )
                return
            
            # Kiểm tra có cá trong kho không
            current_count = user_data['fish_inventory'].get(target_fish, 0)
            if current_count == 0:
                fish_info = self.FISH_TYPES[target_fish]
                await ctx.reply(
                    f"❌ Bạn không có {target_fish} **{fish_info['name']}** nào để bán!",
                    mention_author=True
                )
                return
            
            # Xử lý số lượng bán
            try:
                sell_amount = int(amount) if amount else 1
                if sell_amount <= 0:
                    await ctx.reply("❌ Số lượng phải lớn hơn 0!", mention_author=True)
                    return
                if sell_amount > current_count:
                    sell_amount = current_count
            except ValueError:
                await ctx.reply("❌ Số lượng không hợp lệ!", mention_author=True)
                return
            
            # Thực hiện bán cá
            fish_info = self.FISH_TYPES[target_fish]
            total_earned = fish_info['price'] * sell_amount
            
            # Cập nhật inventory
            user_data['fish_inventory'][target_fish] -= sell_amount
            
            # Thêm tiền vào ví
            if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
                self.bot_instance.shared_wallet.add_balance(user_id, total_earned)
            
            # Cập nhật thống kê
            user_data['total_sold'] += sell_amount
            user_data['total_earned'] += total_earned
            
            self.save_fishing_data()
            
            # Thông báo thành công
            embed = discord.Embed(
                title="💰 Bán Cá Thành Công!",
                description=f"{ctx.author.mention} đã bán cá!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🐟 Cá đã bán:",
                value=f"{target_fish} **{fish_info['name']}** x{sell_amount}",
                inline=True
            )
            
            embed.add_field(
                name="💵 Thu nhập:",
                value=f"**+{total_earned:,} xu**",
                inline=True
            )
            
            remaining = user_data['fish_inventory'][target_fish]
            embed.add_field(
                name="🎒 Còn lại:",
                value=f"{remaining} con",
                inline=True
            )
            
            embed.add_field(
                name="📊 Thống kê tổng:",
                value=f"Đã bán: {user_data['total_sold']} con\nTổng kiếm: {user_data['total_earned']:,} xu",
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='rodshop', aliases=['shopcan', 'cancau', 'buyrod'])
        async def rod_shop_command(ctx, action=None, rod_type=None):
            """Shop cần câu - mua cần câu tốt hơn"""
            user_id = ctx.author.id
            user_data = self.get_user_fishing_data(user_id)
            
            if not action:
                # Hiển thị shop cần câu
                embed = discord.Embed(
                    title="🏪 Shop Cần Câu",
                    description="Mua cần câu tốt hơn để tăng tỷ lệ cá hiếm!",
                    color=discord.Color.gold()
                )
                
                current_rod = user_data.get('current_rod', 'basic')
                current_rod_info = self.FISHING_RODS[current_rod]
                embed.add_field(
                    name="🎣 Cần câu hiện tại:",
                    value=f"{current_rod_info['name']}\n*{current_rod_info['description']}*",
                    inline=False
                )
                
                shop_text = ""
                for rod_id, rod_info in self.FISHING_RODS.items():
                    owned = rod_id in user_data.get('owned_rods', ['basic'])
                    status = "✅ Đã sở hữu" if owned else f"💰 {rod_info['price']:,} xu"
                    
                    shop_text += f"{rod_info['name']}\n"
                    shop_text += f"*{rod_info['description']}*\n"
                    shop_text += f"**{status}**\n\n"
                
                embed.add_field(
                    name="🛒 Danh sách cần câu:",
                    value=shop_text,
                    inline=False
                )
                
                embed.add_field(
                    name="📝 Hướng dẫn:",
                    value="• `;rodshop buy <loại>` - Mua cần câu\n• `;rodshop equip <loại>` - Trang bị cần câu\n• `;rodshop list` - Xem cần câu đã mua",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if action.lower() == "buy":
                if not rod_type:
                    await ctx.reply("❌ Vui lòng chọn loại cần câu! Ví dụ: `;rodshop buy iron`", mention_author=True)
                    return
                
                rod_type = rod_type.lower()
                if rod_type not in self.FISHING_RODS:
                    await ctx.reply("❌ Loại cần câu không tồn tại! Dùng `;rodshop` để xem danh sách.", mention_author=True)
                    return
                
                rod_info = self.FISHING_RODS[rod_type]
                
                # Kiểm tra đã sở hữu chưa
                if rod_type in user_data.get('owned_rods', ['basic']):
                    await ctx.reply(f"❌ Bạn đã sở hữu {rod_info['name']} rồi!", mention_author=True)
                    return
                
                # Kiểm tra tiền
                if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
                    current_balance = self.bot_instance.shared_wallet.get_balance(user_id)
                    if current_balance < rod_info['price']:
                        await ctx.reply(
                            f"❌ Không đủ tiền! Bạn cần {rod_info['price']:,} xu nhưng chỉ có {current_balance:,} xu.",
                            mention_author=True
                        )
                        return
                    
                    # Trừ tiền và thêm cần câu
                    self.bot_instance.shared_wallet.subtract_balance(user_id, rod_info['price'])
                    if 'owned_rods' not in user_data:
                        user_data['owned_rods'] = ['basic']
                    user_data['owned_rods'].append(rod_type)
                    self.save_fishing_data()
                    
                    embed = discord.Embed(
                        title="🎉 Mua Cần Câu Thành Công!",
                        description=f"Bạn đã mua {rod_info['name']}!",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="💰 Chi phí:",
                        value=f"{rod_info['price']:,} xu",
                        inline=True
                    )
                    embed.add_field(
                        name="💳 Số dư còn lại:",
                        value=f"{current_balance - rod_info['price']:,} xu",
                        inline=True
                    )
                    embed.add_field(
                        name="🎣 Hiệu quả:",
                        value=rod_info['description'],
                        inline=False
                    )
                    embed.add_field(
                        name="💡 Lưu ý:",
                        value=f"Dùng `;rodshop equip {rod_type}` để trang bị cần câu mới!",
                        inline=False
                    )
                    
                    await ctx.reply(embed=embed, mention_author=True)
                else:
                    await ctx.reply("❌ Hệ thống ví không khả dụng!", mention_author=True)
            
            elif action.lower() == "equip":
                if not rod_type:
                    await ctx.reply("❌ Vui lòng chọn loại cần câu! Ví dụ: `;rodshop equip iron`", mention_author=True)
                    return
                
                rod_type = rod_type.lower()
                if rod_type not in self.FISHING_RODS:
                    await ctx.reply("❌ Loại cần câu không tồn tại!", mention_author=True)
                    return
                
                # Kiểm tra đã sở hữu chưa
                if rod_type not in user_data.get('owned_rods', ['basic']):
                    rod_info = self.FISHING_RODS[rod_type]
                    await ctx.reply(f"❌ Bạn chưa sở hữu {rod_info['name']}! Dùng `;rodshop buy {rod_type}` để mua.", mention_author=True)
                    return
                
                # Trang bị cần câu
                user_data['current_rod'] = rod_type
                self.save_fishing_data()
                
                rod_info = self.FISHING_RODS[rod_type]
                embed = discord.Embed(
                    title="🎣 Trang Bị Cần Câu Thành Công!",
                    description=f"Bạn đã trang bị {rod_info['name']}!",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="🎯 Hiệu quả:",
                    value=rod_info['description'],
                    inline=False
                )
                embed.add_field(
                    name="💡 Lưu ý:",
                    value="Cần câu mới sẽ có hiệu lực từ lần câu cá tiếp theo!",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
            
            elif action.lower() == "list":
                # Hiển thị danh sách cần câu đã mua
                owned_rods = user_data.get('owned_rods', ['basic'])
                current_rod = user_data.get('current_rod', 'basic')
                
                embed = discord.Embed(
                    title="🎒 Cần Câu Đã Sở Hữu",
                    description="Danh sách cần câu bạn đã mua:",
                    color=discord.Color.blue()
                )
                
                for rod_id in owned_rods:
                    rod_info = self.FISHING_RODS[rod_id]
                    status = "🎣 **Đang sử dụng**" if rod_id == current_rod else "📦 Trong kho"
                    
                    embed.add_field(
                        name=f"{rod_info['name']} {status}",
                        value=rod_info['description'],
                        inline=False
                    )
                
                embed.add_field(
                    name="💡 Lưu ý:",
                    value="Dùng `;rodshop equip <loại>` để đổi cần câu!",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
            
            else:
                await ctx.reply("❌ Hành động không hợp lệ! Dùng `;rodshop` để xem hướng dẫn.", mention_author=True)
        
        @self.bot.command(name='kho', aliases=['inventory', 'fish_inventory', 'khocar'])
        async def inventory_command(ctx, target_user: discord.Member = None):
            """Xem kho cá của bản thân hoặc người khác"""
            target = target_user or ctx.author
            user_data = self.get_user_fishing_data(target.id)
            
            embed = discord.Embed(
                title=f"🎒 Kho Cá - {target.display_name}",
                color=discord.Color.blue()
            )
            
            if not user_data['fish_inventory'] or all(count == 0 for count in user_data['fish_inventory'].values()):
                embed.description = "Kho cá trống! Dùng `;cauca` để câu cá."
            else:
                inventory_text = ""
                total_value = 0
                total_fish = 0
                
                # Sắp xếp theo độ hiếm và giá trị
                sorted_fish = sorted(
                    user_data['fish_inventory'].items(),
                    key=lambda x: (
                        {"legendary": 5, "epic": 4, "rare": 3, "common": 2, "trash": 1}[self.FISH_TYPES[x[0]]['rarity']],
                        self.FISH_TYPES[x[0]]['price']
                    ),
                    reverse=True
                )
                
                for fish_emoji, count in sorted_fish:
                    if count > 0:
                        fish_info = self.FISH_TYPES[fish_emoji]
                        value = fish_info['price'] * count
                        total_value += value
                        total_fish += count
                        
                        rarity_icon = {
                            "trash": "⚪", 
                            "common": "🟢", 
                            "rare": "🔵", 
                            "epic": "🟣",
                            "legendary": "🟡"
                        }[fish_info['rarity']]
                        inventory_text += f"{rarity_icon} {fish_emoji} **{fish_info['name']}**: {count} con ({fish_info['price']:,} xu/con)\n"
                
                embed.add_field(
                    name="🐟 Danh sách cá:",
                    value=inventory_text,
                    inline=False
                )
                
                embed.add_field(
                    name="📊 Thống kê:",
                    value=f"Tổng cá: **{total_fish}** con\nGiá trị: **{total_value:,}** xu",
                    inline=True
                )
            
            # Thông tin level và thống kê
            embed.add_field(
                name="🎯 Thông tin câu cá:",
                value=(
                    f"Level: **{user_data['fishing_level']}**\n"
                    f"EXP: **{user_data['fishing_exp']}/100**\n"
                    f"Đã câu: **{user_data['total_fished']}** con\n"
                    f"Đã bán: **{user_data['total_sold']}** con\n"
                    f"Tổng kiếm: **{user_data['total_earned']:,}** xu"
                ),
                inline=True
            )
            
            embed.add_field(
                name="💡 Lệnh hữu ích:",
                value="`;cauca` - Câu cá\n`;sell` - Bán cá\n`;sell all` - Bán tất cả",
                inline=False
            )
            
            embed.set_footer(text=f"Cooldown câu cá: 5 phút • Chi phí: {self.FISHING_COST:,} xu/lần")
            
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='topfish', aliases=['bangxephangca', 'fishleaderboard'])
        async def fishing_leaderboard_command(ctx):
            """Bảng xếp hạng câu cá"""
            if not self.fishing_data:
                await ctx.reply("❌ Chưa có ai câu cá!", mention_author=True)
                return
            
            # Sắp xếp theo tổng cá đã câu
            sorted_users = sorted(
                self.fishing_data.items(),
                key=lambda x: x[1].get('total_fished', 0),
                reverse=True
            )[:10]  # Top 10
            
            embed = discord.Embed(
                title="🏆 Bảng Xếp Hạng Câu Cá",
                description="Top 10 cao thủ câu cá:",
                color=discord.Color.gold()
            )
            
            leaderboard_text = ""
            for i, (user_id_str, data) in enumerate(sorted_users, 1):
                try:
                    user = self.bot.get_user(int(user_id_str))
                    name = user.display_name if user else f"User {user_id_str}"
                    
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    
                    leaderboard_text += (
                        f"{medal} **{name}**\n"
                        f"   🐟 Đã câu: {data.get('total_fished', 0)} con\n"
                        f"   🎯 Level: {data.get('fishing_level', 1)}\n"
                        f"   💰 Đã kiếm: {data.get('total_earned', 0):,} xu\n\n"
                    )
                except:
                    continue
            
            embed.add_field(
                name="🎣 Bảng xếp hạng:",
                value=leaderboard_text or "Không có dữ liệu",
                inline=False
            )
            
            embed.set_footer(text="Dùng ;cauca để tham gia câu cá!")
            
            await ctx.reply(embed=embed, mention_author=True)
