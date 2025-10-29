"""
Message Cache Utility để giảm Discord API calls
"""
import asyncio
import discord
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)

class MessageCache:
    """Cache messages để giảm API calls"""
    
    def __init__(self, max_cache_size=500, cache_duration_minutes=10):
        """
        Khởi tạo message cache
        
        Args:
            max_cache_size: Số lượng message tối đa trong cache
            cache_duration_minutes: Thời gian cache (phút)
        """
        self._cache: Dict[int, dict] = {}  # message_id -> {message, timestamp}
        self._max_cache_size = max_cache_size
        self._cache_duration = timedelta(minutes=cache_duration_minutes)
        self._access_count = 0
        self._hit_count = 0
        
        # Set để track các message đang được fetch để tránh duplicate requests
        self._fetching_messages: Set[int] = set()
        
        # Start cleanup task
        self._cleanup_task = None
    
    async def get_message(self, channel: discord.TextChannel, message_id: int) -> Optional[discord.Message]:
        """
        Lấy message từ cache hoặc fetch từ Discord API
        
        Args:
            channel: Discord channel
            message_id: ID của message
            
        Returns:
            Discord message hoặc None nếu không tìm thấy
        """
        self._access_count += 1
        
        # Kiểm tra cache trước
        cached_data = self._cache.get(message_id)
        if cached_data:
            message, timestamp = cached_data['message'], cached_data['timestamp']
            
            # Kiểm tra xem cache còn valid không
            if datetime.now() - timestamp < self._cache_duration:
                self._hit_count += 1
                logger.debug(f"Cache hit for message {message_id}")
                return message
            else:
                # Cache expired, xóa
                del self._cache[message_id]
        
        # Kiểm tra xem có đang fetch message này không
        if message_id in self._fetching_messages:
            # Chờ một chút rồi thử lại
            await asyncio.sleep(0.1)
            return await self.get_message(channel, message_id)
        
        # Fetch từ Discord API
        try:
            self._fetching_messages.add(message_id)
            
            # Thêm delay nhỏ để tránh spam API
            await asyncio.sleep(0.1)
            
            message = await channel.fetch_message(message_id)
            
            # Cache message
            self._cache_message(message)
            
            logger.debug(f"Fetched and cached message {message_id}")
            return message
            
        except discord.NotFound:
            logger.debug(f"Message {message_id} not found")
            return None
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited when fetching message {message_id}")
                # Chờ lâu hơn khi bị rate limit
                await asyncio.sleep(2)
                return None
            else:
                logger.error(f"HTTP error fetching message {message_id}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None
        finally:
            self._fetching_messages.discard(message_id)
    
    def _cache_message(self, message: discord.Message):
        """Cache một message"""
        # Kiểm tra kích thước cache
        if len(self._cache) >= self._max_cache_size:
            # Xóa message cũ nhất
            oldest_id = min(self._cache.keys(), 
                           key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_id]
        
        # Cache message
        self._cache[message.id] = {
            'message': message,
            'timestamp': datetime.now()
        }
    
    async def bulk_cache_messages(self, channel: discord.TextChannel, limit: int = 50):
        """
        Cache nhiều message cùng lúc để tối ưu
        
        Args:
            channel: Discord channel
            limit: Số lượng message tối đa
        """
        try:
            # Sử dụng history() thay vì fetch từng message
            async for message in channel.history(limit=limit):
                self._cache_message(message)
                
            logger.info(f"Bulk cached {min(limit, len(self._cache))} messages from {channel.name}")
            
        except discord.HTTPException as e:
            if e.status == 429:
                logger.warning(f"Rate limited during bulk cache in {channel.name}")
            else:
                logger.error(f"Error during bulk cache: {e}")
        except Exception as e:
            logger.error(f"Error during bulk cache: {e}")
    
    def clear_cache(self):
        """Xóa toàn bộ cache"""
        self._cache.clear()
        logger.info("Message cache cleared")
    
    def cleanup_expired(self):
        """Xóa các message đã hết hạn trong cache"""
        now = datetime.now()
        expired_ids = []
        
        for message_id, data in self._cache.items():
            if now - data['timestamp'] >= self._cache_duration:
                expired_ids.append(message_id)
        
        for message_id in expired_ids:
            del self._cache[message_id]
        
        if expired_ids:
            logger.debug(f"Cleaned up {len(expired_ids)} expired messages from cache")
    
    def get_stats(self) -> dict:
        """Lấy thống kê cache"""
        hit_rate = (self._hit_count / self._access_count * 100) if self._access_count > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'max_cache_size': self._max_cache_size,
            'access_count': self._access_count,
            'hit_count': self._hit_count,
            'hit_rate': f"{hit_rate:.1f}%",
            'fetching_count': len(self._fetching_messages)
        }
    
    def start_cleanup_task(self):
        """Bắt đầu task cleanup định kỳ"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Task cleanup định kỳ"""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup mỗi 5 phút
                self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def stop_cleanup_task(self):
        """Dừng task cleanup"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

# Global message cache instance
message_cache = MessageCache()
