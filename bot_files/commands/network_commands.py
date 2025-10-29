"""
Network diagnostic và optimization commands
"""
import discord
from discord.ext import commands
import logging
import asyncio
from .base import BaseCommand

logger = logging.getLogger(__name__)

class NetworkCommands(BaseCommand):
    """Class chứa các commands network diagnostic"""
    
    def register_commands(self):
        """Register network commands"""
        
        @self.bot.command(name='netping')
        async def ping_command(ctx):
            """
            Kiểm tra ping và chẩn đoán kết nối
            
            Usage: !netping
            """
            await self._ping_diagnostic_impl(ctx)
        
        # Command optimize đã bị xóa vì conflict với built-in command
        
        @self.bot.command(name='netstat')
        async def network_stats(ctx):
            """
            Hiển thị thống kê network chi tiết
            
            Usage: !netstat
            """
            await self._network_stats_impl(ctx)
    
    async def _ping_diagnostic_impl(self, ctx):
        """
        Implementation thực tế của ping diagnostic command
        """
        network_optimizer = self.bot_instance.network_optimizer
        
        # Đo ping nhiều lần để có kết quả chính xác
        loading_msg = await ctx.send("🔍 Đang chẩn đoán kết nối...")
        
        pings = []
        for i in range(3):
            ping = await network_optimizer.measure_api_ping(ctx)
            pings.append(ping)
            await loading_msg.edit(content=f"🔍 Đang chẩn đoán kết nối... ({i+1}/3)")
        
        await loading_msg.delete()
        
        # Phân tích kết quả
        avg_ping = sum(pings) / len(pings)
        min_ping = min(pings)
        max_ping = max(pings)
        
        # Chẩn đoán vấn đề
        issues = await network_optimizer.diagnose_connection_issues()
        
        # Xác định màu sắc
        if avg_ping < 300:
            color = discord.Color.green()
            status_icon = "🟢"
        elif avg_ping < 1000:
            color = discord.Color.orange()
            status_icon = "🟡"
        else:
            color = discord.Color.red()
            status_icon = "🔴"
        
        embed = discord.Embed(
            title=f"🏓 Chẩn đoán Ping {status_icon}",
            description=f"Kết quả đo ping từ 3 lần thử nghiệm",
            color=color
        )
        
        embed.add_field(
            name="📊 Kết quả đo lường",
            value=(
                f"Trung bình: **{round(avg_ping)}ms**\n"
                f"Thấp nhất: {min_ping}ms\n"
                f"Cao nhất: {max_ping}ms\n"
                f"Biến động: {max_ping - min_ping}ms"
            ),
            inline=True
        )
        
        # Thêm thống kê tổng thể
        ping_stats = network_optimizer.get_ping_statistics()
        embed.add_field(
            name="📈 Thống kê tổng thể",
            value=(
                f"Trạng thái: **{ping_stats['status']}**\n"
                f"WebSocket: {ping_stats['ws_avg']}ms\n"
                f"API TB: {ping_stats['api_avg']}ms\n"
                f"Mẫu dữ liệu: {len(network_optimizer.api_ping_history)}"
            ),
            inline=True
        )
        
        # Hiển thị chẩn đoán
        diagnosis_text = "\n".join(issues[:10])  # Giới hạn 10 dòng
        if len(diagnosis_text) > 1024:
            diagnosis_text = diagnosis_text[:1020] + "..."
        
        embed.add_field(
            name="🔍 Chẩn đoán",
            value=diagnosis_text,
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    # Method _optimize_connection_impl đã bị xóa vì command optimize conflict
    
    async def _network_stats_impl(self, ctx):
        """
        Implementation thực tế của network stats command
        """
        network_optimizer = self.bot_instance.network_optimizer
        network_stats = network_optimizer.get_network_stats()
        ping_stats = network_optimizer.get_ping_statistics()
        
        embed = discord.Embed(
            title="📊 Thống kê Network Chi tiết",
            description="Thông tin chi tiết về hiệu suất mạng",
            color=discord.Color.blue()
        )
        
        # WebSocket stats
        embed.add_field(
            name="🔌 WebSocket",
            value=(
                f"Trung bình: {ping_stats['ws_avg']}ms\n"
                f"Min: {ping_stats['ws_min']}ms\n"
                f"Max: {ping_stats['ws_max']}ms\n"
                f"Trạng thái: {ping_stats['status']}"
            ),
            inline=True
        )
        
        # API stats
        embed.add_field(
            name="🌐 API Performance",
            value=(
                f"Trung bình: {ping_stats['api_avg']}ms\n"
                f"Min: {ping_stats['api_min']}ms\n"
                f"Max: {ping_stats['api_max']}ms\n"
                f"Mẫu: {network_stats['api_samples']}"
            ),
            inline=True
        )
        
        # Connection health
        embed.add_field(
            name="🏥 Connection Health",
            value=(
                f"Issues: {network_stats['connection_issues']}\n"
                f"Last optimize: {network_stats['last_optimization']}\n"
                f"Ping samples: {network_stats['ping_samples']}\n"
                f"Status: {ping_stats['status']}"
            ),
            inline=True
        )
        
        # Recommendations
        if ping_stats['api_avg'] > 1000:
            recommendations = (
                "🔴 **Ping cao - Cần tối ưu hóa:**\n"
                "• Kiểm tra kết nối internet\n"
                "• Thử đổi DNS server (8.8.8.8)\n"
                "• Restart router/modem\n"
                "• Restart bot nếu cần"
            )
            rec_color = "🔴"
        elif ping_stats['api_avg'] > 500:
            recommendations = (
                "🟡 **Ping trung bình:**\n"
                "• Monitor với `!netping`\n"
                "• Kiểm tra kết nối nếu cần"
            )
            rec_color = "🟡"
        else:
            recommendations = (
                "🟢 **Kết nối tốt:**\n"
                "• Không cần tối ưu thêm\n"
                "• Tiếp tục monitor"
            )
            rec_color = "🟢"
        
        embed.add_field(
            name=f"{rec_color} Khuyến nghị",
            value=recommendations,
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
