"""
Announce/Broadcast commands
Lệnh: ;thongbao [noi_dung]
- Admin dùng ;thongbao + nội dung: DM tới các thành viên đang online trong server
- Member gõ ;thongbao (không nội dung): Nhận lại thông báo gần nhất của server
"""
import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
import logging

from .base import BaseCommand

logger = logging.getLogger(__name__)

class AnnounceCommands(BaseCommand):
    """Commands gửi thông báo hệ thống"""

    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        # Lưu thông báo theo guild_id
        self.data_file = 'announcements.json'
        self._cache = self._load_data()

    def _load_data(self) -> dict:
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Lỗi khi tải announcements: {e}")
        return {}

    def _save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Lỗi khi lưu announcements: {e}")

    def _set_latest_announcement(self, guild_id: int, content: str, author_id: int):
        self._cache[str(guild_id)] = {
            'content': content,
            'author_id': author_id,
            'timestamp': datetime.now().isoformat()
        }
        self._save_data()

    def _get_latest_announcement(self, guild_id: int):
        return self._cache.get(str(guild_id))

    def _build_announcement_embed(self, ctx, content: str) -> discord.Embed:
        embed = discord.Embed(
            title="📢 Thông báo từ Server",
            description=content,
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )
        embed.set_author(
            name=f"{ctx.guild.name}",
            icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else discord.Embed.Empty
        )
        embed.add_field(name="Người gửi", value=f"<@{ctx.author.id}>", inline=True)
        return embed

    def register_commands(self):
        @self.bot.command(name='thongbao')
        async def thongbao(ctx, *, content: str = None):
            """
            - Admin: ;thongbao <nội dung> -> DM tới thành viên đang online
            - User: ;thongbao -> Xem thông báo gần nhất của server
            """
            # Sử dụng lock để tránh duplicate execution
            lock = self.bot_instance.get_command_lock('thongbao', ctx.author.id)
            async with lock:
                try:
                    if ctx.guild is None:
                        await ctx.reply("❌ Vui lòng sử dụng lệnh trong server.", mention_author=True)
                        return

                    # Nếu không có nội dung -> trả về thông báo gần nhất
                    if not content:
                        latest = self._get_latest_announcement(ctx.guild.id)
                        if not latest:
                            await ctx.reply("ℹ️ Hiện chưa có thông báo nào.", mention_author=True)
                            return

                        embed = discord.Embed(
                            title="📢 Thông báo gần nhất",
                            description=latest['content'],
                            color=discord.Color.blurple(),
                        )
                        # Thời gian
                        try:
                            ts = int(datetime.fromisoformat(latest['timestamp']).timestamp())
                            embed.add_field(name="Thời gian", value=f"<t:{ts}:F>", inline=True)
                        except Exception:
                            pass
                        embed.add_field(name="Người gửi", value=f"<@{latest['author_id']}>", inline=True)
                        await ctx.reply(embed=embed, mention_author=True)
                        return

                    # Có nội dung -> kiểm tra quyền sử dụng dynamic permission system
                    if hasattr(self.bot_instance, 'permission_manager'):
                        has_permission, user_level = self.bot_instance.permission_manager.check_command_permission(ctx, 'announce')
                        if not has_permission:
                            await ctx.reply("❌ Bạn không có quyền gửi thông báo.", mention_author=True)
                            return
                    else:
                        # Fallback: Kiểm tra quyền admin nếu không có permission system
                        if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                            await ctx.reply("❌ Bạn không có quyền gửi thông báo.", mention_author=True)
                            return

                    # Xây dựng embed và lưu
                    embed = self._build_announcement_embed(ctx, content)
                    self._set_latest_announcement(ctx.guild.id, content, ctx.author.id)

                    # Chọn thành viên đang online (bao gồm online/idle/dnd), bỏ qua bot
                    def is_online(member: discord.Member) -> bool:
                        return (
                            not member.bot and
                            member.status in {discord.Status.online, discord.Status.idle, discord.Status.dnd}
                        )

                    members = [m for m in ctx.guild.members if is_online(m)]
                    if not members:
                        await ctx.reply("⚠️ Không có thành viên nào đang online để gửi DM.", mention_author=True)
                        return

                    # Gửi DM với giới hạn đồng thời để tránh rate limit
                    sent = 0
                    failed = 0
                    sem = asyncio.Semaphore(5)

                    async def send_dm(member: discord.Member):
                        nonlocal sent, failed
                        async with sem:
                            try:
                                await member.send(embed=embed)
                                sent += 1
                            except Exception:
                                failed += 1

                    await asyncio.gather(*(send_dm(m) for m in members))

                    summary = discord.Embed(
                        title="✅ Đã gửi thông báo",
                        description=f"Đã cố gắng gửi DM tới **{len(members)}** thành viên đang online.",
                        color=discord.Color.green()
                    )
                    summary.add_field(name="Gửi thành công", value=str(sent), inline=True)
                    summary.add_field(name="Thất bại", value=str(failed), inline=True)
                    await ctx.reply(embed=summary, mention_author=True)

                except Exception as e:
                    logger.error(f"Lỗi thongbao command: {e}")
                    await ctx.reply("❌ Có lỗi xảy ra khi gửi thông báo.", mention_author=True)
