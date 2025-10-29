import discord
from discord.ext import commands
import logging
from .base import BaseCommand
from utils.shared_wallet import shared_wallet

logger = logging.getLogger(__name__)

class WalletReloadCommands(BaseCommand):
    """Commands để reload wallet data"""
    
    def register_commands(self):
        """Đăng ký các commands"""
        
        @self.bot.command(name='reloadwallet', aliases=['rwallet', 'refreshwallet'])
        async def reload_wallet(ctx):
            """
            Reload dữ liệu ví từ file (manual)
            
            Usage: ;reloadwallet
            Aliases: ;rwallet, ;refreshwallet
            """
            # Kiểm tra quyền admin
            if not ctx.author.guild_permissions.administrator:
                is_admin = hasattr(self.bot_instance, 'admin_ids') and ctx.author.id in self.bot_instance.admin_ids
                is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
                
                if not (is_admin or is_supreme):
                    await ctx.reply(
                        "❌ Bạn cần quyền **Administrator** hoặc là **Admin/Supreme Admin** của bot để sử dụng lệnh này!",
                        mention_author=True
                    )
                    return
            
            # Processing message
            processing_embed = discord.Embed(
                title="🔄 Đang reload wallet data...",
                description="Đang tải lại dữ liệu từ file...",
                color=discord.Color.blue()
            )
            
            msg = await ctx.reply(embed=processing_embed, mention_author=True)
            
            # Reload data
            success, result = shared_wallet.reload_data()
            
            if success:
                embed = discord.Embed(
                    title="✅ Reload wallet thành công!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📊 Thống kê trước reload",
                    value=(
                        f"**Users:** {result['old_count']:,}\n"
                        f"**Tổng tiền:** {result['old_total']:,} xu"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Thống kê sau reload",
                    value=(
                        f"**Users:** {result['new_count']:,}\n"
                        f"**Tổng tiền:** {result['new_total']:,} xu"
                    ),
                    inline=True
                )
                
                # Tính thay đổi
                user_diff = result['new_count'] - result['old_count']
                money_diff = result['new_total'] - result['old_total']
                
                changes = []
                if user_diff != 0:
                    sign = "+" if user_diff > 0 else ""
                    changes.append(f"Users: {sign}{user_diff}")
                if money_diff != 0:
                    sign = "+" if money_diff > 0 else ""
                    changes.append(f"Tiền: {sign}{money_diff:,} xu")
                
                if changes:
                    embed.add_field(
                        name="📈 Thay đổi",
                        value="\n".join(changes),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="ℹ️ Thông báo",
                        value="Không có thay đổi nào",
                        inline=False
                    )
                
                embed.set_footer(text=f"Reload bởi {ctx.author.display_name}")
                
                await msg.edit(embed=embed)
                logger.info(f"Wallet reloaded manually by {ctx.author.id}")
                
            else:
                embed = discord.Embed(
                    title="❌ Lỗi reload wallet",
                    description=f"```\n{result}\n```",
                    color=discord.Color.red()
                )
                await msg.edit(embed=embed)
        
        @self.bot.command(name='autowallet', aliases=['autoreloadwallet'])
        async def auto_wallet(ctx, action: str = None, interval: int = 5):
            """
            Bật/tắt auto reload wallet khi file thay đổi
            
            Usage: 
            ;autowallet start [interval] - Bật auto reload (check mỗi X giây)
            ;autowallet stop - Tắt auto reload
            ;autowallet status - Xem trạng thái
            
            Aliases: ;autoreloadwallet
            """
            # Kiểm tra quyền Supreme Admin
            is_supreme = hasattr(self.bot_instance, 'supreme_admin_id') and self.bot_instance.supreme_admin_id and ctx.author.id == self.bot_instance.supreme_admin_id
            
            if not is_supreme:
                await ctx.reply(
                    "❌ Chỉ **Supreme Admin** mới có thể sử dụng lệnh này!",
                    mention_author=True
                )
                return
            
            if action is None or action.lower() == "status":
                # Show status
                embed = discord.Embed(
                    title="📊 Auto Wallet Reload Status",
                    color=discord.Color.blue()
                )
                
                status = "🟢 **Đang chạy**" if shared_wallet._is_watching else "🔴 **Đã dừng**"
                embed.add_field(
                    name="Trạng thái",
                    value=status,
                    inline=False
                )
                
                if shared_wallet._is_watching:
                    embed.add_field(
                        name="ℹ️ Thông tin",
                        value="Bot đang tự động theo dõi file `shared_wallet.json` và reload khi có thay đổi",
                        inline=False
                    )
                
                embed.add_field(
                    name="📝 Lệnh",
                    value=(
                        "; start [interval]` - Bật auto reload\n"
                        "; stop` - Tắt auto reload\n"
                        "; status` - Xem trạng thái"
                    ),
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            elif action.lower() == "start":
                if shared_wallet._is_watching:
                    await ctx.reply(
                        "⚠️ Auto reload đã đang chạy rồi!",
                        mention_author=True
                    )
                    return
                
                # Validate interval
                if interval < 1:
                    interval = 5
                elif interval > 300:
                    interval = 300
                
                # Start watching
                import asyncio
                shared_wallet._file_watch_task = asyncio.create_task(
                    shared_wallet.start_file_watching(check_interval=interval)
                )
                
                embed = discord.Embed(
                    title="✅ Đã bật auto reload wallet!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="⚙️ Cài đặt",
                    value=f"**Check interval:** {interval} giây",
                    inline=False
                )
                
                embed.add_field(
                    name="📂 File theo dõi",
                    value="`shared_wallet.json`",
                    inline=False
                )
                
                embed.add_field(
                    name="🔄 Hoạt động",
                    value="Bot sẽ tự động reload khi phát hiện file thay đổi",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                logger.info(f"Auto wallet reload started by {ctx.author.id} (interval: {interval}s)")
                
            elif action.lower() == "stop":
                if not shared_wallet._is_watching:
                    await ctx.reply(
                        "⚠️ Auto reload chưa chạy!",
                        mention_author=True
                    )
                    return
                
                # Stop watching
                shared_wallet.stop_file_watching()
                
                embed = discord.Embed(
                    title="🛑 Đã tắt auto reload wallet!",
                    color=discord.Color.orange()
                )
                
                embed.add_field(
                    name="ℹ️ Thông báo",
                    value="Bot sẽ không tự động reload wallet nữa",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Tip",
                    value="Dùng ;` để reload thủ công",
                    inline=False
                )
                
                await ctx.reply(embed=embed, mention_author=True)
                logger.info(f"Auto wallet reload stopped by {ctx.author.id}")
                
            else:
                await ctx.reply(
                    f"❌ Action không hợp lệ: `{action}`\n"
                    "Sử dụng: `start`, `stop`, hoặc `status`",
                    mention_author=True
                )
        
        @self.bot.command(name='walletstats', aliases=['wstats'])
        async def wallet_stats(ctx):
            """
            Xem thống kê tổng quan của wallet system
            
            Usage: ;walletstats
            Aliases: ;wstats
            """
            embed = discord.Embed(
                title="💰 Wallet System Statistics",
                color=discord.Color.gold()
            )
            
            user_count = shared_wallet.get_user_count()
            total_money = shared_wallet.get_total_money_in_system()
            
            embed.add_field(
                name="👥 Tổng Users",
                value=f"**{user_count:,}** người",
                inline=True
            )
            
            embed.add_field(
                name="💵 Tổng tiền trong hệ thống",
                value=f"**{total_money:,}** xu",
                inline=True
            )
            
            if user_count > 0:
                avg_balance = total_money / user_count
                embed.add_field(
                    name="📊 Trung bình/người",
                    value=f"**{avg_balance:,.0f}** xu",
                    inline=True
                )
            
            # Top 3 richest
            rich_users = shared_wallet.get_all_users_with_money()[:3]
            
            if rich_users:
                top_text = []
                medals = ["🥇", "🥈", "🥉"]
                
                for i, user_data in enumerate(rich_users):
                    try:
                        user = await self.bot.fetch_user(user_data['user_id'])
                        username = user.display_name
                    except:
                        username = f"User {user_data['user_id']}"
                    
                    top_text.append(f"{medals[i]} **{username}:** {user_data['balance']:,} xu")
                
                embed.add_field(
                    name="🏆 Top 3 Giàu nhất",
                    value="\n".join(top_text),
                    inline=False
                )
            
            # Auto reload status
            auto_status = "🟢 Đang bật" if shared_wallet._is_watching else "🔴 Đã tắt"
            embed.add_field(
                name="🔄 Auto Reload",
                value=auto_status,
                inline=True
            )
            
            embed.add_field(
                name="📂 File",
                value="`shared_wallet.json`",
                inline=True
            )
            
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")
            
            await ctx.reply(embed=embed, mention_author=True)

        logger.info("Wallet reload commands registered")
