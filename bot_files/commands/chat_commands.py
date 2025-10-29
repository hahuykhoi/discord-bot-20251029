"""
Chat commands - Anonymous messaging
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from .base import BaseCommand

logger = logging.getLogger(__name__)

class ChatCommands(BaseCommand):
    """Class chứa các commands chat ẩn danh"""
    
    def register_commands(self):
        """Register chat commands"""
        
        # Slash command /chat đã được chuyển sang slash_commands.py để tránh conflict
        
        @self.bot.command(name='dm', aliases=['chat'])
        async def dm_chat(ctx, user: discord.User = None, *, message: str = None):
            """
            Gửi tin nhắn DM cho user theo ID hoặc tag
            Chỉ user ID 1264908798003253314 mới sử dụng được
            Không bị delay/cooldown
            
            Usage: 
                ;dm <user_id> <nội dung tin nhắn>
                ;dm @user <nội dung tin nhắn>
                ;chat <user_id> <nội dung tin nhắn> (alias)
                ;chat @user <nội dung tin nhắn> (alias)
            """
            # Bypass cooldown cho dm command
            await self._dm_chat_impl(ctx, user, message)
        
        @self.bot.command(name='chatroom')
        async def chatroom(ctx, channel_id: int = None, *, message: str = None):
            """
            Gửi tin nhắn vào channel theo ID
            Chỉ user ID 1264908798003253314 mới sử dụng được
            
            Usage: ;chatroom <channel_id> <nội dung tin nhắn>
            """
            await self._chatroom_impl(ctx, channel_id, message)
    
    async def _slash_chat_impl(self, interaction: discord.Interaction, message: str):
        """
        Implementation cho slash command /chat
        Bot sẽ gửi tin nhắn thay user trong channel hiện tại
        """
        try:
            # Kiểm tra quyền sử dụng - chỉ user ID cụ thể
            ALLOWED_USER_ID = 1264908798003253314
            if interaction.user.id != ALLOWED_USER_ID:
                await interaction.response.send_message(
                    "❌ Bạn không có quyền sử dụng lệnh này!",
                    ephemeral=True  # Chỉ user thấy
                )
                return
            
            # Kiểm tra nội dung tin nhắn
            if not message or message.strip() == "":
                await interaction.response.send_message(
                    "❌ Vui lòng cung cấp nội dung tin nhắn!",
                    ephemeral=True
                )
                return
            
            # Kiểm tra độ dài tin nhắn
            if len(message) > 2000:
                await interaction.response.send_message(
                    f"❌ Tin nhắn quá dài! Giới hạn: 2000 ký tự, hiện tại: {len(message)} ký tự",
                    ephemeral=True
                )
                return
            
            # Kiểm tra bot có quyền gửi tin nhắn trong channel không
            if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
                await interaction.response.send_message(
                    "❌ Bot không có quyền gửi tin nhắn trong channel này!",
                    ephemeral=True
                )
                return
            
            # Respond ephemeral để chỉ user thấy
            await interaction.response.send_message("✅ Tin nhắn đã được gửi!", ephemeral=True)
            
            # Gửi tin nhắn thay user
            await interaction.channel.send(message)
            
            # Log để theo dõi
            logger.info(f"Slash chat used by {interaction.user} ({interaction.user.id}) in {interaction.channel.name} ({interaction.channel.id}): {message[:50]}...")
            
        except discord.errors.Forbidden:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Bot không có quyền gửi tin nhắn trong channel này!",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ Bot không có quyền gửi tin nhắn trong channel này!",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in slash chat: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Có lỗi xảy ra: {str(e)[:100]}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Có lỗi xảy ra: {str(e)[:100]}",
                    ephemeral=True
                )
    
    async def _dm_chat_impl(self, ctx, user: discord.User, message: str):
        """
        Implementation thực tế của DM chat command
        """
        try:
            # Kiểm tra quyền sử dụng - chỉ user ID cụ thể
            ALLOWED_USER_ID = 1264908798003253314
            if ctx.author.id != ALLOWED_USER_ID:
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", 
                    mention_author=True
                )
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                return
            
            # Kiểm tra nếu không có user target
            if user is None:
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Vui lòng cung cấp user ID hoặc tag cần gửi tin nhắn!\n"
                    f"**Cách sử dụng:** ; <user_id> <nội dung tin nhắn>` hoặc ; @user <nội dung tin nhắn>`\n"
                    f"**Ví dụ:** ; 123456789 Hello!` hoặc ; @username Hello!`",
                    mention_author=True
                )
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                return
            # Kiểm tra nếu không có nội dung
            if not message or message.strip() == "":
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Vui lòng cung cấp nội dung tin nhắn!\n"
                    f"**Cách sử dụng:** ; <user_id> <nội dung tin nhắn>` hoặc ; @user <nội dung tin nhắn>`\n"
                    f"**Ví dụ:** ; 123456789 Hello there!` hoặc ; @username Hello there!`",
                    mention_author=True
                )
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                return
            
            # Kiểm tra user và gửi DM
            try:
                # Kiểm tra nếu user là bot
                if user.bot:
                    error_msg = await ctx.reply(
                        f"{ctx.author.mention} ❌ Không thể gửi DM cho bot!",
                        mention_author=True
                    )
                    # Xóa tin nhắn sau 3 giây
                    await asyncio.sleep(3)
                    try:
                        await ctx.message.delete()
                        await error_msg.delete()
                    except:
                        pass
                    return
                
                # Kiểm tra nếu user là chính mình
                if user.id == ctx.author.id:
                    error_msg = await ctx.reply(
                        f"{ctx.author.mention} ❌ Không thể gửi DM cho chính mình!",
                        mention_author=True
                    )
                    # Xóa tin nhắn sau 3 giây
                    await asyncio.sleep(3)
                    try:
                        await ctx.message.delete()
                        await error_msg.delete()
                    except:
                        pass
                    return
                
                await user.send(message)
                
                # Thông báo thành công
                success_embed = discord.Embed(
                    title="✉️ DM đã được gửi!",
                    description=f"Tin nhắn đã được gửi thành công cho {user.mention}",
                    color=discord.Color.green()
                )
                success_embed.add_field(
                    name="Nội dung",
                    value=f"`{message[:100]}{'...' if len(message) > 100 else ''}`",
                    inline=False
                )
                success_msg = await ctx.reply(embed=success_embed, mention_author=True)
                
                # Log để theo dõi
                logger.info(f"DM sent by {ctx.author} ({ctx.author.id}) to {user} ({user.id}): {message[:50]}...")
                
                # Tự động xóa tin nhắn lệnh và tin nhắn báo thành công sau 3 giây
                try:
                    await asyncio.sleep(3)
                    await ctx.message.delete()  # Xóa tin nhắn lệnh gốc
                    await success_msg.delete()  # Xóa tin nhắn báo thành công
                except discord.errors.NotFound:
                    # Tin nhắn đã bị xóa rồi
                    pass
                except discord.errors.Forbidden:
                    # Bot không có quyền xóa tin nhắn
                    logger.warning("Bot không có quyền xóa tin nhắn trong channel này")
                
            except discord.errors.Forbidden:
                # User đã chặn DM từ server hoặc từ bot
                error_embed = discord.Embed(
                    title="❌ Không thể gửi DM",
                    description=f"Không thể gửi tin nhắn cho {user.mention} ({user.id})",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Nguyên nhân có thể",
                    value=(
                        "• User đã chặn DM từ server này\n"
                        "• User đã chặn DM từ bot\n"
                        "• User không cùng server với bot"
                    ),
                    inline=False
                )
                error_msg = await ctx.reply(embed=error_embed, mention_author=True)
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                
            except Exception as e:
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Lỗi khi gửi DM: {str(e)[:100]}",
                    mention_author=True
                )
                logger.error(f"Error sending DM: {e}")
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error in anonymous chat: {e}")
            try:
                await ctx.send(f"❌ Có lỗi xảy ra khi gửi tin nhắn: {str(e)[:100]}", delete_after=5)
            except:
                pass
    
    async def _chatroom_impl(self, ctx, channel_id: int, message: str):
        """
        Implementation thực tế của chatroom command
        """
        try:
            # Kiểm tra quyền sử dụng - chỉ user ID cụ thể
            ALLOWED_USER_ID = 1264908798003253314
            if ctx.author.id != ALLOWED_USER_ID:
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Bạn không có quyền sử dụng lệnh này!", 
                    mention_author=True
                )
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                return
            
            # Kiểm tra nếu không có channel_id target
            if channel_id is None:
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Vui lòng cung cấp channel ID cần gửi tin nhắn!\n"
                    f"**Cách sử dụng:** ; <channel_id> <nội dung tin nhắn>`\n"
                    f"**Ví dụ:** ; 123456789 Hello everyone!`",
                    mention_author=True
                )
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                return
            
            # Kiểm tra nếu không có nội dung
            if not message or message.strip() == "":
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Vui lòng cung cấp nội dung tin nhắn!\n"
                    f"**Cách sử dụng:** ; <channel_id> <nội dung tin nhắn>`\n"
                    f"**Ví dụ:** ; 123456789 Hello everyone!`",
                    mention_author=True
                )
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                return
            
            # Thử lấy channel từ ID và gửi tin nhắn
            try:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    # Thử fetch nếu không có trong cache
                    channel = await self.bot.fetch_channel(channel_id)
                
                # Kiểm tra xem bot có quyền gửi tin nhắn trong channel không
                if not channel.permissions_for(ctx.guild.me).send_messages:
                    error_msg = await ctx.reply(
                        f"{ctx.author.mention} ❌ Bot không có quyền gửi tin nhắn trong channel này!",
                        mention_author=True
                    )
                    # Xóa tin nhắn sau 3 giây
                    await asyncio.sleep(3)
                    try:
                        await ctx.message.delete()
                        await error_msg.delete()
                    except:
                        pass
                    return
                
                # Gửi tin nhắn vào channel
                await channel.send(message)
                
                # Thông báo thành công
                success_embed = discord.Embed(
                    title="📢 Tin nhắn đã được gửi!",
                    description=f"Tin nhắn đã được gửi thành công vào {channel.mention}",
                    color=discord.Color.green()
                )
                success_embed.add_field(
                    name="Nội dung",
                    value=f"`{message[:100]}{'...' if len(message) > 100 else ''}`",
                    inline=False
                )
                success_msg = await ctx.reply(embed=success_embed, mention_author=True)
                
                # Log để theo dõi
                logger.info(f"Channel message sent by {ctx.author} ({ctx.author.id}) to {channel.name} ({channel_id}): {message[:50]}...")
                
                # Tự động xóa tin nhắn lệnh và tin nhắn báo thành công sau 3 giây
                try:
                    await asyncio.sleep(3)
                    await ctx.message.delete()  # Xóa tin nhắn lệnh gốc
                    await success_msg.delete()  # Xóa tin nhắn báo thành công
                except discord.errors.NotFound:
                    # Tin nhắn đã bị xóa rồi
                    pass
                except discord.errors.Forbidden:
                    # Bot không có quyền xóa tin nhắn
                    logger.warning("Bot không có quyền xóa tin nhắn trong channel này")
                
            except discord.NotFound:
                # Channel không tồn tại
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Không tìm thấy channel với ID: {channel_id}",
                    mention_author=True
                )
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                    
            except discord.errors.Forbidden:
                # Bot không có quyền truy cập channel
                error_embed = discord.Embed(
                    title="❌ Không thể gửi tin nhắn",
                    description=f"Không thể gửi tin nhắn vào channel ID: {channel_id}",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Nguyên nhân có thể",
                    value=(
                        "• Bot không có quyền truy cập channel\n"
                        "• Bot không có quyền gửi tin nhắn\n"
                        "• Channel là private channel"
                    ),
                    inline=False
                )
                error_msg = await ctx.reply(embed=error_embed, mention_author=True)
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
                
            except Exception as e:
                error_msg = await ctx.reply(
                    f"{ctx.author.mention} ❌ Lỗi khi gửi tin nhắn: {str(e)[:100]}",
                    mention_author=True
                )
                logger.error(f"Error sending channel message: {e}")
                # Xóa tin nhắn sau 3 giây
                await asyncio.sleep(3)
                try:
                    await ctx.message.delete()
                    await error_msg.delete()
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error in chatroom command: {e}")
            try:
                await ctx.send(f"❌ Có lỗi xảy ra khi gửi tin nhắn: {str(e)[:100]}", delete_after=5)
            except:
                pass
