# -*- coding: utf-8 -*-
"""
Slash Commands - Chỉ giữ lại /dm, /chat và /giveaway (từ giveaway_commands.py)
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
from .base import BaseCommand

logger = logging.getLogger(__name__)

class SlashCommands(BaseCommand):
    """Class chứa các slash commands - Chỉ /dm và /chat"""
    
    def register_commands(self):
        """Register slash commands - Chỉ giữ lại /dm, /chat và /giveaway (từ giveaway_commands.py)"""
        
        # Admin check function
        def is_admin(user_id: int) -> bool:
            """Kiểm tra user có phải admin không"""
            ALLOWED_USER_ID = 1264908798003253314
            return user_id == ALLOWED_USER_ID
        
        # DM command - Gửi DM cho user với số lượng tin nhắn (Admin only)
        @self.bot.tree.command(name="dm", description="Gửi DM cho user (Admin only)")
        async def slash_dm(interaction: discord.Interaction, 
                          user: discord.User, 
                          message: str, 
                          count: int = 1):
            """Slash command /dm - Gửi DM với số lượng tin nhắn tùy chỉnh"""
            try:
                # Kiểm tra quyền admin
                if not is_admin(interaction.user.id):
                    await interaction.response.send_message(
                        "❌ Bạn không có quyền sử dụng lệnh này!",
                        ephemeral=True
                    )
                    return
                
                # Validate count
                if count < 1 or count > 10:
                    await interaction.response.send_message(
                        "❌ Số lượng tin nhắn phải từ 1-10!",
                        ephemeral=True
                    )
                    return
                
                # Validate message
                if not message or message.strip() == "":
                    await interaction.response.send_message(
                        "❌ Vui lòng cung cấp nội dung tin nhắn!",
                        ephemeral=True
                    )
                    return
                
                # Kiểm tra user
                if user.bot:
                    await interaction.response.send_message(
                        "❌ Không thể gửi DM cho bot!",
                        ephemeral=True
                    )
                    return
                
                if user.id == interaction.user.id:
                    await interaction.response.send_message(
                        "❌ Không thể gửi DM cho chính mình!",
                        ephemeral=True
                    )
                    return
                
                # Respond first
                await interaction.response.send_message(
                    f"🔄 Đang gửi {count} tin nhắn cho {user.mention}...",
                    ephemeral=True
                )
                
                # Gửi tin nhắn với số lượng chỉ định
                success_count = 0
                for i in range(count):
                    try:
                        await user.send(message)
                        success_count += 1
                    except discord.Forbidden:
                        break
                    except Exception as e:
                        logger.error(f"Error sending DM {i+1}: {e}")
                        break
                
                # Thông báo kết quả
                if success_count == count:
                    await interaction.followup.send(
                        f"✅ Đã gửi thành công {success_count} tin nhắn cho {user.mention}!",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⚠️ Chỉ gửi được {success_count}/{count} tin nhắn cho {user.mention}!",
                        ephemeral=True
                    )
                
                logger.info(f"Slash DM: {interaction.user} sent {success_count} messages to {user}")
                
            except Exception as e:
                logger.error(f"Error in slash dm: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Có lỗi xảy ra!", ephemeral=True)

        # Chat command - Bot gửi tin nhắn trong channel (Admin only)
        @self.bot.tree.command(name="chat", description="Bot gửi tin nhắn trong channel (Admin only)")
        async def slash_chat(interaction: discord.Interaction, 
                            message: str, 
                            count: int = 1):
            """Slash command /chat - Gửi tin nhắn với số lượng tùy chỉnh"""
            try:
                # Kiểm tra quyền admin
                if not is_admin(interaction.user.id):
                    await interaction.response.send_message(
                        "❌ Bạn không có quyền sử dụng lệnh này!",
                        ephemeral=True
                    )
                    return
                
                # Validate count
                if count < 1 or count > 10:
                    await interaction.response.send_message(
                        "❌ Số lượng tin nhắn phải từ 1-10!",
                        ephemeral=True
                    )
                    return
                
                # Validate message
                if not message or message.strip() == "":
                    await interaction.response.send_message(
                        "❌ Vui lòng cung cấp nội dung tin nhắn!",
                        ephemeral=True
                    )
                    return
                
                # Kiểm tra permissions
                if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
                    await interaction.response.send_message(
                        "❌ Bot không có quyền gửi tin nhắn trong channel này!",
                        ephemeral=True
                    )
                    return
                
                # Respond first
                await interaction.response.send_message(
                    f"🔄 Đang gửi {count} tin nhắn...",
                    ephemeral=True
                )
                
                # Gửi tin nhắn với số lượng chỉ định
                success_count = 0
                for i in range(count):
                    try:
                        await interaction.channel.send(message)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error sending message {i+1}: {e}")
                        break
                
                # Thông báo kết quả
                await interaction.followup.send(
                    f"✅ Đã gửi thành công {success_count} tin nhắn!",
                    ephemeral=True
                )
                
                logger.info(f"Slash Chat: {interaction.user} sent {success_count} messages in {interaction.channel}")
                
            except Exception as e:
                logger.error(f"Error in slash chat: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Có lỗi xảy ra!", ephemeral=True)
    
    # Giveaway commands được đăng ký trong giveaway_commands.py
    # Chỉ còn lại /dm và /chat ở đây
    
    async def sync_commands(self):
        """
        Sync slash commands với Discord
        """
        try:
            synced = await self.bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")
            print(f"✅ Successfully synced {len(synced)} slash commands")
            return len(synced)
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
            print(f"❌ Failed to sync slash commands: {e}")
            return 0
    
    async def force_sync_commands(self):
        """
        Force sync slash commands (clear cache first)
        """
        try:
            # Clear command tree first
            self.bot.tree.clear_commands()
            logger.info("Cleared command tree")
            
            # Re-register all commands
            await self.register_commands()
            
            # Sync with Discord
            synced = await self.bot.tree.sync()
            logger.info(f"Force synced {len(synced)} slash command(s)")
            print(f"🔄 Force synced {len(synced)} slash commands")
            return len(synced)
        except Exception as e:
            logger.error(f"Failed to force sync slash commands: {e}")
            print(f"❌ Failed to force sync: {e}")
            return 0
