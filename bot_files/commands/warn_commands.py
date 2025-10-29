"""
Warn và Warnings commands
"""
import discord
from discord.ext import commands
from datetime import datetime
import logging
import json
import os
from .base import BaseCommand

logger = logging.getLogger(__name__)

class WarnCommands(BaseCommand):
    """Class chứa các commands liên quan đến warn"""
    
    def load_amen_config(self):
        """Load cấu hình từ amen.json"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'amen.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("Không tìm thấy file amen.json")
                return None
        except Exception as e:
            logger.error(f"Lỗi khi đọc amen.json: {e}")
            return None
    
    async def send_mute_notification(self, ctx, member: discord.Member, reason: str, duration: str = "1 phút"):
        """Gửi thông báo DM khi có người bị mute"""
        try:
            amen_config = self.load_amen_config()
            if not amen_config or not amen_config.get('enabled', False):
                return
            
            notification_user_id = amen_config.get('notification_user_id')
            if not notification_user_id or notification_user_id == "YOUR_USER_ID_HERE":
                logger.warning("notification_user_id chưa được cấu hình trong amen.json")
                return
            
            # Lấy user để gửi DM
            try:
                notification_user = await self.bot.fetch_user(int(notification_user_id))
            except (ValueError, discord.NotFound):
                logger.error(f"Không tìm thấy user với ID: {notification_user_id}")
                return
            
            # Lấy lịch sử warnings của user
            user_warnings = self.bot_instance.get_warnings(member.id)
            warning_history = ""
            
            if user_warnings:
                warning_history = "\n\n**📋 Lịch sử 3 warnings:**\n"
                for i, warning in enumerate(user_warnings[-3:], 1):  # Lấy 3 warning cuối
                    warning_time = warning.get('timestamp', 'Không rõ thời gian')
                    warning_reason = warning.get('reason', 'Không có lý do')
                    warning_mod = warning.get('moderator', 'Không rõ mod')
                    
                    # Format timestamp nếu có
                    if isinstance(warning_time, str) and warning_time != 'Không rõ thời gian':
                        try:
                            # Chuyển timestamp thành Discord timestamp
                            from datetime import datetime
                            dt = datetime.fromisoformat(warning_time.replace('Z', '+00:00'))
                            timestamp_formatted = f"<t:{int(dt.timestamp())}:R>"
                        except:
                            timestamp_formatted = warning_time
                    else:
                        timestamp_formatted = warning_time
                    
                    warning_history += f"**{i}.** {warning_reason}\n   *Mod: {warning_mod} • {timestamp_formatted}*\n"
            
            # Tạo tin nhắn từ template
            message_template = amen_config.get('message_template', 
                "🔇 **Mute Notification**\n\n**User:** {user_mention} ({user_name})\n**Server:** {server_name}\n**Reason:** {reason}\n**Duration:** {duration}\n**Moderator:** {moderator_mention}\n**Time:** <t:{timestamp}:F>")
            
            timestamp = int(datetime.now().timestamp())
            
            message = message_template.format(
                user_mention=member.mention,
                user_name=f"{member.display_name} ({member.name})",
                server_name=ctx.guild.name,
                reason=reason,
                duration=duration,
                moderator_mention=ctx.author.mention,
                timestamp=timestamp
            )
            
            # Thêm lịch sử warnings vào tin nhắn
            full_message = message + warning_history
            
            # Kiểm tra độ dài tin nhắn (Discord limit 2000 chars)
            if len(full_message) > 2000:
                # Rút gọn nếu quá dài
                available_space = 2000 - len(message) - 50  # Để lại chỗ cho "..."
                if available_space > 100:
                    warning_history = warning_history[:available_space] + "\n*...quá dài, đã rút gọn*"
                    full_message = message + warning_history
                else:
                    full_message = message  # Chỉ gửi thông tin cơ bản
            
            # Gửi DM
            await notification_user.send(full_message)
            logger.info(f"Đã gửi thông báo mute đến {notification_user.name} ({notification_user_id})")
            
        except discord.Forbidden:
            logger.error(f"Không thể gửi DM đến user {notification_user_id} (DM bị tắt)")
        except Exception as e:
            logger.error(f"Lỗi khi gửi thông báo mute: {e}")
    
    def register_commands(self):
        """Register warn và warnings commands"""
        
        @self.bot.command(name='warn')
        async def warn_user(ctx, member: discord.Member, *, reason: str = "Không có lý do cụ thể"):
            """
            Cảnh báo một user và gửi DM với rate limiting
            
            Usage: ;warn @user <lý do>
            """
            # Sử dụng rate limiting cho command này
            await self.execute_with_rate_limit(ctx, self._warn_user_impl, ctx, member, reason)
        
        @self.bot.command(name='warnings')
        async def check_warnings(ctx, member: discord.Member = None):
            """
            Kiểm tra số lượng warnings của user với rate limiting
            
            Usage: ;warnings [@user]
            """
            # Sử dụng rate limiting cho command này
            await self.execute_with_rate_limit(ctx, self._check_warnings_impl, ctx, member)
        
        @self.bot.command(name='amenconfig')
        async def amen_config_command(ctx, action: str = None, *, value: str = None):
            """
            Quản lý cấu hình thông báo mute trong amen.json (Admin only)
            
            Usage: 
            ;amenconfig status - Xem trạng thái hiện tại
            ;amenconfig set <user_id> - Đặt user ID nhận thông báo
            ;amenconfig enable/disable - Bật/tắt thông báo
            """
            # Kiểm tra quyền sử dụng dynamic permission system
            if hasattr(self.bot_instance, 'permission_manager'):
                has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'amenconfig')
                if not has_permission:
                    await ctx.reply("❌ Bạn không có quyền sử dụng lệnh này.", mention_author=True)
                    return
            else:
                # Fallback: Kiểm tra quyền admin nếu không có permission system
                if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                    await ctx.reply("❌ Bạn không có quyền sử dụng lệnh này.", mention_author=True)
                    return
            
            amen_config = self.load_amen_config()
            
            if not action or action.lower() == "status":
                # Hiển thị trạng thái hiện tại
                if not amen_config:
                    await ctx.reply("❌ Không tìm thấy file amen.json", mention_author=True)
                    return
                
                embed = discord.Embed(
                    title="📋 Cấu hình Amen Notification",
                    color=discord.Color.blue()
                )
                
                user_id = amen_config.get('notification_user_id', 'Chưa cấu hình')
                enabled = amen_config.get('enabled', False)
                
                embed.add_field(
                    name="🆔 User ID",
                    value=f"`{user_id}`",
                    inline=True
                )
                
                embed.add_field(
                    name="🔔 Trạng thái",
                    value="🟢 Enabled" if enabled else "🔴 Disabled",
                    inline=True
                )
                
                # Thử lấy thông tin user nếu có ID hợp lệ
                if user_id != 'Chưa cấu hình' and user_id != 'YOUR_USER_ID_HERE':
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        embed.add_field(
                            name="👤 User Info",
                            value=f"{user.display_name} ({user.name})",
                            inline=False
                        )
                    except:
                        embed.add_field(
                            name="⚠️ Warning",
                            value="User ID không hợp lệ hoặc không tìm thấy",
                            inline=False
                        )
                
                await ctx.reply(embed=embed, mention_author=True)
            
            elif action.lower() == "set" and value:
                # Đặt user ID
                try:
                    user_id = int(value)
                    # Kiểm tra user có tồn tại không
                    user = await self.bot.fetch_user(user_id)
                    
                    # Cập nhật config
                    if not amen_config:
                        amen_config = {"enabled": True, "notification_user_id": str(user_id)}
                    else:
                        amen_config['notification_user_id'] = str(user_id)
                    
                    # Lưu file
                    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'amen.json')
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(amen_config, f, indent=4, ensure_ascii=False)
                    
                    embed = discord.Embed(
                        title="✅ Đã cập nhật cấu hình",
                        description=f"User nhận thông báo: {user.display_name} ({user.name})\nID: `{user_id}`",
                        color=discord.Color.green()
                    )
                    await ctx.reply(embed=embed, mention_author=True)
                    
                except ValueError:
                    await ctx.reply("❌ User ID phải là số nguyên.", mention_author=True)
                except discord.NotFound:
                    await ctx.reply("❌ Không tìm thấy user với ID này.", mention_author=True)
                except Exception as e:
                    await ctx.reply(f"❌ Lỗi: {str(e)}", mention_author=True)
            
            elif action.lower() in ["enable", "disable"]:
                # Bật/tắt thông báo
                if not amen_config:
                    await ctx.reply("❌ Không tìm thấy file amen.json", mention_author=True)
                    return
                
                enabled = action.lower() == "enable"
                amen_config['enabled'] = enabled
                
                # Lưu file
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'amen.json')
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(amen_config, f, indent=4, ensure_ascii=False)
                
                status = "🟢 Enabled" if enabled else "🔴 Disabled"
                embed = discord.Embed(
                    title="✅ Đã cập nhật trạng thái",
                    description=f"Thông báo mute: {status}",
                    color=discord.Color.green() if enabled else discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
            
            else:
                await ctx.reply("❌ Sử dụng: ; status/set <user_id>/enable/disable`", mention_author=True)
    
    async def _warn_user_impl(self, ctx, member: discord.Member, reason: str):
        """
        Implementation thực tế của warn command
        """
        # Kiểm tra quyền sử dụng dynamic permission system
        if hasattr(self.bot_instance, 'permission_manager'):
            has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'warn')
            if not has_permission:
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        else:
            # Fallback: Kiểm tra quyền admin nếu không có permission system
            if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        
        # Không thể warn chính mình
        if member.id == ctx.author.id:
            await ctx.reply(f"{ctx.author.mention} ❌ Bạn không thể warn chính mình!", mention_author=True)
            return
        
        # Không thể warn bot
        if member.bot:
            await ctx.reply(f"{ctx.author.mention} ❌ Không thể warn bot!", mention_author=True)
            return
        
        try:
            # Thêm warning vào database
            warning_count = self.bot_instance.add_warning(
                user_id=member.id,
                reason=reason,
                warned_by=f"{ctx.author} ({ctx.author.id})"
            )
            
            # Tạo embed cho DM - màu sắc và nội dung dựa trên số warnings
            if warning_count >= 3:
                dm_color = discord.Color.red()
                dm_title = "🔇 Cảnh báo nghiêm trọng - Đã bị timeout"
                dm_description = f"Bạn đã nhận được cảnh báo thứ {warning_count} từ server **{ctx.guild.name}** và đã bị timeout."
            elif warning_count == 2:
                dm_color = discord.Color.orange()
                dm_title = "⚠️ Cảnh báo nghiêm trọng"
                dm_description = f"Bạn đã nhận được cảnh báo thứ {warning_count} từ server **{ctx.guild.name}**. Cảnh báo tiếp theo sẽ dẫn đến mute."
            else:
                dm_color = discord.Color.yellow()
                dm_title = "⚠️ Cảnh báo từ Server"
                dm_description = f"Bạn đã nhận được cảnh báo từ server **{ctx.guild.name}**"
            
            embed = discord.Embed(
                title=dm_title,
                description=dm_description,
                color=dm_color,
                timestamp=datetime.now()
            )
            embed.add_field(name="Lý do", value=reason, inline=False)
            embed.add_field(name="Được cảnh báo bởi", value=ctx.author.mention, inline=True)
            embed.add_field(name="Tổng số cảnh báo", value=f"{warning_count} lần", inline=True)
            
            if warning_count >= 3:
                embed.add_field(name="⚠️ Thông báo quan trọng", 
                              value="Bạn đã bị timeout 1 phút do vi phạm nhiều lần. Sẽ tự động hết timeout sau 1 phút.", 
                              inline=False)
            elif warning_count == 2:
                embed.add_field(name="⚠️ Cảnh báo cuối", 
                              value="Đây là cảnh báo cuối cùng. Vi phạm tiếp theo sẽ dẫn đến timeout.", 
                              inline=False)
            
            embed.set_footer(text=f"Server: {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            
            # Gửi DM cho user
            try:
                await member.send(embed=embed)
                dm_status = "✅ Đã gửi DM"
            except discord.Forbidden:
                dm_status = "❌ Không thể gửi DM (user đã tắt DM)"
            except Exception as e:
                dm_status = f"❌ Lỗi gửi DM: {str(e)[:50]}"
            
            # Timeout user nếu đạt 3 warnings
            timeout_status = "⚠️ Chưa đủ 3 warnings để timeout"
            if warning_count >= 3:
                timeout_status = await self._handle_auto_mute(ctx, member, reason)
            
            # Phản hồi trong channel với reply - màu sắc dựa trên số warnings
            if warning_count >= 3:
                embed_color = discord.Color.red()  # Đỏ - nghiêm trọng (đã timeout)
                title = "🔇 Đã cảnh báo và timeout"
            elif warning_count == 2:
                embed_color = discord.Color.orange()  # Cam - cảnh báo
                title = "⚠️ Cảnh báo nghiêm trọng"
            else:
                embed_color = discord.Color.yellow()  # Vàng - cảnh báo nhẹ
                title = "⚠️ Đã cảnh báo"
            
            response_embed = discord.Embed(
                title=title,
                description=f"{ctx.author.mention} đã cảnh báo {member.mention}",
                color=embed_color
            )
            response_embed.add_field(name="Lý do", value=reason, inline=False)
            response_embed.add_field(name="Tổng cảnh báo", value=f"{warning_count} lần", inline=True)
            response_embed.add_field(name="Trạng thái DM", value=dm_status, inline=True)
            response_embed.add_field(name="Trạng thái Timeout", value=timeout_status, inline=True)
            
            await ctx.reply(embed=response_embed, mention_author=True)
            
            # Log
            logger.info(
                f"User {member} ({member.id}) đã được warn bởi {ctx.author} ({ctx.author.id}). "
                f"Lý do: {reason}. Tổng warnings: {warning_count}"
            )
            
        except Exception as e:
            await ctx.send(f"❌ Có lỗi xảy ra: {str(e)}")
            logger.error(f"Lỗi khi warn user {member}: {e}")
    
    async def _handle_auto_mute(self, ctx, member: discord.Member, reason: str):
        """
        Xử lý auto-mute khi user đạt 3 warnings sử dụng Discord timeout
        
        Args:
            ctx: Discord context
            member: Member cần mute
            reason: Lý do warn
            
        Returns:
            str: Status message
        """
        try:
            from datetime import timedelta
            
            # Kiểm tra xem user đã bị timeout chưa
            if member.timed_out_until and member.timed_out_until > datetime.now(member.timed_out_until.tzinfo):
                return "ℹ️ User đã bị timeout từ trước"
            
            # Timeout user trong 1 phút sử dụng Discord timeout
            timeout_duration = timedelta(minutes=1)
            await member.timeout(
                timeout_duration, 
                reason=f"Auto-timeout after 3 warnings. Last warning by {ctx.author}: {reason}"
            )
            
            # Gửi thông báo DM đến user được cấu hình trong amen.json
            await self.send_mute_notification(ctx, member, reason, "1 phút")
            
            # Xóa tất cả warnings sau khi timeout (reset về 0)
            self.bot_instance.clear_user_warnings(member.id)
            logger.info(f"Đã xóa tất cả warnings của user {member} ({member.id}) sau khi timeout")
            
            return "🔇 Đã timeout user (1 phút) và reset warnings"
                
        except discord.Forbidden:
            return "❌ Không có quyền timeout user"
        except discord.HTTPException as e:
            return f"❌ Lỗi HTTP timeout: {str(e)[:30]}"
        except Exception as e:
            return f"❌ Lỗi timeout: {str(e)[:30]}"
    
    async def _check_warnings_impl(self, ctx, member: discord.Member = None):
        """
        Implementation thực tế của warnings command
        """
        # Nếu không mention ai thì kiểm tra chính mình
        if member is None:
            member = ctx.author
        
        # Kiểm tra quyền sử dụng dynamic permission system (admin/mod hoặc chính user đó)
        is_checking_self = (member.id == ctx.author.id)
        
        if not is_checking_self:
            # Chỉ check permission nếu không phải xem chính mình
            if hasattr(self.bot_instance, 'permission_manager'):
                has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'warnings')
                if not has_permission:
                    await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền xem warnings của user khác!", mention_author=True)
                    return
            else:
                # Fallback: Kiểm tra quyền admin nếu không có permission system
                if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                    await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền xem warnings của user khác!", mention_author=True)
                    return
        
        warnings_list = self.bot_instance.get_warnings(member.id)
        
        if not warnings_list:
            embed = discord.Embed(
                title="📋 Lịch sử cảnh báo",
                description=f"{member.mention} chưa có cảnh báo nào.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="📋 Lịch sử cảnh báo",
                description=f"{member.mention} có **{len(warnings_list)}** cảnh báo:",
                color=discord.Color.red()
            )
            
            for i, warning in enumerate(warnings_list[-5:], 1):  # Chỉ hiển thị 5 warnings gần nhất
                timestamp = datetime.fromisoformat(warning['timestamp']).strftime('%d/%m/%Y %H:%M')
                embed.add_field(
                    name=f"Cảnh báo #{len(warnings_list) - 5 + i}",
                    value=f"**Lý do:** {warning['reason']}\n**Bởi:** {warning['warned_by']}\n**Thời gian:** {timestamp}",
                    inline=False
                )
            
            if len(warnings_list) > 5:
                embed.set_footer(text=f"Hiển thị 5/{len(warnings_list)} cảnh báo gần nhất")
        
        await ctx.reply(embed=embed, mention_author=True)
