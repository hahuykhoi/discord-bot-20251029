import discord
from discord.ext import commands
from .base import BaseCommand
import logging
from utils.shared_wallet import shared_wallet
from datetime import datetime

logger = logging.getLogger(__name__)

class WalletCommands(BaseCommand):
    """Commands cho quản lý ví tiền chung"""
    
    async def _show_cash_leaderboard(self, ctx):
        """Hiển thị bảng xếp hạng top 10 người giàu nhất"""
        try:
            users_with_money = shared_wallet.get_all_users_with_money()
            
            if not users_with_money:
                await ctx.reply(
                    f"{ctx.author.mention} ℹ️ Chưa có ai có tiền trong hệ thống!",
                    mention_author=True
                )
                return
            
            embed = discord.Embed(
                title="🏆 Bảng Xếp Hạng Tiền",
                description="Top 10 người giàu nhất trong hệ thống",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            top_10 = users_with_money[:10]
            
            leaderboard_text = ""
            for i, user_data in enumerate(top_10):
                try:
                    user = await self.bot.fetch_user(user_data['user_id'])
                    username = user.display_name if user else f"User {user_data['user_id']}"
                    
                    leaderboard_text += (
                        f"{medals[i]} **{username}**\n"
                        f"💰 Số dư: {user_data['balance']:,} xu\n\n"
                    )
                except:
                    leaderboard_text += (
                        f"{medals[i]} **User {user_data['user_id']}**\n"
                        f"💰 Số dư: {user_data['balance']:,} xu\n\n"
                    )
            
            embed.description = leaderboard_text if leaderboard_text else "Chưa có dữ liệu!"
            
            # Thêm thống kê tổng quan
            total_money = shared_wallet.get_total_money_in_system()
            user_count = shared_wallet.get_user_count()
            
            embed.add_field(
                name="📊 Thống kê",
                value=(
                    f"• **Tổng tiền:** {total_money:,} xu\n"
                    f"• **Tổng người chơi:** {user_count} người\n"
                    f"• **Trung bình:** {total_money // max(user_count, 1):,} xu/người"
                ),
                inline=False
            )
            
            embed.set_footer(text="Chơi các game để tăng số dư!")
            
            await ctx.reply(embed=embed, mention_author=True)
            
        except Exception as e:
            logger.error(f"Lỗi trong cash top: {e}")
            await ctx.reply(
                f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem bảng xếp hạng!",
                mention_author=True
            )
    
    def register_commands(self):
        """Đăng ký các lệnh wallet"""
        
        @self.bot.command(name='cash')
        async def check_cash(ctx, subcommand=None):
            """Xem số dư ví chung hoặc bảng xếp hạng
            
            Usage:
            - ;cash - Xem số dư của bạn
            - ;cash top - Xem top 10 người giàu nhất
            """
            try:
                # Nếu có subcommand là "top", hiển thị leaderboard
                if subcommand and subcommand.lower() == 'top':
                    await self._show_cash_leaderboard(ctx)
                    return
                balance = shared_wallet.get_balance(ctx.author.id)
                
                embed = discord.Embed(
                    title="💰 Số Dư Ví Chung",
                    description=f"**{balance:,} xu**",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                embed.set_author(
                    name=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                
                embed.add_field(
                    name="🎮 Games hỗ trợ",
                    value=(
                        "• **Tài Xỉu** (`;taixiu`)\n"
                        "• **Rock Paper Scissors** (`;rps`)\n"
                        "• **Slot Machine** (`;slot`)\n"
                        "• **Blackjack** (`;blackjack`)\n"
                        "• **Flip Coin** (`;flip`)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Thông tin",
                    value=(
                        "Ví này được sử dụng chung cho tất cả games\n"
                        "Số dư ban đầu: **1,000 xu**\n"
                        "Xem bảng xếp hạng: `;wallet top`"
                    ),
                    inline=False
                )
                
                embed.set_footer(text="Chơi có trách nhiệm!")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong cash command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem số dư!",
                    mention_author=True
                )
        
        @self.bot.command(name='resetallmoney')
        async def reset_all_money(ctx):
            """Reset tất cả tiền của mọi người (Supreme Admin only)"""
            try:
                # Kiểm tra quyền Supreme Admin
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể reset tất cả tiền!",
                        mention_author=True
                    )
                    return
                
                # Lấy thống kê trước khi reset
                users_with_money = shared_wallet.get_all_users_with_money()
                total_money_before = shared_wallet.get_total_money_in_system()
                user_count = shared_wallet.get_user_count()
                
                # Reset tất cả số dư
                reset_count = shared_wallet.reset_all_balances()
                
                embed = discord.Embed(
                    title="💸 Reset Tất Cả Tiền",
                    description="**Đã reset tất cả số dư về 0!**",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📊 Thống kê trước reset",
                    value=(
                        f"• **Tổng tiền trong hệ thống:** {total_money_before:,} xu\n"
                        f"• **Số user có tiền:** {len(users_with_money)} người\n"
                        f"• **Tổng số user:** {user_count} người"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🔄 Kết quả reset",
                    value=(
                        f"• **Số tài khoản đã reset:** {reset_count}\n"
                        f"• **Tổng tiền đã xóa:** {total_money_before:,} xu\n"
                        f"• **Trạng thái:** Hoàn thành"
                    ),
                    inline=False
                )
                
                if users_with_money:
                    top_users = users_with_money[:5]  # Top 5 user có nhiều tiền nhất
                    top_list = []
                    for i, user_data in enumerate(top_users, 1):
                        try:
                            user = self.bot.get_user(user_data['user_id'])
                            username = user.display_name if user else f"User {user_data['user_id']}"
                            top_list.append(f"{i}. {username}: {user_data['balance']:,} xu")
                        except:
                            top_list.append(f"{i}. User {user_data['user_id']}: {user_data['balance']:,} xu")
                    
                    embed.add_field(
                        name="🏆 Top 5 user bị reset nhiều tiền nhất",
                        value="\n".join(top_list),
                        inline=False
                    )
                
                embed.add_field(
                    name="⚠️ Lưu ý",
                    value=(
                        "• Tất cả user sẽ nhận 1,000 xu khi chơi game lần đầu\n"
                        "• Hành động này không thể hoàn tác\n"
                        "• Mục đích: Chống lạm phát trong hệ thống"
                    ),
                    inline=False
                )
                
                embed.set_author(
                    name=f"Reset by {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong resetallmoney command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi reset tiền!",
                    mention_author=True
                )
        
        @self.bot.command(name='moneystats')
        async def money_stats(ctx):
            """Xem thống kê tiền trong hệ thống (Admin+)"""
            try:
                # Kiểm tra quyền admin
                is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
                is_supreme = self.bot_instance.is_supreme_admin(ctx.author.id)
                
                if not (is_admin or is_supreme):
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Chỉ Admin trở lên mới có thể xem thống kê tiền!",
                        mention_author=True
                    )
                    return
                
                users_with_money = shared_wallet.get_all_users_with_money()
                total_money = shared_wallet.get_total_money_in_system()
                user_count = shared_wallet.get_user_count()
                
                embed = discord.Embed(
                    title="📊 Thống Kê Tiền Hệ Thống",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💰 Tổng quan",
                    value=(
                        f"• **Tổng tiền:** {total_money:,} xu\n"
                        f"• **User có tiền:** {len(users_with_money)}/{user_count}\n"
                        f"• **Trung bình:** {total_money // max(len(users_with_money), 1):,} xu/người"
                    ),
                    inline=False
                )
                
                if users_with_money:
                    top_users = users_with_money[:10]  # Top 10
                    top_list = []
                    for i, user_data in enumerate(top_users, 1):
                        try:
                            user = self.bot.get_user(user_data['user_id'])
                            username = user.display_name if user else f"User {user_data['user_id']}"
                            top_list.append(f"{i}. {username}: {user_data['balance']:,} xu")
                        except:
                            top_list.append(f"{i}. User {user_data['user_id']}: {user_data['balance']:,} xu")
                    
                    embed.add_field(
                        name="🏆 Top 10 Giàu Nhất",
                        value="\n".join(top_list),
                        inline=False
                    )
                
                embed.set_footer(text="Dữ liệu từ ví chung của tất cả games")
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong moneystats command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xem thống kê!",
                    mention_author=True
                )
        
        @self.bot.command(name='givemoney')
        async def give_money(ctx, user: discord.Member, amount: int):
            """Cho tiền cho user (Supreme Admin only)"""
            try:
                # Kiểm tra quyền Supreme Admin
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể cho tiền!",
                        mention_author=True
                    )
                    return
                
                if amount <= 0:
                    await ctx.reply(
                        f"{ctx.author.mention} ❌ Số tiền phải lớn hơn 0!",
                        mention_author=True
                    )
                    return
                
                old_balance = shared_wallet.get_balance(user.id)
                new_balance = shared_wallet.add_balance(user.id, amount)
                
                embed = discord.Embed(
                    title="💰 Cho Tiền",
                    description=f"**Đã cho {amount:,} xu cho {user.display_name}**",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📊 Thay đổi số dư",
                    value=(
                        f"• **Trước:** {old_balance:,} xu\n"
                        f"• **Thêm:** +{amount:,} xu\n"
                        f"• **Sau:** {new_balance:,} xu"
                    ),
                    inline=False
                )
                
                embed.set_author(
                    name=f"Cho bởi {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong givemoney command: {e}")
                await ctx.reply(
                    f"{ctx.author.mention} ❌ Có lỗi xảy ra khi cho tiền!",
                    mention_author=True
                )
