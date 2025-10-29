# -*- coding: utf-8 -*-
"""
DM Management Commands - Quản lý tin nhắn DM
"""
import discord
from discord.ext import commands
import logging
import json
import os
from datetime import datetime, timedelta
import asyncio
from .base import BaseCommand

logger = logging.getLogger(__name__)

class DMManagementCommands(BaseCommand):
    """Class chứa các commands quản lý DM"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.dm_history_file = "dm_history.json"
        self.dm_history = self.load_dm_history()
        self.cleanup_task = None
        self.cleanup_started = False
    
    def load_dm_history(self):
        """Load lịch sử DM từ file"""
        try:
            if os.path.exists(self.dm_history_file):
                with open(self.dm_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading DM history: {e}")
            return []
    
    def save_dm_history(self):
        """Save lịch sử DM vào file"""
        try:
            # Tự động cleanup DM cũ hơn 3 ngày trước khi save
            self.cleanup_old_dms()
            
            # Giữ tối đa 500 tin nhắn DM gần nhất
            if len(self.dm_history) > 500:
                self.dm_history = self.dm_history[-500:]
            
            with open(self.dm_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.dm_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving DM history: {e}")
    
    def cleanup_old_dms(self):
        """Xóa DM cũ hơn 3 ngày"""
        try:
            cutoff_time = datetime.now() - timedelta(days=3)
            original_count = len(self.dm_history)
            
            # Lọc chỉ giữ DM trong 3 ngày gần đây
            self.dm_history = [
                dm for dm in self.dm_history
                if datetime.fromisoformat(dm['timestamp']) > cutoff_time
            ]
            
            deleted_count = original_count - len(self.dm_history)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old DM entries (older than 3 days)")
                
        except Exception as e:
            logger.error(f"Error cleaning up old DMs: {e}")
    
    async def start_cleanup_task(self):
        """Khởi động task cleanup định kỳ"""
        try:
            if self.cleanup_started:
                return
                
            # Đợi bot ready
            await self.bot.wait_until_ready()
            
            # Tạo task cleanup chạy mỗi 6 giờ
            self.cleanup_task = asyncio.create_task(self.periodic_cleanup())
            self.cleanup_started = True
            logger.info("DM cleanup task started - will run every 6 hours")
            
        except Exception as e:
            logger.error(f"Error starting cleanup task: {e}")
    
    async def periodic_cleanup(self):
        """Task cleanup chạy định kỳ mỗi 6 giờ"""
        while not self.bot.is_closed():
            try:
                # Cleanup DM cũ
                original_count = len(self.dm_history)
                self.cleanup_old_dms()
                deleted_count = original_count - len(self.dm_history)
                
                if deleted_count > 0:
                    # Save lại file sau khi cleanup
                    with open(self.dm_history_file, 'w', encoding='utf-8') as f:
                        json.dump(self.dm_history, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Periodic cleanup: Removed {deleted_count} old DM entries")
                
                # Đợi 6 giờ (21600 giây)
                await asyncio.sleep(21600)
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                # Nếu có lỗi, đợi 1 giờ rồi thử lại
                await asyncio.sleep(3600)
    
    def register_commands(self):
        """Register DM management commands"""
        
        @self.bot.command(name='checkdms')
        async def check_dms(ctx, limit: int = 10):
            """
            Xem tin nhắn DM gần đây (Chỉ Supreme Admin)
            
            Usage: ;checkdms [số lượng]
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            
            await self.execute_with_rate_limit(ctx, self._check_dms_impl, ctx, limit)
        
        @self.bot.command(name='cleanupdms')
        async def cleanup_dms_manual(ctx):
            """
            Thực hiện cleanup DM thủ công (Chỉ Supreme Admin)
            
            Usage: ;cleanupdms
            """
            # Chỉ Supreme Admin mới có thể sử dụng
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply(f"{ctx.author.mention} ❌ Chỉ Supreme Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            
            await self.execute_with_rate_limit(ctx, self._cleanup_dms_manual_impl, ctx)
    
    async def _check_dms_impl(self, ctx, limit: int):
        """Implementation thực tế của checkdms command"""
        try:
            # Validate limit
            if limit < 1:
                limit = 10
            elif limit > 50:
                limit = 50
            
            # Lấy tin nhắn DM gần đây
            recent_dms = self.dm_history[-limit:] if self.dm_history else []
            
            if not recent_dms:
                embed = discord.Embed(
                    title="📭 Không có tin nhắn DM",
                    description="Chưa có tin nhắn DM nào được ghi nhận.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="💡 Thông tin",
                    value="Hệ thống sẽ tự động ghi nhận và forward tin nhắn DM đến Supreme Admin.",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Tạo embed hiển thị DM
            embed = discord.Embed(
                title=f"📬 {len(recent_dms)} tin nhắn DM gần đây",
                description=f"Hiển thị {len(recent_dms)} tin nhắn DM mới nhất",
                color=discord.Color.green()
            )
            
            for i, dm in enumerate(reversed(recent_dms), 1):
                try:
                    timestamp = datetime.fromisoformat(dm['timestamp'])
                    time_str = f"<t:{int(timestamp.timestamp())}:R>"
                    
                    content_preview = dm['content'][:100] + ('...' if len(dm['content']) > 100 else '')
                    
                    embed.add_field(
                        name=f"#{i} - {dm['username']} ({dm['user_id']})",
                        value=f"**Thời gian:** {time_str}\n**Nội dung:** `{content_preview}`",
                        inline=False
                    )
                    
                    # Giới hạn số field để tránh embed quá dài
                    if i >= 10:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing DM entry: {e}")
                    continue
            
            embed.set_footer(
                text=f"Tổng cộng: {len(self.dm_history)} tin nhắn DM • Hiển thị: {min(len(recent_dms), 10)}"
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lỗi hệ thống",
                description=f"Có lỗi xảy ra khi kiểm tra DM: {str(e)[:200]}",
                color=discord.Color.red()
            )
            await ctx.reply(embed=error_embed, mention_author=True)
            logger.error(f"Error in checkdms command: {e}")
    
    async def _cleanup_dms_manual_impl(self, ctx):
        """Implementation thực tế của cleanup DM manual command"""
        try:
            # Thông báo bắt đầu cleanup
            processing_embed = discord.Embed(
                title="🧹 Đang thực hiện cleanup...",
                description="Đang xóa các tin nhắn DM cũ hơn 3 ngày...",
                color=discord.Color.orange()
            )
            processing_msg = await ctx.reply(embed=processing_embed, mention_author=True)
            
            # Thực hiện cleanup
            original_count = len(self.dm_history)
            cutoff_time = datetime.now() - timedelta(days=3)
            
            # Lọc DM cũ hơn 3 ngày
            old_dms = [
                dm for dm in self.dm_history
                if datetime.fromisoformat(dm['timestamp']) <= cutoff_time
            ]
            
            # Cleanup
            self.cleanup_old_dms()
            deleted_count = original_count - len(self.dm_history)
            
            # Save lại file
            if deleted_count > 0:
                self.save_dm_history()
            
            # Tạo embed kết quả
            if deleted_count > 0:
                result_embed = discord.Embed(
                    title="✅ Cleanup hoàn thành!",
                    description=f"Đã xóa {deleted_count} tin nhắn DM cũ hơn 3 ngày",
                    color=discord.Color.green()
                )
                result_embed.add_field(
                    name="📊 Thống kê",
                    value=f"**Trước cleanup:** {original_count} DM\n**Sau cleanup:** {len(self.dm_history)} DM\n**Đã xóa:** {deleted_count} DM",
                    inline=False
                )
                
                # Hiển thị một số DM đã xóa (nếu có)
                if old_dms:
                    sample_deleted = old_dms[:3]  # Hiển thị 3 DM cũ nhất đã xóa
                    deleted_info = []
                    for dm in sample_deleted:
                        timestamp = datetime.fromisoformat(dm['timestamp'])
                        days_old = (datetime.now() - timestamp).days
                        deleted_info.append(f"• {dm['username']} - {days_old} ngày trước")
                    
                    if len(old_dms) > 3:
                        deleted_info.append(f"• ... và {len(old_dms) - 3} DM khác")
                    
                    result_embed.add_field(
                        name="🗑️ DM đã xóa (mẫu)",
                        value="\n".join(deleted_info),
                        inline=False
                    )
                
            else:
                result_embed = discord.Embed(
                    title="ℹ️ Không có DM cần xóa",
                    description="Tất cả tin nhắn DM đều trong vòng 3 ngày gần đây",
                    color=discord.Color.blue()
                )
                result_embed.add_field(
                    name="📊 Thống kê hiện tại",
                    value=f"**Tổng DM:** {len(self.dm_history)}\n**Cũ nhất:** {self._get_oldest_dm_age()} ngày",
                    inline=False
                )
            
            # Thông tin về cleanup tự động
            result_embed.add_field(
                name="🔄 Cleanup tự động",
                value="Hệ thống tự động cleanup mỗi 6 giờ\nDM cũ hơn 3 ngày sẽ được xóa tự động",
                inline=False
            )
            
            result_embed.set_footer(
                text="DM Management System • Cleanup thủ công hoàn thành"
            )
            
            # Cập nhật tin nhắn
            await processing_msg.edit(embed=result_embed)
            
            logger.info(f"Manual DM cleanup completed by {ctx.author}: {deleted_count} entries removed")
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lỗi hệ thống",
                description=f"Có lỗi xảy ra khi cleanup DM: {str(e)[:200]}",
                color=discord.Color.red()
            )
            await ctx.reply(embed=error_embed, mention_author=True)
            logger.error(f"Error in cleanup DMs command: {e}")
    
    def _get_oldest_dm_age(self):
        """Lấy tuổi của DM cũ nhất (tính bằng ngày)"""
        try:
            if not self.dm_history:
                return 0
            
            oldest_timestamp = min(
                datetime.fromisoformat(dm['timestamp']) 
                for dm in self.dm_history
            )
            age = (datetime.now() - oldest_timestamp).days
            return age
        except:
            return 0
    
    def stop_cleanup_task(self):
        """Dừng cleanup task khi bot shutdown"""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            logger.info("DM cleanup task stopped")
    
    async def handle_dm_message(self, message: discord.Message):
        """
        Xử lý tin nhắn DM - được gọi từ bot_refactored.py
        """
        try:
            # Bỏ qua tin nhắn từ bot
            if message.author.bot:
                return
            
            # Lưu vào lịch sử
            dm_entry = {
                'user_id': str(message.author.id),
                'username': str(message.author),
                'display_name': message.author.display_name,
                'content': message.content,
                'timestamp': datetime.now().isoformat(),
                'message_id': str(message.id)
            }
            
            self.dm_history.append(dm_entry)
            self.save_dm_history()
            
            # Forward đến Supreme Admin
            await self._forward_dm_to_supreme_admin(message, dm_entry)
            
            logger.info(f"DM received from {message.author} ({message.author.id}): {message.content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error handling DM message: {e}")
    
    async def _forward_dm_to_supreme_admin(self, message: discord.Message, dm_entry: dict):
        """Forward tin nhắn DM đến Supreme Admin"""
        try:
            # Lấy Supreme Admin ID
            supreme_admin_id = self.bot_instance.supreme_admin_id
            if not supreme_admin_id:
                logger.warning("No Supreme Admin set - cannot forward DM")
                return
            
            # Lấy Supreme Admin user
            try:
                supreme_admin = await self.bot.fetch_user(supreme_admin_id)
            except discord.NotFound:
                logger.error(f"Supreme Admin user {supreme_admin_id} not found")
                return
            
            # Tạo embed thông báo DM
            embed = discord.Embed(
                title="📨 Tin nhắn DM mới",
                description="Có người đã gửi tin nhắn DM cho bot",
                color=discord.Color.blue()
            )
            
            # Thông tin người gửi
            embed.add_field(
                name="👤 Người gửi",
                value=f"**Username:** {message.author}\n**Display Name:** {message.author.display_name}\n**ID:** {message.author.id}",
                inline=True
            )
            
            # Thời gian
            embed.add_field(
                name="🕒 Thời gian",
                value=f"<t:{int(message.created_at.timestamp())}:F>",
                inline=True
            )
            
            # Nội dung tin nhắn
            content_display = message.content if len(message.content) <= 1000 else message.content[:1000] + "..."
            embed.add_field(
                name="💬 Nội dung",
                value=f"```{content_display}```" if content_display else "*Không có nội dung text*",
                inline=False
            )
            
            # Thông tin bổ sung
            embed.add_field(
                name="📊 Thông tin bổ sung",
                value=f"**Message ID:** {message.id}\n**Tổng DM nhận:** {len(self.dm_history)}",
                inline=False
            )
            
            # Avatar người gửi
            if message.author.avatar:
                embed.set_thumbnail(url=message.author.avatar.url)
            
            embed.set_footer(
                text="DM Management System • Sử dụng ;checkdms để xem lịch sử",
                icon_url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None
            )
            
            # Gửi embed đến Supreme Admin
            await supreme_admin.send(embed=embed)
            
            # Nếu có attachments, gửi thông báo
            if message.attachments:
                attachment_info = []
                for attachment in message.attachments:
                    attachment_info.append(f"• {attachment.filename} ({attachment.size} bytes)")
                
                attachment_embed = discord.Embed(
                    title="📎 File đính kèm",
                    description=f"Tin nhắn có {len(message.attachments)} file đính kèm:\n" + "\n".join(attachment_info),
                    color=discord.Color.orange()
                )
                await supreme_admin.send(embed=attachment_embed)
            
            logger.info(f"DM forwarded to Supreme Admin: {message.author} -> {supreme_admin}")
            
        except discord.Forbidden:
            logger.error("Cannot send DM to Supreme Admin - DMs may be disabled")
        except Exception as e:
            logger.error(f"Error forwarding DM to Supreme Admin: {e}")
