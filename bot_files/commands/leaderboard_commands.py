"""
Leaderboard Commands - Hệ thống bảng xếp hạng và cuộc thi cho Discord bot
Lệnh: ;weeklytop, ;leaderboard, ;competition
"""
import discord
from discord.ext import commands
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from utils.shared_wallet import shared_wallet

logger = logging.getLogger(__name__)

class LeaderboardCommands:
    def __init__(self, bot_instance):
        """
        Khởi tạo Leaderboard Commands
        
        Args:
            bot_instance: Instance của AutoReplyBotRefactored
        """
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.weekly_data_file = 'data/weekly_leaderboard.json'
        self.weekly_data = self.load_weekly_data()
        
        logger.info("Leaderboard Commands đã được khởi tạo")
    
    def load_weekly_data(self) -> Dict:
        """Load weekly leaderboard data"""
        try:
            if os.path.exists(self.weekly_data_file):
                with open(self.weekly_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi khi load weekly data: {e}")
            return {}
    
    def save_weekly_data(self) -> None:
        """Save weekly leaderboard data"""
        try:
            os.makedirs(os.path.dirname(self.weekly_data_file), exist_ok=True)
            with open(self.weekly_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.weekly_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save weekly data: {e}")
    
    def get_current_week(self) -> str:
        """Lấy tuần hiện tại (format: YYYY-WW)"""
        now = datetime.now()
        year, week, _ = now.isocalendar()
        return f"{year}-{week:02d}"
    
    def add_weekly_win(self, user_id: int, game_type: str) -> None:
        """Thêm 1 ván thắng vào weekly leaderboard"""
        week = self.get_current_week()
        user_str = str(user_id)
        
        if week not in self.weekly_data:
            self.weekly_data[week] = {}
        
        if user_str not in self.weekly_data[week]:
            self.weekly_data[week][user_str] = {
                'total_wins': 0,
                'taixiu_wins': 0,
                'rps_wins': 0,
                'slot_wins': 0,
                'flip_wins': 0,
                'blackjack_wins': 0
            }
        
        self.weekly_data[week][user_str]['total_wins'] += 1
        self.weekly_data[week][user_str][f'{game_type}_wins'] += 1
        self.save_weekly_data()
    
    def get_weekly_leaderboard(self, limit: int = 10) -> list:
        """Lấy bảng xếp hạng tuần hiện tại"""
        week = self.get_current_week()
        
        if week not in self.weekly_data:
            return []
        
        # Sắp xếp theo total_wins
        sorted_users = sorted(
            self.weekly_data[week].items(),
            key=lambda x: x[1]['total_wins'],
            reverse=True
        )
        
        return sorted_users[:limit]
    
    def reset_weekly_leaderboard(self) -> dict:
        """Reset bảng xếp hạng tuần và trao thưởng cho top players"""
        week = self.get_current_week()
        
        if week not in self.weekly_data:
            return {"message": "Không có dữ liệu tuần này để reset"}
        
        # Lấy top 3 players
        leaderboard = self.get_weekly_leaderboard(10)  # Lấy nhiều để có lịch sử
        rewards_given = []
        
        for i, (user_id, data) in enumerate(leaderboard):
            try:
                user_id_int = int(user_id)
                wins = data['total_wins']
                
                if i == 0:  # Top 1
                    # Trao 2k EXP
                    reward_exp = 2000
                    # Shop system đã bị xóa - chỉ log thông tin
                    logger.info(f"Weekly Top 1: User {user_id_int} với {wins} wins - Sẽ trao {reward_exp} EXP Rare (Shop system đã xóa)")
                    
                    rewards_given.append({
                        'user_id': user_id_int,
                        'rank': 1,
                        'wins': wins,
                        'reward': reward_exp
                    })
                    
                elif i == 1:  # Top 2
                    # Trao 1k EXP
                    reward_exp = 1000
                    # Shop system đã bị xóa - chỉ log thông tin
                    logger.info(f"Weekly Top 2: User {user_id_int} với {wins} wins - Sẽ trao {reward_exp} EXP Rare (Shop system đã xóa)")
                    
                    rewards_given.append({
                        'user_id': user_id_int,
                        'rank': 2,
                        'wins': wins,
                        'reward': reward_exp
                    })
                    
                elif i == 2:  # Top 3
                    # Trao 500 EXP
                    reward_exp = 500
                    # Shop system đã bị xóa - chỉ log thông tin
                    logger.info(f"Weekly Top 3: User {user_id_int} với {wins} wins - Sẽ trao {reward_exp} EXP Rare (Shop system đã xóa)")
                    
                    rewards_given.append({
                        'user_id': user_id_int,
                        'rank': 3,
                        'wins': wins,
                        'reward': reward_exp
                    })
                    
            except Exception as e:
                logger.error(f"Lỗi khi trao thưởng cho user {user_id}: {e}")
        
        # Lưu lịch sử tuần vừa kết thúc
        if 'history' not in self.weekly_data:
            self.weekly_data['history'] = {}
        
        self.weekly_data['history'][week] = {
            'leaderboard': leaderboard,
            'rewards': rewards_given,
            'end_date': datetime.now().isoformat()
        }
        
        # Xóa dữ liệu tuần hiện tại để bắt đầu tuần mới
        if week in self.weekly_data:
            del self.weekly_data[week]
        
        self.save_weekly_data()
        
        return {
            'week': week,
            'rewards_given': rewards_given,
            'total_participants': len(leaderboard)
        }
    
    def get_last_week_winners(self) -> dict:
        """Lấy thông tin người thắng tuần trước"""
        if 'history' not in self.weekly_data:
            return None
        
        # Lấy tuần gần nhất trong history
        if not self.weekly_data['history']:
            return None
        
        last_week = max(self.weekly_data['history'].keys())
        return self.weekly_data['history'][last_week]
    
    def register_commands(self):
        """Register leaderboard commands"""
        
        @self.bot.command(name='weeklytop', aliases=['topweek', 'bangdua'])
        async def weekly_top_command(ctx):
            """
            Hiển thị bảng đua top hàng tuần
            
            Usage: ;weeklytop
            """
            try:
                # Tạo embed bảng đua
                embed = discord.Embed(
                    title="🏆 BẢNG ĐUA TOP HÀNG TUẦN",
                    description="Cuộc thi thống kê game hàng tuần với phần thưởng hấp dẫn!",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                # Thông tin cuộc thi
                embed.add_field(
                    name="📅 Thời gian:",
                    value=(
                        "• **Bắt đầu:** Thứ 2 hàng tuần (00:00)\n"
                        "• **Kết thúc:** Chủ nhật hàng tuần (23:59)\n"
                        "• **Trao thưởng:** Thứ 2 tuần sau"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🎯 Tiêu chí xếp hạng:",
                    value=(
                        "• **Tổng số ván thắng** trong tuần\n"
                        "• **Tất cả game:** Tài Xỉu, RPS, Slot, Flip, Blackjack\n"
                        "• **Chỉ tính ván thắng** (không tính hòa hoặc thua)\n"
                        "• **Reset mỗi tuần** - Cơ hội công bằng cho tất cả"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🏅 Phần thưởng:",
                    value=(
                        "🥇 **TOP 1:** 2,000 EXP Rare\n"
                        "🥈 **TOP 2:** 1,000 EXP Rare\n"
                        "🥉 **TOP 3:** 500 EXP Rare\n"
                        "🏅 **TOP 4 trở xuống:** Không có phần thưởng"
                    ),
                    inline=False
                )
                
                # Lấy bảng xếp hạng thực tế
                leaderboard = self.get_weekly_leaderboard(10)
                
                if leaderboard:
                    leaderboard_text = ""
                    medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
                    
                    for i, (user_id, data) in enumerate(leaderboard):
                        try:
                            user = self.bot.get_user(int(user_id))
                            username = user.display_name if user else f"User {user_id}"
                            wins = data['total_wins']
                            
                            leaderboard_text += f"{medals[i]} **{username}** - {wins} ván thắng\n"
                        except:
                            continue
                    
                    embed.add_field(
                        name="📊 BXH hiện tại:",
                        value=leaderboard_text if leaderboard_text else "Chưa có dữ liệu tuần này",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="📊 BXH hiện tại:",
                        value="Chưa có ai tham gia tuần này. Hãy chơi game để lên bảng xếp hạng!",
                        inline=False
                    )
                
                embed.add_field(
                    name="📈 Cách tham gia:",
                    value=(
                        "• **Chơi game** bất kỳ: `;taixiu`, `;rps`, `;slot`, `;flip`, `;blackjack`\n"
                        "• **Thắng ván** để tích lũy điểm\n"
                        "• **Kiểm tra thứ hạng** bằng `;myleaderboard`\n"
                        "• **Nhận thưởng** tự động vào thứ 2"
                    ),
                    inline=False
                )
                
                # Thông tin tuần hiện tại
                current_week = self.get_current_week()
                now = datetime.now()
                # Tính ngày thứ 2 tuần này
                monday = now - timedelta(days=now.weekday())
                sunday = monday + timedelta(days=6)
                
                embed.add_field(
                    name="⚡ Thông tin tuần này:",
                    value=(
                        f"• **Tuần:** {current_week}\n"
                        f"• **Từ:** {monday.strftime('%d/%m')} - {sunday.strftime('%d/%m/%Y')}\n"
                        f"• **Tổng người tham gia:** {len(leaderboard)} người\n"
                        f"• **Tổng ván thắng:** {sum(data['total_wins'] for _, data in leaderboard)} ván"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 Game được tính:",
                    value=(
                        "🎲 **Tài Xỉu** - Đoán tài/xỉu\n"
                        "✂️ **RPS** - Kéo búa bao\n"
                        "🎰 **Slot** - Máy đánh bạc\n"
                        "🪙 **Flip** - Tung xu\n"
                        "🃏 **Blackjack** - Bài 21"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Thành tích:",
                    value=(
                        "👑 **Vua tuần trước:** Chưa có\n"
                        "🔥 **Kỷ lục:** Chưa có\n"
                        "⭐ **Streak cao nhất:** Chưa có\n"
                        "💎 **EXP đã trao:** 0 EXP"
                    ),
                    inline=True
                )
                
                embed.set_footer(
                    text="Cập nhật real-time • Chúc may mắn! 🍀",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong weekly top command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi hiển thị bảng đua. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='myleaderboard', aliases=['myrank', 'hangtoi'])
        async def my_leaderboard_command(ctx):
            """
            Xem thứ hạng cá nhân trong tuần
            
            Usage: ;myleaderboard
            """
            try:
                week = self.get_current_week()
                user_str = str(ctx.author.id)
                
                if week not in self.weekly_data or user_str not in self.weekly_data[week]:
                    embed = discord.Embed(
                        title="📊 Thứ hạng của bạn",
                        description="Bạn chưa tham gia cuộc thi tuần này!",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="💡 Cách tham gia:",
                        value="Chơi bất kỳ game nào và thắng để lên bảng xếp hạng!",
                        inline=False
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Lấy dữ liệu user
                user_data = self.weekly_data[week][user_str]
                
                # Tìm thứ hạng
                leaderboard = self.get_weekly_leaderboard(100)  # Lấy nhiều để tìm thứ hạng
                rank = None
                for i, (uid, _) in enumerate(leaderboard):
                    if uid == user_str:
                        rank = i + 1
                        break
                
                embed = discord.Embed(
                    title="📊 Thứ hạng của bạn",
                    description=f"Thống kê tuần {week}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🏅 Thứ hạng:",
                    value=f"**#{rank}** / {len(leaderboard)} người" if rank else "Chưa xác định",
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Tổng thắng:",
                    value=f"**{user_data['total_wins']}** ván",
                    inline=True
                )
                
                embed.add_field(
                    name="🎮 Chi tiết:",
                    value=(
                        f"🎲 Tài Xỉu: {user_data.get('taixiu_wins', 0)}\n"
                        f"✂️ RPS: {user_data.get('rps_wins', 0)}\n"
                        f"🎰 Slot: {user_data.get('slot_wins', 0)}\n"
                        f"🪙 Flip: {user_data.get('flip_wins', 0)}\n"
                        f"🃏 Blackjack: {user_data.get('blackjack_wins', 0)}"
                    ),
                    inline=False
                )
                
                # Phần thưởng dự kiến
                reward_text = "🏅 Không có phần thưởng"
                if rank:
                    if rank == 1:
                        reward_text = "🥇 2,000 EXP Rare"
                    elif rank == 2:
                        reward_text = "🥈 1,000 EXP Rare"
                    elif rank == 3:
                        reward_text = "🥉 500 EXP Rare"
                    else:
                        reward_text = "🏅 Không có phần thưởng"
                
                embed.add_field(
                    name="🎁 Phần thưởng dự kiến:",
                    value=reward_text,
                    inline=False
                )
                
                embed.set_author(
                    name=ctx.author.display_name,
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                
                embed.set_footer(text="Chơi thêm để cải thiện thứ hạng!")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong my leaderboard command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi xem thứ hạng. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='weeklyhistory', aliases=['lichsutop', 'tophistory'])
        async def weekly_history_command(ctx):
            """
            Xem lịch sử các tuần trước
            
            Usage: ;weeklyhistory
            """
            try:
                if 'history' not in self.weekly_data or not self.weekly_data['history']:
                    embed = discord.Embed(
                        title="📚 Lịch sử bảng đua",
                        description="Chưa có lịch sử tuần nào!",
                        color=discord.Color.blue()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                embed = discord.Embed(
                    title="📚 LỊCH SỬ BẢNG ĐUA HÀNG TUẦN",
                    description="Các nhà vô địch tuần trước",
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                
                # Lấy 5 tuần gần nhất
                recent_weeks = sorted(self.weekly_data['history'].keys(), reverse=True)[:5]
                
                for week in recent_weeks:
                    history = self.weekly_data['history'][week]
                    rewards = history.get('rewards', [])
                    
                    if rewards:
                        winners_text = ""
                        for reward in rewards:
                            try:
                                user = self.bot.get_user(reward['user_id'])
                                username = user.display_name if user else f"User {reward['user_id']}"
                                if reward['rank'] == 1:
                                    rank_emoji = "🥇"
                                elif reward['rank'] == 2:
                                    rank_emoji = "🥈"
                                elif reward['rank'] == 3:
                                    rank_emoji = "🥉"
                                else:
                                    rank_emoji = "🏅"
                                winners_text += f"{rank_emoji} **{username}** - {reward['wins']} wins → {reward['reward']:,} EXP\n"
                            except:
                                continue
                        
                        embed.add_field(
                            name=f"📅 Tuần {week}",
                            value=winners_text if winners_text else "Không có người thắng",
                            inline=False
                        )
                
                embed.set_footer(text="Top 5 tuần gần nhất")
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong weekly history command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi xem lịch sử. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='resetweekly', aliases=['resetbangdua'])
        async def reset_weekly_command(ctx):
            """
            Reset bảng đua tuần và trao thưởng (Admin only)
            
            Usage: ;resetweekly
            """
            try:
                # Kiểm tra quyền admin
                if not self.bot_instance.is_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Admin mới có thể reset bảng đua tuần!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Thực hiện reset
                result = self.reset_weekly_leaderboard()
                
                if "message" in result:
                    embed = discord.Embed(
                        title="ℹ️ Thông báo",
                        description=result["message"],
                        color=discord.Color.blue()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Tạo embed thông báo kết quả
                embed = discord.Embed(
                    title="🏆 RESET BẢNG ĐUA TUẦN THÀNH CÔNG",
                    description=f"Đã reset tuần {result['week']} và trao thưởng!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                if result['rewards_given']:
                    rewards_text = ""
                    for reward in result['rewards_given']:
                        try:
                            user = self.bot.get_user(reward['user_id'])
                            username = user.display_name if user else f"User {reward['user_id']}"
                            if reward['rank'] == 1:
                                rank_emoji = "🥇"
                            elif reward['rank'] == 2:
                                rank_emoji = "🥈"
                            elif reward['rank'] == 3:
                                rank_emoji = "🥉"
                            else:
                                rank_emoji = "🏅"
                            rewards_text += f"{rank_emoji} **{username}** - {reward['wins']} wins → **{reward['reward']:,} EXP**\n"
                        except:
                            continue
                    
                    embed.add_field(
                        name="🎁 Phần thưởng đã trao:",
                        value=rewards_text,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🎁 Phần thưởng đã trao:",
                        value="Không có ai đủ điều kiện nhận thưởng tuần này",
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Thống kê:",
                    value=f"• **Tổng người tham gia:** {result['total_participants']}\n• **Tuần mới bắt đầu:** {self.get_current_week()}",
                    inline=False
                )
                
                embed.set_footer(text="Bảng đua tuần mới đã bắt đầu!")
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong reset weekly command: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Có lỗi xảy ra khi reset bảng đua. Vui lòng thử lại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        logger.info("Đã đăng ký Leaderboard commands: weeklytop, myleaderboard, weeklyhistory, resetweekly")
