"""
Mute và Unmute commands
"""
import discord
from discord.ext import commands
import logging
import re
from datetime import datetime, timedelta
from .base import BaseCommand

logger = logging.getLogger(__name__)

class MuteCommands(BaseCommand):
    """Class chứa các commands liên quan đến mute"""
    
    def register_commands(self):
        """Register mute and unmute commands"""
        
        @self.bot.command(name='mute', aliases=['timeout'])
        async def mute_user(ctx, member: discord.Member, duration: str, *, reason: str = "Không có lý do"):
            """
            Mute (timeout) một user với thời gian tùy chỉnh
            
            Usage: 
                ;mute @user 10m Spam tin nhắn
                ;mute @user 1h30m Vi phạm quy tắc
                ;mute @user 2d Hành vi không phù hợp
            
            Định dạng thời gian:
                s/sec/seconds - giây
                m/min/minutes - phút  
                h/hour/hours - giờ
                d/day/days - ngày
                w/week/weeks - tuần
            
            Ví dụ: 30s, 5m, 1h, 2d, 1w, 1h30m, 2d12h
            """
            await self.execute_with_rate_limit(ctx, self._mute_user_impl, ctx, member, duration, reason)
        
        @self.bot.command(name='unmute', aliases=['untimeout'])
        async def unmute_user(ctx, member: discord.Member):
            """
            Remove timeout của một user với rate limiting
            
            Usage: ;unmute @user hoặc ;untimeout @user
            """
            # Sử dụng rate limiting cho command này
            await self.execute_with_rate_limit(ctx, self._unmute_user_impl, ctx, member)
        
        @self.bot.command(name='muteinfo', aliases=['timeoutinfo'])
        async def mute_info(ctx, member: discord.Member = None):
            """
            Xem thông tin mute của một user hoặc tất cả users bị mute
            
            Usage: 
                ;muteinfo - Xem tất cả users bị mute
                ;muteinfo @user - Xem thông tin mute của user cụ thể
            """
            await self.execute_with_rate_limit(ctx, self._mute_info_impl, ctx, member)
    
    def _parse_duration(self, duration_str: str) -> timedelta:
        """
        Parse duration string thành timedelta object
        
        Args:
            duration_str: String thời gian như "1h30m", "2d", "30s"
            
        Returns:
            timedelta: Thời gian đã parse
            
        Raises:
            ValueError: Nếu format không hợp lệ
        """
        # Regex pattern để match các định dạng thời gian
        pattern = r'(\d+)\s*(s|sec|seconds?|m|min|minutes?|h|hour|hours?|d|day|days?|w|week|weeks?)'
        matches = re.findall(pattern, duration_str.lower())
        
        if not matches:
            raise ValueError("Định dạng thời gian không hợp lệ")
        
        total_seconds = 0
        
        for value, unit in matches:
            value = int(value)
            
            # Convert to seconds
            if unit in ['s', 'sec', 'second', 'seconds']:
                total_seconds += value
            elif unit in ['m', 'min', 'minute', 'minutes']:
                total_seconds += value * 60
            elif unit in ['h', 'hour', 'hours']:
                total_seconds += value * 3600
            elif unit in ['d', 'day', 'days']:
                total_seconds += value * 86400
            elif unit in ['w', 'week', 'weeks']:
                total_seconds += value * 604800
        
        if total_seconds <= 0:
            raise ValueError("Thời gian phải lớn hơn 0")
        
        # Discord timeout limit là 28 ngày
        max_seconds = 28 * 24 * 60 * 60  # 28 days
        if total_seconds > max_seconds:
            raise ValueError("Thời gian mute tối đa là 28 ngày")
        
        return timedelta(seconds=total_seconds)
    
    def _format_duration(self, td: timedelta) -> str:
        """
        Format timedelta thành string dễ đọc
        
        Args:
            td: timedelta object
            
        Returns:
            str: String thời gian đã format
        """
        total_seconds = int(td.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} ngày")
        if hours > 0:
            parts.append(f"{hours} giờ")
        if minutes > 0:
            parts.append(f"{minutes} phút")
        if seconds > 0 and not parts:  # Chỉ hiển thị giây nếu không có đơn vị lớn hơn
            parts.append(f"{seconds} giây")
        
        return " ".join(parts) if parts else "0 giây"
    
    async def _mute_user_impl(self, ctx, member: discord.Member, duration: str, reason: str):
        """
        Implementation thực tế của mute command
        """
        # Kiểm tra quyền sử dụng dynamic permission system
        if hasattr(self.bot_instance, 'permission_manager'):
            has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'mute')
            if not has_permission:
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        else:
            # Fallback: Kiểm tra quyền admin nếu không có permission system
            if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        
        # Kiểm tra không thể mute chính mình
        if member == ctx.author:
            await ctx.reply(f"{ctx.author.mention} ❌ Bạn không thể mute chính mình!", mention_author=True)
            return
        
        # Kiểm tra không thể mute bot
        if member.bot:
            await ctx.reply(f"{ctx.author.mention} ❌ Không thể mute bot!", mention_author=True)
            return
        
        # Kiểm tra hierarchy - không thể mute người có role cao hơn
        if ctx.author != ctx.guild.owner and member.top_role >= ctx.author.top_role:
            await ctx.reply(f"{ctx.author.mention} ❌ Bạn không thể mute người có role cao hơn hoặc bằng bạn!", mention_author=True)
            return
        
        try:
            # Parse duration
            duration_td = self._parse_duration(duration)
            duration_formatted = self._format_duration(duration_td)
            
            # Kiểm tra user đã bị mute chưa
            if member.timed_out_until and member.timed_out_until > datetime.now(member.timed_out_until.tzinfo):
                await ctx.reply(f"{ctx.author.mention} ❌ {member.mention} đã bị mute rồi!", mention_author=True)
                return
            
            # Thực hiện mute
            await member.timeout(duration_td, reason=f"Muted by {ctx.author}: {reason}")
            
            # Tạo embed thông báo
            embed = discord.Embed(
                title="🔇 Đã mute user thành công",
                description=f"{member.mention} đã bị mute bởi {ctx.author.mention}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="⏰ Thời gian mute",
                value=duration_formatted,
                inline=True
            )
            
            embed.add_field(
                name="📝 Lý do",
                value=reason,
                inline=True
            )
            
            embed.add_field(
                name="🕐 Hết hạn lúc",
                value=f"<t:{int((datetime.now() + duration_td).timestamp())}:F>",
                inline=False
            )
            
            embed.set_footer(text=f"Muted bởi {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            
            await ctx.reply(embed=embed, mention_author=True)
            
            # Gửi DM cho user bị mute
            try:
                dm_embed = discord.Embed(
                    title="🔇 Bạn đã bị mute",
                    description=f"Bạn đã bị mute trong server **{ctx.guild.name}**",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                dm_embed.add_field(
                    name="⏰ Thời gian mute",
                    value=duration_formatted,
                    inline=True
                )
                
                dm_embed.add_field(
                    name="📝 Lý do",
                    value=reason,
                    inline=True
                )
                
                dm_embed.add_field(
                    name="🕐 Hết hạn lúc",
                    value=f"<t:{int((datetime.now() + duration_td).timestamp())}:F>",
                    inline=False
                )
                
                dm_embed.add_field(
                    name="⚠️ Lưu ý",
                    value="Trong thời gian mute, bạn không thể gửi tin nhắn hoặc tham gia voice chat.",
                    inline=False
                )
                
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                # Không thể gửi DM, bỏ qua
                pass
            
            logger.info(f"User {member} ({member.id}) đã bị mute {duration_formatted} bởi {ctx.author} ({ctx.author.id}) - Lý do: {reason}")
            
        except ValueError as e:
            await ctx.reply(f"{ctx.author.mention} ❌ {str(e)}", mention_author=True)
        except discord.Forbidden:
            await ctx.reply(f"{ctx.author.mention} ❌ Không có quyền mute user này!", mention_author=True)
        except discord.HTTPException as e:
            await ctx.reply(f"{ctx.author.mention} ❌ Lỗi HTTP: {str(e)[:100]}", mention_author=True)
        except Exception as e:
            await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra: {str(e)[:100]}", mention_author=True)
            logger.error(f"Lỗi khi mute user {member}: {e}")
    
    async def _unmute_user_impl(self, ctx, member: discord.Member):
        """
        Implementation thực tế của unmute command sử dụng remove timeout
        """
        # Kiểm tra quyền sử dụng dynamic permission system
        if hasattr(self.bot_instance, 'permission_manager'):
            has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'unmute')
            if not has_permission:
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        else:
            # Fallback: Kiểm tra quyền admin nếu không có permission system
            if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        
        try:
            from datetime import datetime
            
            # Kiểm tra user có bị timeout không
            if not member.timed_out_until or member.timed_out_until <= datetime.now(member.timed_out_until.tzinfo):
                await ctx.reply(f"{ctx.author.mention} ❌ {member.mention} không bị timeout!", mention_author=True)
                return
            
            # Remove timeout
            await member.timeout(None, reason=f"Timeout removed by {ctx.author}")
            
            embed = discord.Embed(
                title="🔊 Đã remove timeout thành công",
                description=f"{ctx.author.mention} đã remove timeout cho {member.mention}",
                color=discord.Color.green()
            )
            embed.add_field(
                name="ℹ️ Thông tin", 
                value="User có thể chat và tương tác bình thường trở lại", 
                inline=False
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"User {member} ({member.id}) đã được remove timeout bởi {ctx.author} ({ctx.author.id})")
            
        except discord.Forbidden:
            await ctx.reply(f"{ctx.author.mention} ❌ Không có quyền remove timeout user!", mention_author=True)
        except discord.HTTPException as e:
            await ctx.reply(f"{ctx.author.mention} ❌ Lỗi HTTP: {str(e)[:50]}", mention_author=True)
        except Exception as e:
            await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra: {str(e)}", mention_author=True)
            logger.error(f"Lỗi khi remove timeout user {member}: {e}")
    
    async def _mute_info_impl(self, ctx, member: discord.Member = None):
        """
        Implementation thực tế của muteinfo command
        """
        # Kiểm tra quyền sử dụng dynamic permission system
        if hasattr(self.bot_instance, 'permission_manager'):
            has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'muteinfo')
            if not has_permission:
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        else:
            # Fallback: Kiểm tra quyền admin nếu không có permission system
            if not self.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                await ctx.reply(f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", mention_author=True)
                return
        
        try:
            if member:
                # Xem thông tin mute của user cụ thể
                if not member.timed_out_until or member.timed_out_until <= datetime.now(member.timed_out_until.tzinfo):
                    await ctx.reply(f"{ctx.author.mention} ℹ️ {member.mention} hiện không bị mute!", mention_author=True)
                    return
                
                # Tính thời gian còn lại
                remaining_time = member.timed_out_until - datetime.now(member.timed_out_until.tzinfo)
                remaining_formatted = self._format_duration(remaining_time)
                
                embed = discord.Embed(
                    title="🔇 Thông tin Mute",
                    description=f"Thông tin mute của {member.mention}",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 User",
                    value=f"{member.mention}\n({member.display_name})",
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Thời gian còn lại",
                    value=remaining_formatted,
                    inline=True
                )
                
                embed.add_field(
                    name="🕐 Hết hạn lúc",
                    value=f"<t:{int(member.timed_out_until.timestamp())}:F>",
                    inline=False
                )
                
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                
                await ctx.reply(embed=embed, mention_author=True)
                
            else:
                # Xem tất cả users bị mute trong server
                muted_members = []
                current_time = datetime.now()
                
                for member in ctx.guild.members:
                    if member.timed_out_until and member.timed_out_until > current_time.replace(tzinfo=member.timed_out_until.tzinfo):
                        remaining_time = member.timed_out_until - current_time.replace(tzinfo=member.timed_out_until.tzinfo)
                        remaining_formatted = self._format_duration(remaining_time)
                        muted_members.append({
                            'member': member,
                            'remaining': remaining_formatted,
                            'expires_at': member.timed_out_until
                        })
                
                if not muted_members:
                    await ctx.reply(f"{ctx.author.mention} ℹ️ Hiện không có user nào bị mute trong server!", mention_author=True)
                    return
                
                # Sắp xếp theo thời gian hết hạn
                muted_members.sort(key=lambda x: x['expires_at'])
                
                embed = discord.Embed(
                    title="🔇 Danh sách Users bị Mute",
                    description=f"Có **{len(muted_members)}** user đang bị mute trong server",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                # Hiển thị tối đa 10 users để tránh embed quá dài
                display_count = min(len(muted_members), 10)
                
                for i, muted in enumerate(muted_members[:display_count]):
                    member = muted['member']
                    remaining = muted['remaining']
                    expires_timestamp = int(muted['expires_at'].timestamp())
                    
                    embed.add_field(
                        name=f"👤 {member.display_name}",
                        value=f"Còn lại: **{remaining}**\nHết hạn: <t:{expires_timestamp}:R>",
                        inline=True
                    )
                
                if len(muted_members) > 10:
                    embed.add_field(
                        name="➕ Và nhiều hơn nữa...",
                        value=f"Còn **{len(muted_members) - 10}** user khác bị mute",
                        inline=False
                    )
                
                embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                
                await ctx.reply(embed=embed, mention_author=True)
                
        except Exception as e:
            await ctx.reply(f"{ctx.author.mention} ❌ Có lỗi xảy ra: {str(e)[:100]}", mention_author=True)
            logger.error(f"Lỗi khi xem thông tin mute: {e}")
