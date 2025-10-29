"""
Feedback Commands for Discord Bot
Gửi feedback/báo lỗi về DM cho Supreme Admin
"""
import discord
from discord.ext import commands
import logging
import json
import os
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class FeedbackCommands(BaseCommand):
    """Class chứa lệnh feedback"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.feedback_file = "feedback_history.json"
        
    def register_commands(self):
        """Register feedback commands"""
        
        @self.bot.command(name='feedback', aliases=['report'])
        async def send_feedback(ctx, *, content=None):
            """Gửi feedback/báo lỗi về DM cho Supreme Admin"""
            if not content:
                embed = discord.Embed(
                    title="📝 Gửi Feedback",
                    description="Vui lòng cung cấp nội dung feedback!\n\n**Cách sử dụng:**\n; <nội dung>`",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="💡 Ví dụ",
                    value=(
                        "; Bot bị lỗi khi dùng lệnh play`\n"
                        "; Đề xuất thêm lệnh mute tạm thời`\n"
                        "; Cảm ơn admin đã tạo bot tuyệt vời!`"
                    ),
                    inline=False
                )
                embed.add_field(
                    name="📋 Loại feedback",
                    value="• Báo lỗi (Bug report)\n• Đề xuất tính năng\n• Góp ý cải thiện\n• Lời cảm ơn",
                    inline=False
                )
                embed.set_footer(text="Feedback sẽ được gửi trực tiếp đến Supreme Admin")
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Lấy thông tin Supreme Admin
            supreme_admin_id = await self._get_supreme_admin_id()
            if not supreme_admin_id:
                embed = discord.Embed(
                    title="❌ Không tìm thấy Supreme Admin",
                    description="Hiện tại chưa có Supreme Admin được thiết lập!\n\nVui lòng liên hệ admin server để thiết lập.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Lấy Supreme Admin user
            try:
                supreme_admin = await self.bot.fetch_user(supreme_admin_id)
            except discord.NotFound:
                embed = discord.Embed(
                    title="❌ Không thể tìm thấy Supreme Admin",
                    description="Supreme Admin ID không hợp lệ hoặc user không tồn tại!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            except Exception as e:
                logger.error(f"Error fetching supreme admin: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi hệ thống",
                    description="Không thể kết nối đến Supreme Admin. Vui lòng thử lại sau!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Tạo embed feedback để gửi cho Supreme Admin
            feedback_embed = discord.Embed(
                title="📝 Feedback từ User",
                description=content,
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            # Thông tin người gửi
            feedback_embed.add_field(
                name="👤 Người gửi",
                value=f"{ctx.author.mention} ({ctx.author})",
                inline=True
            )
            feedback_embed.add_field(
                name="🆔 User ID",
                value=str(ctx.author.id),
                inline=True
            )
            feedback_embed.add_field(
                name="📅 Thời gian",
                value=f"<t:{int(datetime.now().timestamp())}:F>",
                inline=True
            )
            
            # Thông tin server
            feedback_embed.add_field(
                name="🏠 Server",
                value=f"{ctx.guild.name} ({ctx.guild.id})",
                inline=True
            )
            feedback_embed.add_field(
                name="📢 Channel",
                value=f"{ctx.channel.mention} ({ctx.channel.name})",
                inline=True
            )
            feedback_embed.add_field(
                name="🔗 Jump Link",
                value=f"[Đến tin nhắn]({ctx.message.jump_url})",
                inline=True
            )
            
            # Avatar người gửi
            if ctx.author.avatar:
                feedback_embed.set_thumbnail(url=ctx.author.avatar.url)
            
            feedback_embed.set_footer(
                text=f"Feedback ID: {ctx.message.id}",
                icon_url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None
            )
            
            # Gửi DM cho Supreme Admin
            try:
                await supreme_admin.send(embed=feedback_embed)
                
                # Lưu feedback vào history
                await self._save_feedback_history({
                    'id': str(ctx.message.id),
                    'user_id': str(ctx.author.id),
                    'username': str(ctx.author),
                    'content': content,
                    'server_id': str(ctx.guild.id),
                    'server_name': ctx.guild.name,
                    'channel_id': str(ctx.channel.id),
                    'channel_name': ctx.channel.name,
                    'timestamp': datetime.now().isoformat(),
                    'jump_url': ctx.message.jump_url
                })
                
                # Thông báo thành công cho user
                success_embed = discord.Embed(
                    title="✅ Feedback đã được gửi!",
                    description=f"Feedback của bạn đã được gửi thành công đến **{supreme_admin.display_name}**!",
                    color=discord.Color.green()
                )
                success_embed.add_field(
                    name="📝 Nội dung",
                    value=content[:100] + ("..." if len(content) > 100 else ""),
                    inline=False
                )
                success_embed.add_field(
                    name="⏰ Thời gian gửi",
                    value=f"<t:{int(datetime.now().timestamp())}:R>",
                    inline=True
                )
                success_embed.add_field(
                    name="📋 Feedback ID",
                    value=f"`{ctx.message.id}`",
                    inline=True
                )
                success_embed.set_footer(text="Cảm ơn bạn đã góp ý để cải thiện bot!")
                
                await ctx.reply(embed=success_embed, mention_author=True)
                logger.info(f"Feedback sent from {ctx.author} to Supreme Admin: {content[:50]}...")
                
            except discord.Forbidden:
                embed = discord.Embed(
                    title="❌ Không thể gửi DM",
                    description=f"Supreme Admin **{supreme_admin.display_name}** đã tắt DM hoặc chặn bot!\n\nVui lòng liên hệ admin qua cách khác.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                logger.warning(f"Cannot send DM to Supreme Admin {supreme_admin}: DM disabled or blocked")
                
            except Exception as e:
                logger.error(f"Error sending feedback DM: {e}")
                embed = discord.Embed(
                    title="❌ Lỗi gửi feedback",
                    description="Có lỗi xảy ra khi gửi feedback. Vui lòng thử lại sau!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='feedbackstats', aliases=['fbstats'])
        async def feedback_stats(ctx):
            """Xem thống kê feedback (chỉ Supreme Admin)"""
            # Kiểm tra quyền Supreme Admin
            supreme_admin_id = await self._get_supreme_admin_id()
            if not supreme_admin_id or ctx.author.id != supreme_admin_id:
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Supreme Admin mới có thể xem thống kê feedback!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Đọc feedback history
            feedback_history = await self._load_feedback_history()
            
            if not feedback_history:
                embed = discord.Embed(
                    title="📊 Thống kê Feedback",
                    description="Chưa có feedback nào được gửi!",
                    color=discord.Color.blue()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Thống kê
            total_feedback = len(feedback_history)
            unique_users = len(set(f['user_id'] for f in feedback_history))
            recent_feedback = [f for f in feedback_history if 
                             (datetime.now() - datetime.fromisoformat(f['timestamp'])).days <= 7]
            
            embed = discord.Embed(
                title="📊 Thống kê Feedback",
                description="Tổng quan về feedback từ users",
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="📝 Tổng feedback",
                value=f"{total_feedback} feedback",
                inline=True
            )
            embed.add_field(
                name="👥 Unique users",
                value=f"{unique_users} người",
                inline=True
            )
            embed.add_field(
                name="📅 Tuần này",
                value=f"{len(recent_feedback)} feedback",
                inline=True
            )
            
            # Top 5 feedback gần nhất
            if feedback_history:
                recent_list = ""
                for i, feedback in enumerate(sorted(feedback_history, 
                                                  key=lambda x: x['timestamp'], reverse=True)[:5]):
                    timestamp = datetime.fromisoformat(feedback['timestamp'])
                    recent_list += f"`{i+1}.` **{feedback['username']}**\n"
                    recent_list += f"    {feedback['content'][:50]}{'...' if len(feedback['content']) > 50 else ''}\n"
                    recent_list += f"    <t:{int(timestamp.timestamp())}:R>\n\n"
                
                embed.add_field(
                    name="📋 Feedback gần nhất",
                    value=recent_list,
                    inline=False
                )
            
            embed.set_footer(text=f"Dữ liệu từ {self.feedback_file}")
            await ctx.reply(embed=embed, mention_author=True)
    
    async def _get_supreme_admin_id(self):
        """Lấy Supreme Admin ID từ file config"""
        try:
            if os.path.exists("supreme_admin.json"):
                with open("supreme_admin.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("supreme_admin_id")
        except Exception as e:
            logger.error(f"Error reading supreme admin config: {e}")
        return None
    
    async def _save_feedback_history(self, feedback_data):
        """Lưu feedback vào history file"""
        try:
            history = await self._load_feedback_history()
            history.append(feedback_data)
            
            # Giữ tối đa 1000 feedback gần nhất
            if len(history) > 1000:
                history = history[-1000:]
            
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving feedback history: {e}")
    
    async def _load_feedback_history(self):
        """Đọc feedback history từ file"""
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading feedback history: {e}")
        return []
