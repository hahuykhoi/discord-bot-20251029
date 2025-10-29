# -*- coding: utf-8 -*-
"""
Purge Commands - Hệ thống xóa tin nhắn hàng loạt
Chỉ Admin mới có quyền sử dụng
"""
import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PurgeCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.setup_commands()
    
    def setup_commands(self):
        """Thiết lập các lệnh purge"""
        
        @self.bot.command(name='purge')
        async def purge_command(ctx, amount=None, limit=None):
            """
            Xóa tin nhắn hàng loạt trong kênh
            Chỉ Admin mới có quyền sử dụng
            
            Usage: 
            ;purge <số> - Xóa số tin nhắn cụ thể (1-100)
            ;purge all - Xóa tất cả tin nhắn trong kênh
            ;purge bot [số] - Xóa tin nhắn của bot (tối đa 100, mặc định 50)
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin mới có thể sử dụng lệnh purge!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Kiểm tra bot có quyền manage_messages không
            if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                embed = discord.Embed(
                    title="❌ Bot thiếu quyền",
                    description="Bot cần quyền `Manage Messages` để xóa tin nhắn!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🔧 Cách khắc phục",
                    value="Vui lòng cấp quyền `Manage Messages` cho bot trong kênh này",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if not amount:
                # Hiển thị help
                embed = discord.Embed(
                    title="🗑️ Hướng dẫn Purge",
                    description="Xóa tin nhắn hàng loạt trong kênh",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="📝 Cách sử dụng",
                    value=(
                        "`;purge <số>` - Xóa số tin nhắn cụ thể (1-100)\n"
                        "`;purge all` - Xóa tất cả tin nhắn trong kênh\n"
                        "`;purge bot [số]` - Xóa tin nhắn bot (mặc định 50, tối đa 100)"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="⚠️ Lưu ý quan trọng",
                    value="• Tin nhắn đã xóa **KHÔNG THỂ KHÔI PHỤC**\n• Chỉ xóa được tin nhắn dưới 14 ngày\n• Cần quyền Admin để sử dụng",
                    inline=False
                )
                
                embed.add_field(
                    name="🛡️ Quyền hạn",
                    value="• Admin: Có thể purge\n• User thường: Không có quyền",
                    inline=False
                )
                
                embed.set_footer(text="Sử dụng cẩn thận - Không thể hoàn tác!")
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Xử lý purge all
            if amount.lower() == 'all':
                # Xác nhận trước khi xóa tất cả
                confirm_embed = discord.Embed(
                    title="⚠️ XÁC NHẬN XÓA TẤT CẢ",
                    description=f"Bạn có chắc muốn xóa **TẤT CẢ** tin nhắn trong kênh {ctx.channel.mention}?",
                    color=discord.Color.orange()
                )
                
                confirm_embed.add_field(
                    name="🚨 Cảnh báo",
                    value="• Hành động này **KHÔNG THỂ HOÀN TÁC**\n• Tất cả tin nhắn sẽ bị xóa vĩnh viễn\n• Chỉ xóa được tin nhắn dưới 14 ngày",
                    inline=False
                )
                
                confirm_embed.add_field(
                    name="✅ Xác nhận",
                    value="Reply `CONFIRM DELETE ALL` trong 30 giây để xác nhận",
                    inline=False
                )
                
                confirm_embed.set_footer(text="Timeout sau 30 giây")
                confirm_msg = await ctx.reply(embed=confirm_embed, mention_author=True)
                
                def check(m):
                    return (m.author == ctx.author and 
                           m.channel == ctx.channel and 
                           m.content.upper() == 'CONFIRM DELETE ALL' and
                           m.reference and 
                           m.reference.message_id == confirm_msg.id)
                
                try:
                    await self.bot.wait_for('message', check=check, timeout=30.0)
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        title="⏰ Hết thời gian",
                        description="Hủy xóa tất cả tin nhắn.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=timeout_embed)
                    return
                
                # Thực hiện xóa tất cả
                try:
                    progress_embed = discord.Embed(
                        title="🗑️ Đang xóa tất cả tin nhắn...",
                        description="Vui lòng chờ, quá trình này có thể mất vài phút.",
                        color=discord.Color.yellow()
                    )
                    progress_msg = await ctx.send(embed=progress_embed)
                    
                    deleted_count = 0
                    
                    # Xóa theo batch để tránh rate limit
                    while True:
                        messages = []
                        async for message in ctx.channel.history(limit=100):
                            if message.id != progress_msg.id:  # Không xóa tin nhắn progress
                                messages.append(message)
                        
                        if not messages:
                            break
                        
                        # Xóa messages
                        try:
                            await ctx.channel.delete_messages(messages)
                            deleted_count += len(messages)
                            
                            # Cập nhật progress
                            if deleted_count % 50 == 0:  # Cập nhật mỗi 50 tin nhắn
                                progress_embed.description = f"Đã xóa {deleted_count} tin nhắn..."
                                await progress_msg.edit(embed=progress_embed)
                        
                        except discord.HTTPException:
                            # Nếu bulk delete không được, xóa từng tin nhắn
                            for message in messages:
                                try:
                                    await message.delete()
                                    deleted_count += 1
                                except:
                                    pass
                        
                        # Delay để tránh rate limit
                        await asyncio.sleep(1)
                    
                    # Thông báo hoàn thành
                    success_embed = discord.Embed(
                        title="✅ Xóa hoàn tất",
                        description=f"Đã xóa **{deleted_count}** tin nhắn trong kênh {ctx.channel.mention}",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    success_embed.add_field(
                        name="👤 Thực hiện bởi",
                        value=ctx.author.mention,
                        inline=True
                    )
                    
                    success_embed.add_field(
                        name="📊 Thống kê",
                        value=f"Tổng cộng: {deleted_count} tin nhắn",
                        inline=True
                    )
                    
                    await progress_msg.edit(embed=success_embed)
                    logger.info(f"Admin {ctx.author} đã purge all {deleted_count} tin nhắn trong {ctx.channel}")
                
                except Exception as e:
                    error_embed = discord.Embed(
                        title="❌ Lỗi khi xóa",
                        description=f"Có lỗi xảy ra: {str(e)}",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    logger.error(f"Lỗi trong purge all: {e}")
                
                return
            
            # Xử lý purge bot - chỉ xóa tin nhắn của bot
            if amount.lower() == 'bot':
                # Xử lý số lượng tin nhắn bot cần xóa
                bot_limit = 50  # Mặc định 50 tin nhắn
                if limit:
                    try:
                        bot_limit = int(limit)
                        if bot_limit < 1:
                            embed = discord.Embed(
                                title="❌ Số quá nhỏ",
                                description="Số tin nhắn phải lớn hơn 0!",
                                color=discord.Color.red()
                            )
                            await ctx.reply(embed=embed, mention_author=True)
                            return
                        if bot_limit > 100:
                            embed = discord.Embed(
                                title="❌ Số quá lớn",
                                description="Chỉ có thể xóa tối đa 100 tin nhắn bot một lần!",
                                color=discord.Color.red()
                            )
                            embed.add_field(
                                name="💡 Gợi ý",
                                value="Sử dụng `;purge bot 100` để xóa 100 tin nhắn bot",
                                inline=False
                            )
                            await ctx.reply(embed=embed, mention_author=True)
                            return
                    except ValueError:
                        embed = discord.Embed(
                            title="❌ Số không hợp lệ",
                            description="Vui lòng nhập số hợp lệ cho số lượng tin nhắn bot!",
                            color=discord.Color.red()
                        )
                        embed.add_field(
                            name="💡 Ví dụ",
                            value="`;purge bot 30` - Xóa 30 tin nhắn bot gần nhất",
                            inline=False
                        )
                        await ctx.reply(embed=embed, mention_author=True)
                        return
                
                try:
                    # Xóa tin nhắn command trước
                    await ctx.message.delete()
                    
                    # Hiển thị thông báo đang xử lý
                    processing_embed = discord.Embed(
                        title="🤖 Đang tìm tin nhắn bot...",
                        description=f"Đang tìm {bot_limit} tin nhắn bot gần nhất để xóa",
                        color=discord.Color.yellow()
                    )
                    progress_msg = await ctx.send(embed=processing_embed)
                    
                    # Tìm tin nhắn của bot
                    bot_messages = []
                    deleted_count = 0
                    
                    # Quét lịch sử kênh để tìm tin nhắn bot (giới hạn theo bot_limit)
                    async for message in ctx.channel.history(limit=bot_limit * 3):  # Quét nhiều hơn để đảm bảo tìm đủ
                        if message.author.bot and message.id != progress_msg.id:
                            bot_messages.append(message)
                            if len(bot_messages) >= bot_limit:
                                break
                    
                    if not bot_messages:
                        no_msg_embed = discord.Embed(
                            title="⚠️ Không tìm thấy tin nhắn bot",
                            description="Không có tin nhắn nào của bot để xóa trong kênh này!",
                            color=discord.Color.orange()
                        )
                        await progress_msg.edit(embed=no_msg_embed)
                        # Tự xóa sau 5 giây
                        await asyncio.sleep(5)
                        try:
                            await progress_msg.delete()
                        except:
                            pass
                        return
                    
                    # Xóa tin nhắn bot theo batch
                    batch_size = 100
                    for i in range(0, len(bot_messages), batch_size):
                        batch = bot_messages[i:i + batch_size]
                        try:
                            await ctx.channel.delete_messages(batch)
                            deleted_count += len(batch)
                        except discord.HTTPException:
                            # Nếu bulk delete không được, xóa từng tin nhắn
                            for msg in batch:
                                try:
                                    await msg.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.5)
                                except:
                                    pass
                        
                        # Cập nhật progress nếu có nhiều batch
                        if len(bot_messages) > batch_size and i + batch_size < len(bot_messages):
                            processing_embed.description = f"Đã xóa {deleted_count}/{len(bot_messages)} tin nhắn bot..."
                            await progress_msg.edit(embed=processing_embed)
                            await asyncio.sleep(1)
                    
                    # Thông báo kết quả
                    success_embed = discord.Embed(
                        title="🤖 Xóa tin nhắn bot hoàn tất",
                        description=f"Đã xóa **{deleted_count}** tin nhắn của bot trong kênh {ctx.channel.mention}",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    success_embed.add_field(
                        name="👤 Thực hiện bởi",
                        value=ctx.author.mention,
                        inline=True
                    )
                    
                    success_embed.add_field(
                        name="🎯 Loại tin nhắn",
                        value="Chỉ tin nhắn của bot",
                        inline=True
                    )
                    
                    success_embed.add_field(
                        name="📊 Thống kê",
                        value=f"Tổng cộng: {deleted_count} tin nhắn bot",
                        inline=False
                    )
                    
                    success_embed.set_footer(text="Tin nhắn này sẽ tự xóa sau 10 giây")
                    
                    await progress_msg.edit(embed=success_embed)
                    
                    # Tự xóa tin nhắn thông báo sau 10 giây
                    await asyncio.sleep(10)
                    try:
                        await progress_msg.delete()
                    except:
                        pass
                    
                    logger.info(f"Admin {ctx.author} đã purge {deleted_count} tin nhắn bot trong {ctx.channel}")
                
                except discord.Forbidden:
                    embed = discord.Embed(
                        title="❌ Không có quyền",
                        description="Bot không có quyền xóa tin nhắn trong kênh này!",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                
                except Exception as e:
                    error_embed = discord.Embed(
                        title="❌ Lỗi khi xóa tin nhắn bot",
                        description=f"Có lỗi xảy ra: {str(e)}",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    logger.error(f"Lỗi trong purge bot: {e}")
                
                return
            
            # Xử lý purge số lượng cụ thể
            try:
                delete_count = int(amount)
            except ValueError:
                embed = discord.Embed(
                    title="❌ Tham số không hợp lệ",
                    description="Vui lòng nhập số hợp lệ, 'all' hoặc 'bot'!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Ví dụ",
                    value=(
                        "`;purge 10` - Xóa 10 tin nhắn\n"
                        "`;purge all` - Xóa tất cả tin nhắn\n"
                        "`;purge bot` - Xóa 50 tin nhắn bot (mặc định)\n"
                        "`;purge bot 30` - Xóa 30 tin nhắn bot"
                    ),
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Giới hạn số lượng
            if delete_count < 1:
                embed = discord.Embed(
                    title="❌ Số quá nhỏ",
                    description="Số tin nhắn phải lớn hơn 0!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            if delete_count > 100:
                embed = discord.Embed(
                    title="❌ Số quá lớn",
                    description="Chỉ có thể xóa tối đa 100 tin nhắn một lần!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Gợi ý",
                    value="Sử dụng `;purge all` để xóa tất cả tin nhắn hoặc `;purge bot [số]` để xóa tin nhắn bot",
                    inline=False
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Thực hiện xóa
            try:
                # Xóa tin nhắn command trước
                await ctx.message.delete()
                
                # Lấy tin nhắn cần xóa (không bao gồm tin nhắn command)
                messages_to_delete = []
                async for message in ctx.channel.history(limit=delete_count):
                    messages_to_delete.append(message)
                
                if not messages_to_delete:
                    embed = discord.Embed(
                        title="⚠️ Không có tin nhắn",
                        description="Không tìm thấy tin nhắn nào để xóa!",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Xóa tin nhắn
                deleted_messages = await ctx.channel.purge(limit=delete_count)
                actual_deleted = len(deleted_messages)
                
                # Thông báo kết quả (tự xóa sau 5 giây)
                success_embed = discord.Embed(
                    title="✅ Xóa thành công",
                    description=f"Đã xóa **{actual_deleted}** tin nhắn",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                success_embed.add_field(
                    name="👤 Thực hiện bởi",
                    value=ctx.author.mention,
                    inline=True
                )
                
                success_embed.add_field(
                    name="📍 Kênh",
                    value=ctx.channel.mention,
                    inline=True
                )
                
                success_embed.set_footer(text="Tin nhắn này sẽ tự xóa sau 5 giây")
                
                result_msg = await ctx.send(embed=success_embed)
                
                # Tự xóa tin nhắn thông báo sau 5 giây
                await asyncio.sleep(5)
                try:
                    await result_msg.delete()
                except:
                    pass
                
                logger.info(f"Admin {ctx.author} đã purge {actual_deleted} tin nhắn trong {ctx.channel}")
            
            except discord.Forbidden:
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Bot không có quyền xóa tin nhắn trong kênh này!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            
            except discord.HTTPException as e:
                embed = discord.Embed(
                    title="❌ Lỗi Discord",
                    description=f"Không thể xóa tin nhắn: {str(e)}",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Lưu ý",
                    value="Chỉ có thể xóa tin nhắn dưới 14 ngày tuổi",
                    inline=False
                )
                await ctx.send(embed=embed)
            
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Lỗi không xác định",
                    description=f"Có lỗi xảy ra: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                logger.error(f"Lỗi trong purge: {e}")
    
    def register_commands(self):
        """Đăng ký commands - được gọi từ bot chính"""
        logger.info("Purge commands đã được đăng ký")
