"""
Network optimization và ping monitoring utilities
"""
import asyncio
import aiohttp
import time
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class NetworkOptimizer:
    """Class tối ưu hóa network performance"""
    
    def __init__(self, bot_instance):
        """
        Khởi tạo network optimizer
        
        Args:
            bot_instance: Instance của AutoReplyBot
        """
        self.bot_instance = bot_instance
        self.ping_history = deque(maxlen=50)  # Lưu 50 ping measurements gần nhất
        self.api_ping_history = deque(maxlen=50)
        self.connection_issues = 0
        self.last_optimization = datetime.now()
        
        # Network settings
        self.timeout_settings = aiohttp.ClientTimeout(
            total=30,      # Total timeout
            connect=10,    # Connection timeout
            sock_read=15   # Socket read timeout
        )
        
        # Connection pool settings
        self.connector_settings = {
            'limit': 100,           # Total connection pool size
            'limit_per_host': 30,   # Connections per host
            'ttl_dns_cache': 300,   # DNS cache TTL (5 minutes)
            'use_dns_cache': True,
            'keepalive_timeout': 30,
            'enable_cleanup_closed': True
        }
    
    async def measure_api_ping(self, ctx) -> int:
        """
        Đo API ping một cách tối ưu hơn
        
        Args:
            ctx: Discord context
            
        Returns:
            int: Ping in milliseconds
        """
        try:
            # Method 1: Đo thời gian edit message (chính xác hơn)
            start_time = time.perf_counter()
            message = await ctx.send("🏓 Measuring ping...")
            
            edit_start = time.perf_counter()
            await message.edit(content="🏓 Ping measured!")
            edit_end = time.perf_counter()
            
            # Cleanup
            await asyncio.sleep(0.5)
            await message.delete()
            
            # Tính ping từ edit operation (chính xác hơn)
            api_ping = round((edit_end - edit_start) * 1000)
            
            # Lưu vào history
            self.api_ping_history.append(api_ping)
            
            return api_ping
            
        except Exception as e:
            logger.error(f"Error measuring API ping: {e}")
            return 9999  # Return high ping on error
    
    async def measure_websocket_ping(self) -> int:
        """
        Đo WebSocket ping (Bot Latency)
        
        Returns:
            int: WebSocket ping in milliseconds
        """
        try:
            ws_ping = round(self.bot_instance.bot.latency * 1000)
            self.ping_history.append(ws_ping)
            return ws_ping
        except Exception as e:
            logger.error(f"Error measuring WebSocket ping: {e}")
            return 9999
    
    def get_ping_statistics(self) -> Dict:
        """
        Lấy thống kê ping
        
        Returns:
            Dict: Ping statistics
        """
        if not self.ping_history or not self.api_ping_history:
            return {
                'ws_avg': 0, 'ws_min': 0, 'ws_max': 0,
                'api_avg': 0, 'api_min': 0, 'api_max': 0,
                'status': 'No data'
            }
        
        ws_pings = list(self.ping_history)
        api_pings = list(self.api_ping_history)
        
        return {
            'ws_avg': round(sum(ws_pings) / len(ws_pings)),
            'ws_min': min(ws_pings),
            'ws_max': max(ws_pings),
            'api_avg': round(sum(api_pings) / len(api_pings)),
            'api_min': min(api_pings),
            'api_max': max(api_pings),
            'status': self._get_connection_status()
        }
    
    def _get_connection_status(self) -> str:
        """
        Đánh giá trạng thái kết nối
        
        Returns:
            str: Connection status
        """
        if not self.api_ping_history:
            return "Unknown"
        
        recent_pings = list(self.api_ping_history)[-10:]  # 10 pings gần nhất
        avg_ping = sum(recent_pings) / len(recent_pings)
        
        if avg_ping < 100:
            return "Excellent"
        elif avg_ping < 300:
            return "Good"
        elif avg_ping < 1000:
            return "Fair"
        elif avg_ping < 3000:
            return "Poor"
        else:
            return "Critical"
    
    async def optimize_connection(self):
        """
        Tối ưu hóa kết nối Discord
        """
        try:
            # Chỉ optimize nếu đã qua 5 phút từ lần cuối
            if datetime.now() - self.last_optimization < timedelta(minutes=5):
                return
            
            logger.info("Starting connection optimization...")
            
            # 1. Optimize Discord.py settings
            if hasattr(self.bot_instance.bot, 'http'):
                # Tăng timeout cho HTTP requests
                self.bot_instance.bot.http.timeout = 30
                
                # Optimize connector nếu có thể
                if hasattr(self.bot_instance.bot.http, 'connector'):
                    connector = self.bot_instance.bot.http.connector
                    if hasattr(connector, '_limit'):
                        connector._limit = 100
                    if hasattr(connector, '_limit_per_host'):
                        connector._limit_per_host = 30
            
            # 2. Clear DNS cache (nếu có thể)
            try:
                import socket
                # Force DNS refresh
                socket.getaddrinfo('discord.com', 443)
            except:
                pass
            
            # 3. Optimize bot settings
            self._optimize_bot_settings()
            
            self.last_optimization = datetime.now()
            logger.info("Connection optimization completed")
            
        except Exception as e:
            logger.error(f"Error during connection optimization: {e}")
    
    def _optimize_bot_settings(self):
        """
        Tối ưu hóa cài đặt bot
        """
        try:
            # Giảm message cache để tiết kiệm RAM và bandwidth
            if hasattr(self.bot_instance.bot, '_connection'):
                self.bot_instance.bot._connection.max_messages = 500
            
            # Optimize heartbeat nếu có thể
            if hasattr(self.bot_instance.bot, 'ws') and self.bot_instance.bot.ws:
                # Không thay đổi heartbeat interval vì Discord control
                pass
                
        except Exception as e:
            logger.error(f"Error optimizing bot settings: {e}")
    
    async def diagnose_connection_issues(self) -> List[str]:
        """
        Chẩn đoán vấn đề kết nối
        
        Returns:
            List[str]: Danh sách vấn đề và gợi ý
        """
        issues = []
        
        # Kiểm tra ping history
        if self.api_ping_history:
            recent_pings = list(self.api_ping_history)[-5:]
            avg_ping = sum(recent_pings) / len(recent_pings)
            
            if avg_ping > 5000:
                issues.append("🔴 API ping cực cao (>5s) - Có thể do mạng chậm hoặc Discord API overload")
            elif avg_ping > 2000:
                issues.append("🟠 API ping cao (>2s) - Kiểm tra kết nối internet")
            elif avg_ping > 1000:
                issues.append("🟡 API ping trung bình (>1s) - Có thể tối ưu được")
        
        # Kiểm tra WebSocket ping
        if self.ping_history:
            recent_ws = list(self.ping_history)[-5:]
            avg_ws = sum(recent_ws) / len(recent_ws)
            
            if avg_ws > 500:
                issues.append("🔴 WebSocket ping cao - Có thể do kết nối không ổn định")
        
        # Kiểm tra connection issues
        if self.connection_issues > 5:
            issues.append(f"⚠️ Đã có {self.connection_issues} lỗi kết nối gần đây")
        
        # Gợi ý tối ưu hóa
        if not issues:
            issues.append("✅ Kết nối ổn định")
        else:
            issues.extend([
                "",
                "💡 Gợi ý tối ưu hóa:",
                "• Kiểm tra kết nối internet",
                "• Restart router/modem",
                "• Thử đổi DNS (8.8.8.8, 1.1.1.1)",
                "• Kiểm tra firewall/antivirus",
                "• Restart bot nếu cần thiết"
            ])
        
        return issues
    
    def record_connection_issue(self):
        """
        Ghi nhận lỗi kết nối
        """
        self.connection_issues += 1
        logger.warning(f"Connection issue recorded. Total: {self.connection_issues}")
    
    def reset_connection_issues(self):
        """
        Reset counter lỗi kết nối
        """
        self.connection_issues = 0
        logger.info("Connection issues counter reset")
    
    def get_network_stats(self) -> Dict:
        """
        Lấy thống kê network
        
        Returns:
            Dict: Network statistics
        """
        ping_stats = self.get_ping_statistics()
        
        return {
            'ping_stats': ping_stats,
            'connection_issues': self.connection_issues,
            'last_optimization': self.last_optimization.strftime('%H:%M:%S'),
            'ping_samples': len(self.ping_history),
            'api_samples': len(self.api_ping_history)
        }
