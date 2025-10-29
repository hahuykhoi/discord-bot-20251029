"""
Memory management utilities
"""
import asyncio
import json
from datetime import datetime, timedelta
from discord.ext import tasks
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """Class quản lý memory và cleanup"""
    
    def __init__(self, bot_instance):
        """
        Khởi tạo memory manager
        
        Args:
            bot_instance: Instance của AutoReplyBot
        """
        self.bot_instance = bot_instance
        self._pending_saves = False
        self._started = False
        
        # Background tasks sẽ được start sau khi có event loop
    
    @tasks.loop(minutes=5)
    async def cleanup_task(self):
        """Background task để dọn dẹp memory định kỳ"""
        current_time = datetime.now()
        
        # Cleanup expired cooldowns (> 10 phút)
        expired_cooldowns = [
            user_id for user_id, last_time in self.bot_instance.cooldowns.items()
            if current_time - last_time > timedelta(minutes=10)
        ]
        for user_id in expired_cooldowns:
            del self.bot_instance.cooldowns[user_id]
        
        # Cleanup expired user command history (> 2 phút)
        expired_users = []
        for user_id, command_history in self.bot_instance.user_command_history.items():
            # Xóa các lệnh cũ hơn 2 phút
            two_minutes_ago = current_time - timedelta(minutes=2)
            while command_history and command_history[0] < two_minutes_ago:
                command_history.popleft()
            
            # Nếu không còn lệnh nào trong lịch sử, xóa user khỏi dict
            if not command_history:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.bot_instance.user_command_history[user_id]
        
        # Cleanup completed mute tasks
        completed_tasks = [
            user_id for user_id, task in self.bot_instance.mute_tasks.items()
            if task.done()
        ]
        for user_id in completed_tasks:
            del self.bot_instance.mute_tasks[user_id]
        
        # Clear role cache nếu quá lớn
        if len(self.bot_instance._role_cache) > 50:
            self.bot_instance._role_cache.clear()
            logger.info("Cleared role cache due to size limit")
        
        if expired_cooldowns or expired_users or completed_tasks:
            logger.info(f"Memory cleanup: {len(expired_cooldowns)} cooldowns, {len(expired_users)} user histories, {len(completed_tasks)} tasks")
    
    @tasks.loop(minutes=2)
    async def batch_save_task(self):
        """Background task để batch save data thay vì save ngay lập tức"""
        if self._pending_saves:
            await self._batch_save_data()
            self._pending_saves = False
    
    async def _batch_save_data(self):
        """Batch save để giảm I/O operations"""
        try:
            # Convert deque warnings to list for JSON serialization
            warnings_data = {}
            for user_id, warnings_deque in self.bot_instance.warnings.items():
                warnings_data[str(user_id)] = list(warnings_deque)
            
            # Save warnings
            warnings_file = self.bot_instance.config.get('warnings_file', 'warnings.json')
            with open(warnings_file, 'w', encoding='utf-8') as f:
                json.dump(warnings_data, f, indent=2, ensure_ascii=False)
            
            # Save admin IDs
            admin_data = {
                "admin_ids": list(self.bot_instance.admin_ids),
                "description": "Danh sách User IDs có quyền sử dụng lệnh warn"
            }
            admin_file = self.bot_instance.config.get('admin_file', 'admin.json')
            with open(admin_file, 'w', encoding='utf-8') as f:
                json.dump(admin_data, f, indent=2, ensure_ascii=False)
            
            # Save priority users
            priority_data = {
                "priority_users": list(self.bot_instance.priority_users),
                "description": "Danh sách User IDs được bypass rate limiting"
            }
            priority_file = self.bot_instance.config.get('priority_file', 'priority.json')
            with open(priority_file, 'w', encoding='utf-8') as f:
                json.dump(priority_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Batch saved warnings, admin and priority data")
            
        except Exception as e:
            logger.error(f"Error in batch save: {e}")
    
    def mark_for_save(self):
        """Mark data for saving trong next batch cycle"""
        self._pending_saves = True
    
    def get_memory_stats(self):
        """
        Lấy thống kê memory usage
        
        Returns:
            dict: Memory statistics
        """
        return {
            'cooldowns': len(self.bot_instance.cooldowns),
            'user_command_history': len(self.bot_instance.user_command_history),
            'mute_tasks': len(self.bot_instance.mute_tasks),
            'role_cache': len(self.bot_instance._role_cache),
            'warnings_users': len(self.bot_instance.warnings),
            'admin_ids': len(self.bot_instance.admin_ids),
            'priority_users': len(self.bot_instance.priority_users),
            'supreme_admin': 1 if self.bot_instance.supreme_admin_id else 0,
            'pending_saves': self._pending_saves
        }
    
    def start(self):
        """Start memory manager background tasks"""
        if not self._started:
            self.cleanup_task.start()
            self.batch_save_task.start()
            self._started = True
            logger.info("Memory manager started")
    
    def stop(self):
        """Dừng memory manager"""
        if self._started:
            if hasattr(self, 'cleanup_task'):
                self.cleanup_task.cancel()
            if hasattr(self, 'batch_save_task'):
                self.batch_save_task.cancel()
            self._started = False
        
        # Final save before shutdown
        if self._pending_saves:
            asyncio.create_task(self._batch_save_data())
