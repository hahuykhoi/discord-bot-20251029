"""
Rate limiting utilities
"""
import asyncio
import discord
from discord.ext import tasks
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Class quản lý rate limiting cho commands"""
    
    def __init__(self, max_concurrent=2, queue_delay=45):
        """
        Khởi tạo rate limiter với cài đặt bảo thủ hơn
        
        Args:
            max_concurrent: Số lượng commands tối đa đồng thời (giảm từ 3 xuống 2)
            queue_delay: Thời gian delay ước tính cho queue (tăng từ 30 lên 45 giây)
        """
        self._active_commands = 0
        self._max_concurrent_commands = max_concurrent
        self._command_queue = asyncio.Queue()
        self._queue_delay = queue_delay
        self._started = False
        
        # Thêm exponential backoff cho Discord API
        self._api_call_count = 0
        self._last_api_reset = datetime.now()
        self._api_limit_per_minute = 30  # Giới hạn 30 API calls/phút
        
        # Queue processor sẽ được start sau khi có event loop
    
    @tasks.loop(seconds=2)  # Tăng từ 1 giây lên 2 giây để giảm tải
    async def command_queue_processor(self):
        """Background task để xử lý command queue với rate limiting cải thiện"""
        try:
            # Kiểm tra API rate limit
            await self._check_api_rate_limit()
            
            if not self._command_queue.empty() and self._active_commands < self._max_concurrent_commands:
                # Lấy command từ queue
                queued_item = await asyncio.wait_for(self._command_queue.get(), timeout=0.1)
                ctx, command_func, args, kwargs = queued_item
                
                # Tăng counter
                self._active_commands += 1
                
                try:
                    # Thêm delay nhỏ để tránh spam
                    await asyncio.sleep(0.5)
                    
                    # Thực thi command
                    await command_func(*args, **kwargs)
                    
                    # Track API call
                    self._api_call_count += 1
                    
                except discord.HTTPException as e:
                    if e.status == 429:  # Rate limited
                        logger.warning(f"Discord rate limit hit: {e}")
                        # Đưa command trở lại queue để thử lại sau
                        await self._command_queue.put((ctx, command_func, args, kwargs))
                        await asyncio.sleep(2)  # Chờ lâu hơn khi bị rate limit
                    else:
                        logger.error(f"Discord HTTP error: {e}")
                        try:
                            await ctx.reply(f"{ctx.author.mention} ❌ Lỗi Discord API: {str(e)[:50]}", mention_author=True)
                        except:
                            pass
                except Exception as e:
                    logger.error(f"Error executing queued command: {e}")
                    try:
                        await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra khi xử lý lệnh từ queue: {str(e)[:50]}", mention_author=True)
                    except:
                        pass
                finally:
                    # Giảm counter
                    self._active_commands -= 1
                    
        except asyncio.TimeoutError:
            pass  # Không có command trong queue
        except Exception as e:
            logger.error(f"Error in command queue processor: {e}")
    
    async def _check_api_rate_limit(self):
        """Kiểm tra và reset API rate limit counter"""
        now = datetime.now()
        if (now - self._last_api_reset).total_seconds() >= 60:
            # Reset counter mỗi phút
            self._api_call_count = 0
            self._last_api_reset = now
        
        # Nếu đã đạt giới hạn, chờ
        if self._api_call_count >= self._api_limit_per_minute:
            wait_time = 60 - (now - self._last_api_reset).total_seconds()
            if wait_time > 0:
                logger.info(f"API rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
    
    async def execute_with_rate_limit(self, ctx, command_func, *args, **kwargs):
        """
        Thực thi command với rate limiting cải thiện
        
        Args:
            ctx: Discord context
            command_func: Function cần thực thi
            *args, **kwargs: Arguments cho function
        """
        # Kiểm tra API rate limit trước
        await self._check_api_rate_limit()
        
        if self._active_commands < self._max_concurrent_commands:
            # Có slot trống, thực thi ngay
            self._active_commands += 1
            try:
                # Thêm delay nhỏ để tránh spam
                await asyncio.sleep(0.3)
                
                await command_func(*args, **kwargs)
                
                # Track API call
                self._api_call_count += 1
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    logger.warning(f"Discord rate limit hit in direct execution: {e}")
                    # Thêm vào queue để thử lại sau
                    await self._command_queue.put((ctx, command_func, args, kwargs))
                    await ctx.reply(
                        f"{ctx.author.mention} ⏳ Bot đang bị giới hạn tốc độ Discord. Lệnh đã được thêm vào hàng đợi.",
                        mention_author=True
                    )
                else:
                    raise  # Re-raise other HTTP exceptions
            finally:
                self._active_commands -= 1
        else:
            # Hết slot, thêm vào queue
            await self._command_queue.put((ctx, command_func, args, kwargs))
            
            # Thông báo cho user với thông tin cập nhật
            queue_size = self._command_queue.qsize()
            estimated_wait = queue_size * self._queue_delay
            
            embed = discord.Embed(
                title="⏳ Lệnh đang trong hàng đợi",
                description=f"{ctx.author.mention}, hiện tại đang có {self._active_commands}/{self._max_concurrent_commands} lệnh đang chạy.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Vị trí trong hàng đợi", 
                value=f"#{queue_size}", 
                inline=True
            )
            embed.add_field(
                name="Thời gian chờ ước tính", 
                value=f"~{estimated_wait} giây", 
                inline=True
            )
            embed.add_field(
                name="💡 Lý do", 
                value=f"Để tránh Discord rate limiting, bot chỉ xử lý tối đa {self._max_concurrent_commands} lệnh đồng thời.", 
                inline=False
            )
            embed.add_field(
                name="📊 API Status",
                value=f"API calls: {self._api_call_count}/{self._api_limit_per_minute}/phút",
                inline=True
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Command {ctx.command.name} from {ctx.author} queued. Queue size: {queue_size}")
    
    def get_status(self):
        """
        Lấy trạng thái hiện tại của rate limiter với thông tin API
        
        Returns:
            dict: Thông tin trạng thái
        """
        return {
            'active_commands': self._active_commands,
            'max_concurrent': self._max_concurrent_commands,
            'queue_size': self._command_queue.qsize(),
            'queue_delay': self._queue_delay,
            'api_calls': self._api_call_count,
            'api_limit': self._api_limit_per_minute,
            'api_reset_time': self._last_api_reset.strftime('%H:%M:%S')
        }
    
    def start(self):
        """Start rate limiter background tasks"""
        if not self._started:
            self.command_queue_processor.start()
            self._started = True
            logger.info("Rate limiter started")
    
    def stop(self):
        """Dừng rate limiter"""
        if hasattr(self, 'command_queue_processor') and self._started:
            self.command_queue_processor.cancel()
            self._started = False
