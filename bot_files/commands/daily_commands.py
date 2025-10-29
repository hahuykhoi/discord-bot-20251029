import discord
from discord.ext import commands
from .base import BaseCommand
import logging
from utils.shared_wallet import shared_wallet
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class DailyCommands(BaseCommand):
    """Commands cho hệ thống daily rewards"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.daily_file = "daily_data.json"
        self.daily_data = self.load_daily_data()
    
    def load_daily_data(self):
        """Load dữ liệu daily từ file"""
        try:
            if os.path.exists(self.daily_file):
                with open(self.daily_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi load daily data: {e}")
            return {}
    
    def save_daily_data(self):
        """Lưu dữ liệu daily vào file"""
        try:
            with open(self.daily_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi save daily data: {e}")
    
    def calculate_daily_reward(self, streak):
        """
        Tính toán phần thưởng daily theo streak
        
        Công thức:
        - Ngày 1: 100
        - Ngày 2: 200 (100 + 100)
        - Ngày 3-9: +50 mỗi ngày (250, 300, 350, 400, 450, 500, 550)
        - Ngày 10, 20, 30, ...: Bonus +500
        """
        if streak == 1:
            return 100
        elif streak == 2:
            return 200
        else:
            # Base reward: 200 + (streak - 2) * 50
            base = 200 + (streak - 2) * 50
            
            # Bonus cho các mốc 10, 20, 30, ...
            if streak % 10 == 0:
                return base + 500
            
            return base
    
    def get_next_milestone(self, streak):
        """Lấy mốc tiếp theo"""
        if streak == 0:
            return 1
        next_ten = ((streak // 10) + 1) * 10
        return next_ten
    
    def register_commands(self):
        """Đăng ký các lệnh daily"""
        
        @self.bot.command(name='daily', aliases=['d'])
        async def daily_reward(ctx):
            """
            Nhận phần thưởng hàng ngày
            
            Usage: ;daily hoặc ;d
            
            Reward:
            - Ngày 1: 100 xu
            - Ngày 2: 200 xu
            - Ngày 3+: +50 xu mỗi ngày
            - Mốc 10, 20, 30...: Bonus +500 xu
            """
            try:
                user_id = str(ctx.author.id)
                current_time = datetime.now()
                
                # Lấy dữ liệu user
                if user_id not in self.daily_data:
                    self.daily_data[user_id] = {
                        'last_claim': None,
                        'streak': 0,
                        'total_claimed': 0
                    }
                
                user_data = self.daily_data[user_id]
                
                # Kiểm tra cooldown
                if user_data['last_claim']:
                    last_claim = datetime.fromisoformat(user_data['last_claim'])
                    time_diff = current_time - last_claim
                    
                    # Phải đợi 24 giờ
                    if time_diff < timedelta(hours=24):
                        remaining = timedelta(hours=24) - time_diff
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        
                        embed = discord.Embed(
                            title="⏰ Chưa thể nhận daily!",
                            description=f"Bạn đã nhận daily reward hôm nay rồi!",
                            color=discord.Color.orange()
                        )
                        
                        embed.add_field(
                            name="⏳ Thời gian còn lại",
                            value=f"**{hours} giờ {minutes} phút**",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="📊 Streak hiện tại",
                            value=f"**{user_data['streak']} ngày liên tiếp**",
                            inline=True
                        )
                        
                        next_reward = self.calculate_daily_reward(user_data['streak'] + 1)
                        embed.add_field(
                            name="💰 Phần thưởng tiếp theo",
                            value=f"**{next_reward:,} xu**",
                            inline=True
                        )
                        
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                    
                    # Kiểm tra xem có bị break streak không (quá 48 giờ)
                    if time_diff > timedelta(hours=48):
                        user_data['streak'] = 0
                
                # Tăng streak
                user_data['streak'] += 1
                streak = user_data['streak']
                
                # Tính reward
                reward = self.calculate_daily_reward(streak)
                
                # Cộng tiền vào ví
                old_balance = shared_wallet.get_balance(ctx.author.id)
                new_balance = shared_wallet.add_balance(ctx.author.id, reward)
                
                # Cập nhật dữ liệu
                user_data['last_claim'] = current_time.isoformat()
                user_data['total_claimed'] += reward
                self.save_daily_data()
                
                # Tạo embed
                is_milestone = streak % 10 == 0
                
                embed = discord.Embed(
                    title="🎁 Daily Reward!",
                    description=f"**Bạn đã nhận {reward:,} xu!**",
                    color=discord.Color.gold() if is_milestone else discord.Color.green()
                )
                
                if is_milestone:
                    embed.description += f"\n\n🎉 **MILESTONE BONUS! Ngày {streak}!**"
                
                embed.add_field(
                    name="🔥 Streak",
                    value=f"**{streak} ngày liên tiếp**",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Số dư mới",
                    value=f"**{new_balance:,} xu**",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Tổng đã nhận",
                    value=f"**{user_data['total_claimed']:,} xu**",
                    inline=True
                )
                
                # Thông tin phần thưởng tiếp theo
                next_reward = self.calculate_daily_reward(streak + 1)
                next_milestone = self.get_next_milestone(streak)
                milestone_reward = self.calculate_daily_reward(next_milestone)
                
                embed.add_field(
                    name="🎯 Phần thưởng tiếp theo",
                    value=(
                        f"• **Ngày {streak + 1}:** {next_reward:,} xu\n"
                        f"• **Mốc {next_milestone} (bonus):** {milestone_reward:,} xu"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="⏰ Nhận lần tiếp",
                    value="**24 giờ nữa**",
                    inline=False
                )
                
                embed.set_author(
                    name=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                
                embed.set_footer(text="Nhớ nhận daily mỗi ngày để giữ streak!")
                
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"User {ctx.author.id} claimed daily: {reward} xu (streak: {streak})")
                
            except Exception as e:
                logger.error(f"Lỗi trong daily command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi nhận daily!",
                    mention_author=True
                )
        
        @self.bot.command(name='dailystats', aliases=['dstats'])
        async def daily_stats(ctx, user: discord.Member = None):
            """
            Xem thống kê daily của bản thân hoặc người khác
            
            Usage: 
            ;dailystats - Xem của bạn
            ;dailystats @user - Xem của người khác
            """
            try:
                target = user or ctx.author
                user_id = str(target.id)
                
                if user_id not in self.daily_data:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ {'Bạn' if target == ctx.author else target.display_name} chưa nhận daily lần nào!",
                        mention_author=True
                    )
                    return
                
                user_data = self.daily_data[user_id]
                
                embed = discord.Embed(
                    title=f"📊 Daily Stats - {target.display_name}",
                    color=discord.Color.blue()
                )
                
                embed.set_thumbnail(
                    url=target.avatar.url if target.avatar else None
                )
                
                embed.add_field(
                    name="🔥 Streak hiện tại",
                    value=f"**{user_data['streak']} ngày**",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Tổng đã nhận",
                    value=f"**{user_data['total_claimed']:,} xu**",
                    inline=True
                )
                
                # Tính phần thưởng gần nhất
                if user_data['streak'] > 0:
                    last_reward = self.calculate_daily_reward(user_data['streak'])
                    embed.add_field(
                        name="🎁 Phần thưởng gần nhất",
                        value=f"**{last_reward:,} xu**",
                        inline=True
                    )
                
                # Lần nhận cuối
                if user_data['last_claim']:
                    last_claim = datetime.fromisoformat(user_data['last_claim'])
                    embed.add_field(
                        name="⏰ Nhận lần cuối",
                        value=f"<t:{int(last_claim.timestamp())}:R>",
                        inline=False
                    )
                    
                    # Có thể nhận lại khi nào
                    next_claim = last_claim + timedelta(hours=24)
                    if datetime.now() >= next_claim:
                        embed.add_field(
                            name="✅ Trạng thái",
                            value="**Có thể nhận daily ngay bây giờ!**",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="⏳ Nhận tiếp theo",
                            value=f"<t:{int(next_claim.timestamp())}:R>",
                            inline=False
                        )
                
                # Thông tin phần thưởng tiếp theo
                next_streak = user_data['streak'] + 1
                next_reward = self.calculate_daily_reward(next_streak)
                next_milestone = self.get_next_milestone(user_data['streak'])
                
                embed.add_field(
                    name="🎯 Phần thưởng tiếp theo",
                    value=(
                        f"• **Ngày {next_streak}:** {next_reward:,} xu\n"
                        f"• **Mốc tiếp theo:** Ngày {next_milestone}"
                    ),
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong dailystats command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem thống kê!",
                    mention_author=True
                )
        
        @self.bot.command(name='dailyleaderboard', aliases=['dtop'])
        async def daily_leaderboard(ctx):
            """
            Xem bảng xếp hạng daily streak
            
            Usage: ;dailyleaderboard hoặc ;dtop
            """
            try:
                if not self.daily_data:
                    await ctx.reply(
                        f"{ctx.author.mention} ℹ️ Chưa có ai nhận daily!",
                        mention_author=True
                    )
                    return
                
                # Sắp xếp theo streak
                sorted_users = sorted(
                    self.daily_data.items(),
                    key=lambda x: (x[1]['streak'], x[1]['total_claimed']),
                    reverse=True
                )[:10]
                
                embed = discord.Embed(
                    title="🏆 Daily Leaderboard",
                    description="Top 10 streak dài nhất",
                    color=discord.Color.gold()
                )
                
                medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
                
                leaderboard_text = ""
                for i, (user_id, data) in enumerate(sorted_users):
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        username = user.display_name if user else f"User {user_id}"
                    except:
                        username = f"User {user_id}"
                    
                    leaderboard_text += (
                        f"{medals[i]} **{username}**\n"
                        f"🔥 Streak: {data['streak']} ngày | "
                        f"💰 Tổng: {data['total_claimed']:,} xu\n\n"
                    )
                
                embed.description = leaderboard_text
                
                # Thống kê tổng quan
                total_users = len(self.daily_data)
                total_claimed = sum(d['total_claimed'] for d in self.daily_data.values())
                
                embed.add_field(
                    name="📊 Thống kê chung",
                    value=(
                        f"• **Tổng người chơi:** {total_users}\n"
                        f"• **Tổng xu đã phát:** {total_claimed:,} xu"
                    ),
                    inline=False
                )
                
                embed.set_footer(text="Nhận daily mỗi ngày để lên top!")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong dailyleaderboard command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem bảng xếp hạng!",
                    mention_author=True
                )

        logger.info("Daily commands registered")
