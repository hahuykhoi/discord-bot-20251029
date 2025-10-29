# -*- coding: utf-8 -*-
"""
Emoji Commands - Thêm emoji reaction vào tin nhắn
"""
import discord
from discord.ext import commands
import logging
import random
import asyncio
from .base import BaseCommand

logger = logging.getLogger(__name__)

class EmojiCommands(BaseCommand):
    """Class chứa các commands emoji"""
    
    def register_commands(self):
        """Register emoji commands"""
        
        @self.bot.command(name='emoji', aliases=['react'])
        async def add_emoji(ctx, message_id: int = None, count: int = 1):
            """
            Thêm custom emoji reaction ngẫu nhiên vào tin nhắn theo ID
            Chỉ sử dụng custom emoji của server hiện tại
            ⚡ KHÔNG CÓ RATE LIMIT!
            
            Usage: 
            ;emoji <message_id> [số_lượng]
            ;emoji 1234567890123456789 5
            ;emoji 1234567890123456789 10
            """
            # Bỏ rate limit - gọi trực tiếp implementation
            await self._add_emoji_impl(ctx, message_id, count)
    
    async def _add_emoji_impl(self, ctx, message_id: int, count: int = 1):
        """
        Implementation thực tế của emoji command
        """
        try:
            # Kiểm tra nếu không có message_id
            if message_id is None:
                error_embed = discord.Embed(
                    title="❌ Thiếu thông tin",
                    description="Vui lòng cung cấp ID tin nhắn cần thêm emoji reaction!",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Cách sử dụng",
                    value="; <message_id> [số_lượng]`\n**Ví dụ:** ; 1234567890123456789 5`",
                    inline=False
                )
                error_embed.add_field(
                    name="💡 Tham số",
                    value="• `message_id`: ID tin nhắn cần react\n• `số_lượng`: Số custom emoji muốn thêm (mặc định: 1)",
                    inline=False
                )
                error_embed.add_field(
                    name="💡 Cách lấy Message ID",
                    value=(
                        "1. Bật Developer Mode trong Discord\n"
                        "2. Click phải vào tin nhắn\n"
                        "3. Chọn 'Copy Message ID'"
                    ),
                    inline=False
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            # Lấy số emoji của server trước để validate - chỉ emoji available
            guild_emojis = [emoji for emoji in ctx.guild.emojis if emoji.available] if ctx.guild and ctx.guild.emojis else []
            max_emojis = len(guild_emojis)
            
            # Validate count parameter
            if count < 1:
                count = 1
            elif count > max_emojis and max_emojis > 0:  # Giới hạn theo số emoji của server
                error_embed = discord.Embed(
                    title="⚠️ Giới hạn số lượng",
                    description=f"Server chỉ có {max_emojis} custom emoji. Bạn đã nhập: {count}",
                    color=discord.Color.orange()
                )
                error_embed.add_field(
                    name="💡 Gợi ý",
                    value=f"Sử dụng số từ 1-{max_emojis} để thêm emoji reactions\n⚠️ **Discord limit**: Tối đa 20 reactions per message",
                    inline=False
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            # Sử dụng emoji đã lấy từ validation
            all_emojis = guild_emojis
            
            if not all_emojis:
                error_embed = discord.Embed(
                    title="❌ Server không có custom emoji",
                    description="Server này chưa có custom emoji nào để sử dụng!",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="💡 Giải pháp",
                    value=(
                        "• Server cần có custom emoji để sử dụng lệnh này\n"
                        "• Admin có thể thêm emoji trong Server Settings > Emoji\n"
                        "• Hoặc upload emoji mới từ file ảnh"
                    ),
                    inline=False
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            # Tìm tin nhắn theo ID trong channel hiện tại
            try:
                target_message = await ctx.channel.fetch_message(message_id)
            except discord.NotFound:
                # Thử tìm trong các channel khác của server
                target_message = None
                for channel in ctx.guild.text_channels:
                    if channel.permissions_for(ctx.guild.me).read_messages:
                        try:
                            target_message = await channel.fetch_message(message_id)
                            break
                        except (discord.NotFound, discord.Forbidden):
                            continue
                
                if not target_message:
                    error_embed = discord.Embed(
                        title="❌ Không tìm thấy tin nhắn",
                        description=f"Không tìm thấy tin nhắn với ID: `{message_id}`",
                        color=discord.Color.red()
                    )
                    error_embed.add_field(
                        name="Nguyên nhân có thể",
                        value=(
                            "• Tin nhắn không tồn tại\n"
                            "• Tin nhắn đã bị xóa\n"
                            "• Bot không có quyền truy cập channel chứa tin nhắn\n"
                            "• Message ID không chính xác"
                        ),
                        inline=False
                    )
                    await ctx.reply(embed=error_embed, mention_author=True)
                    return
            
            except discord.Forbidden:
                error_embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Bot không có quyền đọc tin nhắn trong channel này!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            # Filter emoji để chỉ lấy những emoji bot có thể sử dụng
            usable_emojis = []
            for emoji in all_emojis:
                # Kiểm tra emoji có available và bot có thể sử dụng
                if hasattr(emoji, 'available') and emoji.available:
                    # Kiểm tra bot có quyền sử dụng emoji này không
                    if emoji.guild_id == ctx.guild.id:  # Chỉ emoji của server hiện tại
                        usable_emojis.append(emoji)
            
            # Cập nhật all_emojis với emoji đã filter
            all_emojis = usable_emojis
            
            if not all_emojis:
                error_embed = discord.Embed(
                    title="❌ Không có emoji khả dụng",
                    description="Server không có custom emoji nào có thể sử dụng!",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="💡 Nguyên nhân có thể",
                    value=(
                        "• Tất cả emoji đã bị disable\n"
                        "• Bot không có quyền sử dụng emoji\n"
                        "• Emoji bị lỗi hoặc không khả dụng"
                    ),
                    inline=False
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                return
            
            # Chọn emoji ngẫu nhiên (không trùng lặp)
            selected_emojis = random.sample(all_emojis, min(count, len(all_emojis)))
            
            # Thêm reactions vào tin nhắn
            added_emojis = []
            failed_emojis = []
            
            try:
                # Thông báo bắt đầu process (nếu nhiều emoji)
                if count > 1:
                    processing_embed = discord.Embed(
                        title="🔄 Đang thêm emoji reactions...",
                        description=f"Đang thêm {count} emoji reactions vào tin nhắn...",
                        color=discord.Color.blue()
                    )
                    processing_msg = await ctx.reply(embed=processing_embed, mention_author=True)
                
                # Thêm từng emoji
                for emoji in selected_emojis:
                    try:
                        await target_message.add_reaction(emoji)
                        added_emojis.append(emoji)
                        
                        # Delay nhỏ để tránh rate limit Discord API
                        if len(selected_emojis) > 5:
                            await asyncio.sleep(0.2)
                            
                    except discord.HTTPException as e:
                        failed_emojis.append(emoji)
                        # Check if it's Discord's 20 reaction limit
                        if "30010" in str(e) or "Maximum number of reactions reached" in str(e):
                            logger.info(f"Discord 20-reaction limit reached at emoji {len(added_emojis) + 1}")
                            # Stop trying to add more emojis once we hit the limit
                            break
                        # Check if it's Unknown Emoji error
                        elif "10014" in str(e) or "Unknown Emoji" in str(e):
                            logger.warning(f"Unknown emoji (possibly from another server): {emoji}")
                        else:
                            logger.warning(f"Failed to add emoji {emoji}: {e}")
                        continue
                
                # Tạo display string cho emojis đã thêm
                emoji_displays = []
                for emoji in added_emojis[:10]:  # Hiển thị tối đa 10 emoji trong embed
                    if isinstance(emoji, str):
                        emoji_displays.append(str(emoji))
                    else:
                        emoji_displays.append(f"<:{emoji.name}:{emoji.id}>")
                
                # Thông báo thành công
                success_title = f"✅ Đã thêm {len(added_emojis)} emoji reaction{'s' if len(added_emojis) > 1 else ''}!"
                success_desc = f"Đã thêm {len(added_emojis)}/{count} emoji vào tin nhắn"
                
                if failed_emojis:
                    # Check if we hit Discord's 20 reaction limit
                    if len(added_emojis) >= 20:
                        success_desc += f"\n⚠️ **Discord limit**: Đã đạt giới hạn 20 reactions per message"
                        success_desc += f"\n❌ {len(failed_emojis)} emoji không thể thêm do giới hạn Discord"
                    else:
                        success_desc += f"\n⚠️ {len(failed_emojis)} emoji không thể thêm được"
                
                success_embed = discord.Embed(
                    title=success_title,
                    description=success_desc,
                    color=discord.Color.green()
                )
                success_embed.add_field(
                    name="📍 Tin nhắn",
                    value=f"[Đến tin nhắn]({target_message.jump_url})",
                    inline=True
                )
                success_embed.add_field(
                    name="🎯 Emoji đã thêm",
                    value=" ".join(emoji_displays) if emoji_displays else "Không có emoji nào được thêm",
                    inline=False
                )
                
                if len(added_emojis) > 10:
                    success_embed.add_field(
                        name="➕ Và nhiều hơn...",
                        value=f"Còn {len(added_emojis) - 10} emoji khác đã được thêm",
                        inline=False
                    )
                
                # Thông tin Discord limit
                discord_limit_info = ""
                if len(added_emojis) >= 20:
                    discord_limit_info = f"\n🚫 **Discord limit**: 20 reactions max per message"
                elif count > 20:
                    discord_limit_info = f"\n💡 **Lưu ý**: Discord giới hạn 20 reactions per message"
                
                success_embed.add_field(
                    name="📊 Thống kê",
                    value=(
                        f"**Channel:** {target_message.channel.mention}\n"
                        f"**Yêu cầu:** {count} emoji\n"
                        f"**Thành công:** {len(added_emojis)} emoji\n"
                        f"**Thất bại:** {len(failed_emojis)} emoji\n"
                        f"**Server emoji:** {len(all_emojis)} custom emoji\n"
                        f"⚡ **Không có rate limit!**"
                        f"{discord_limit_info}"
                    ),
                    inline=False
                )
                
                # Update hoặc reply với kết quả
                if count > 1 and 'processing_msg' in locals():
                    await processing_msg.edit(embed=success_embed)
                else:
                    await ctx.reply(embed=success_embed, mention_author=True)
                
                # Log activity
                logger.info(f"{len(added_emojis)} emojis added to message {message_id} by {ctx.author} ({ctx.author.id})")
                
            except discord.Forbidden:
                error_embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Bot không có quyền thêm reaction trong channel đó!",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Quyền cần thiết",
                    value="• Add Reactions\n• Read Message History\n• Use External Emojis (nếu dùng custom emoji)",
                    inline=False
                )
                await ctx.reply(embed=error_embed, mention_author=True)
                
            except discord.HTTPException as e:
                if "reaction" in str(e).lower():
                    error_embed = discord.Embed(
                        title="❌ Lỗi reaction",
                        description="Không thể thêm reaction này!",
                        color=discord.Color.red()
                    )
                    error_embed.add_field(
                        name="Nguyên nhân có thể",
                        value=(
                            "• Emoji không khả dụng\n"
                            "• Tin nhắn đã có quá nhiều reaction\n"
                            "• Emoji bị lỗi hoặc đã bị xóa\n"
                            "• Bot đã react emoji này rồi"
                        ),
                        inline=False
                    )
                else:
                    error_embed = discord.Embed(
                        title="❌ Lỗi Discord API",
                        description=f"Lỗi khi thêm reaction: {str(e)[:200]}",
                        color=discord.Color.red()
                    )
                await ctx.reply(embed=error_embed, mention_author=True)
                logger.error(f"HTTPException when adding reaction: {e}")
                
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lỗi hệ thống",
                description=f"Có lỗi xảy ra khi thêm emoji: {str(e)[:200]}",
                color=discord.Color.red()
            )
            await ctx.reply(embed=error_embed, mention_author=True)
            logger.error(f"Error in emoji command: {e}")
