"""
Maintenance Commands - Hệ thống bảo trì bot
Lệnh: ;close, ;open (Supreme Admin only)
"""
import discord
from discord.ext import commands
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MaintenanceCommands:
    def __init__(self, bot_instance):
        """
        Khởi tạo Maintenance Commands
        
        Args:
            bot_instance: Instance của AutoReplyBotRefactored
        """
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.maintenance_file = 'maintenance_mode.json'
        self.maintenance_data = self.load_maintenance_data()
        
        logger.info("Maintenance Commands đã được khởi tạo")
    
    def load_maintenance_data(self):
        """Load trạng thái maintenance từ file"""
        try:
            if os.path.exists(self.maintenance_file):
                with open(self.maintenance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    is_maintenance = data.get('is_maintenance', False)
                    if is_maintenance:
                        logger.warning("⚠️ BOT ĐANG Ở CHẾ ĐỘ BẢO TRÌ")
                    return data
            else:
                return {
                    'is_maintenance': False,
                    'closed_at': None,
                    'closed_by': None,
                    'reason': None
                }
        except Exception as e:
            logger.error(f"Lỗi khi load maintenance data: {e}")
            return {
                'is_maintenance': False,
                'closed_at': None,
                'closed_by': None,
                'reason': None
            }
    
    def save_maintenance_data(self):
        """Lưu trạng thái maintenance vào file"""
        try:
            with open(self.maintenance_file, 'w', encoding='utf-8') as f:
                json.dump(self.maintenance_data, f, indent=4, ensure_ascii=False)
            logger.info("Đã lưu maintenance data")
        except Exception as e:
            logger.error(f"Lỗi khi lưu maintenance data: {e}")
    
    def is_maintenance_mode(self):
        """Kiểm tra xem bot có đang bảo trì không"""
        return self.maintenance_data.get('is_maintenance', False)
    
    def set_maintenance(self, enabled, user_id, username, reason=None):
        """
        Bật/tắt chế độ bảo trì
        
        Args:
            enabled: True để bật, False để tắt
            user_id: ID người thực hiện
            username: Tên người thực hiện
            reason: Lý do (optional)
        """
        self.maintenance_data['is_maintenance'] = enabled
        
        if enabled:
            self.maintenance_data['closed_at'] = datetime.now().isoformat()
            self.maintenance_data['closed_by'] = {
                'id': user_id,
                'name': username
            }
            self.maintenance_data['reason'] = reason or "Đang bảo trì hệ thống"
            logger.warning(f"🔒 MAINTENANCE MODE ENABLED by {username}")
        else:
            self.maintenance_data['opened_at'] = datetime.now().isoformat()
            self.maintenance_data['opened_by'] = {
                'id': user_id,
                'name': username
            }
            logger.info(f"🔓 MAINTENANCE MODE DISABLED by {username}")
        
        self.save_maintenance_data()
    
    def register_commands(self):
        """Đăng ký các commands cho Maintenance"""
        
        @self.bot.command(name='close', aliases=['maintenance', 'lock'])
        async def close_bot(ctx, *, reason: str = None):
            """
            Đóng bot để bảo trì (Supreme Admin only)
            
            Usage: ;close [lý do]
            """
            try:
                # Kiểm tra quyền Supreme Admin
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể đóng bot!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra xem đã đóng chưa
                if self.is_maintenance_mode():
                    embed = discord.Embed(
                        title="⚠️ Bot đã đóng",
                        description="Bot đang trong chế độ bảo trì!",
                        color=discord.Color.orange()
                    )
                    
                    closed_by = self.maintenance_data.get('closed_by', {})
                    embed.add_field(
                        name="👤 Đóng bởi",
                        value=closed_by.get('name', 'Unknown'),
                        inline=True
                    )
                    
                    closed_at = self.maintenance_data.get('closed_at')
                    if closed_at:
                        embed.add_field(
                            name="⏰ Thời gian",
                            value=datetime.fromisoformat(closed_at).strftime("%d/%m/%Y %H:%M:%S"),
                            inline=True
                        )
                    
                    reason_text = self.maintenance_data.get('reason', 'Không có lý do')
                    embed.add_field(
                        name="📝 Lý do",
                        value=reason_text,
                        inline=False
                    )
                    
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Đóng bot
                reason_text = reason or "Đang bảo trì hệ thống"
                self.set_maintenance(True, ctx.author.id, ctx.author.display_name, reason_text)
                
                # Tạo embed thông báo
                embed = discord.Embed(
                    title="🔒 Bot đã đóng",
                    description="Bot đã chuyển sang chế độ bảo trì!",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 Đóng bởi",
                    value=ctx.author.display_name,
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Thời gian",
                    value=datetime.now().strftime("%H:%M:%S"),
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Lý do",
                    value=reason_text,
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Mở lại bot",
                    value="Sử dụng ;` để mở lại bot",
                    inline=False
                )
                
                embed.set_footer(text="Tất cả lệnh đã bị tắt • Chỉ Supreme Admin có thể mở lại")
                
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.warning(f"Bot closed by {ctx.author.display_name} ({ctx.author.id}): {reason_text}")
                
            except Exception as e:
                logger.error(f"Lỗi trong close command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {e}", mention_author=True)
        
        @self.bot.command(name='open', aliases=['unmaintenance', 'unlock'])
        async def open_bot(ctx):
            """
            Mở lại bot sau khi bảo trì (Supreme Admin only)
            
            Usage: ;open
            """
            try:
                # Kiểm tra quyền Supreme Admin
                if not self.bot_instance.is_supreme_admin(ctx.author.id):
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Chỉ Supreme Admin mới có thể mở bot!",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Kiểm tra xem đã mở chưa
                if not self.is_maintenance_mode():
                    embed = discord.Embed(
                        title="✅ Bot đang hoạt động",
                        description="Bot không trong chế độ bảo trì!",
                        color=discord.Color.green()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    return
                
                # Lấy thông tin trước khi mở
                closed_by = self.maintenance_data.get('closed_by', {})
                closed_at = self.maintenance_data.get('closed_at')
                reason = self.maintenance_data.get('reason', 'Không có lý do')
                
                # Mở bot
                self.set_maintenance(False, ctx.author.id, ctx.author.display_name)
                
                # Tạo embed thông báo
                embed = discord.Embed(
                    title="🔓 Bot đã mở",
                    description="Bot đã hoạt động trở lại bình thường!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 Mở bởi",
                    value=ctx.author.display_name,
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Thời gian",
                    value=datetime.now().strftime("%H:%M:%S"),
                    inline=True
                )
                
                # Thông tin lần đóng trước
                if closed_by:
                    embed.add_field(
                        name="📋 Lần đóng trước",
                        value=f"**Bởi:** {closed_by.get('name', 'Unknown')}\n"
                              f"**Lý do:** {reason}",
                        inline=False
                    )
                
                if closed_at:
                    duration = datetime.now() - datetime.fromisoformat(closed_at)
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    
                    embed.add_field(
                        name="⏱️ Thời gian bảo trì",
                        value=f"{hours} giờ {minutes} phút",
                        inline=False
                    )
                
                embed.set_footer(text="Tất cả lệnh đã được kích hoạt • Bot sẵn sàng hoạt động")
                
                await ctx.reply(embed=embed, mention_author=True)
                
                logger.info(f"Bot opened by {ctx.author.display_name} ({ctx.author.id})")
                
            except Exception as e:
                logger.error(f"Lỗi trong open command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {e}", mention_author=True)
        
        @self.bot.command(name='maintenancestatus', aliases=['mstatus'])
        async def maintenance_status(ctx):
            """
            Xem trạng thái bảo trì của bot
            
            Usage: ;maintenancestatus
            """
            try:
                is_maintenance = self.is_maintenance_mode()
                
                if is_maintenance:
                    embed = discord.Embed(
                        title="🔒 Bot đang bảo trì",
                        description="Bot hiện đang trong chế độ bảo trì",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    
                    closed_by = self.maintenance_data.get('closed_by', {})
                    embed.add_field(
                        name="👤 Đóng bởi",
                        value=closed_by.get('name', 'Unknown'),
                        inline=True
                    )
                    
                    closed_at = self.maintenance_data.get('closed_at')
                    if closed_at:
                        closed_time = datetime.fromisoformat(closed_at)
                        embed.add_field(
                            name="⏰ Thời điểm đóng",
                            value=closed_time.strftime("%d/%m/%Y %H:%M:%S"),
                            inline=True
                        )
                        
                        duration = datetime.now() - closed_time
                        hours = int(duration.total_seconds() // 3600)
                        minutes = int((duration.total_seconds() % 3600) // 60)
                        
                        embed.add_field(
                            name="⏱️ Thời gian đã đóng",
                            value=f"{hours} giờ {minutes} phút",
                            inline=True
                        )
                    
                    reason = self.maintenance_data.get('reason', 'Không có lý do')
                    embed.add_field(
                        name="📝 Lý do",
                        value=reason,
                        inline=False
                    )
                    
                else:
                    embed = discord.Embed(
                        title="✅ Bot đang hoạt động",
                        description="Bot đang hoạt động bình thường",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    opened_by = self.maintenance_data.get('opened_by', {})
                    if opened_by:
                        embed.add_field(
                            name="👤 Mở gần nhất bởi",
                            value=opened_by.get('name', 'Unknown'),
                            inline=True
                        )
                    
                    opened_at = self.maintenance_data.get('opened_at')
                    if opened_at:
                        embed.add_field(
                            name="⏰ Thời điểm mở",
                            value=datetime.fromisoformat(opened_at).strftime("%d/%m/%Y %H:%M:%S"),
                            inline=True
                        )
                
                await ctx.reply(embed=embed, mention_author=True)
                
            except Exception as e:
                logger.error(f"Lỗi trong maintenancestatus command: {e}")
                await ctx.reply(f"❌ Có lỗi xảy ra: {e}", mention_author=True)
        
        logger.info("Đã đăng ký Maintenance commands: close, open, maintenancestatus")
