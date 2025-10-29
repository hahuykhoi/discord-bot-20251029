# -*- coding: utf-8 -*-
"""
Reset Commands - Lệnh reset lịch sử chơi và tài sản
"""
import discord
from discord.ext import commands
import json
import os
import logging
import asyncio
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ResetCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        
        # Đường dẫn các file dữ liệu
        self.data_files = {
            'shared_wallet': 'data/shared_wallet.json',
            'taixiu_data': 'data/taixiu_data.json',
            'rps_data': 'data/rps_data.json', 
            'slot_data': 'data/slot_data.json',
            'blackjack_data': 'data/blackjack_data.json',
            'flip_data': 'data/flip_data.json',
            'daily_data': 'data/daily_data.json',
            'shop_data': 'data/shop_data.json',
            'weekly_leaderboard': 'data/weekly_leaderboard.json'
        }
    
    def register_commands(self):
        """Đăng ký các lệnh reset"""
        
        @self.bot.command(name='resetuser')
        async def reset_user_command(ctx, user: discord.Member = None):
            """Reset lịch sử chơi và tài sản của 1 user - Supreme Admin only"""
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Supreme Admin mới có thể reset user!", mention_author=True)
                return
            
            target_user = user or ctx.author
            await self.reset_single_user(ctx, target_user)
        
        @self.bot.command(name='resetall')
        async def reset_all_command(ctx):
            """Reset toàn bộ lịch sử chơi và tài sản - Supreme Admin only"""
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Supreme Admin mới có thể reset toàn bộ!", mention_author=True)
                return
            
            await self.reset_all_users(ctx)
        
        @self.bot.command(name='resetgames')
        async def reset_games_command(ctx, user: discord.Member = None):
            """Reset chỉ lịch sử games (giữ nguyên tiền) - Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể reset games!", mention_author=True)
                return
            
            target_user = user or ctx.author
            await self.reset_user_games_only(ctx, target_user)
        
        @self.bot.command(name='resetmoney')
        async def reset_money_command(ctx, user: discord.Member = None):
            """Reset chỉ tiền (giữ nguyên lịch sử games) - Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể reset tiền!", mention_author=True)
                return
            
            target_user = user or ctx.author
            await self.reset_user_money_only(ctx, target_user)
        
        @self.bot.command(name='resetstats')
        async def reset_stats_command(ctx):
            """Xem thống kê trước khi reset - Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể xem thống kê reset!", mention_author=True)
                return
            
            await self.show_reset_stats(ctx)
    
    async def reset_single_user(self, ctx, user):
        """Reset toàn bộ dữ liệu của 1 user"""
        try:
            user_id = str(user.id)
            reset_summary = {
                'user': user,
                'money_removed': 0,
                'games_reset': [],
                'files_affected': []
            }
            
            # Tạo embed xác nhận
            confirm_embed = discord.Embed(
                title="⚠️ Xác nhận reset user",
                description=f"Bạn có chắc chắn muốn reset toàn bộ dữ liệu của {user.mention}?",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            # Thu thập thông tin hiện tại
            current_money = 0
            if hasattr(self.bot_instance, 'shared_wallet'):
                current_money = self.bot_instance.shared_wallet.get_balance(user.id)
            
            games_data = self.get_user_games_data(user_id)
            
            confirm_embed.add_field(
                name="👤 User:",
                value=f"{user.mention} ({user.display_name})",
                inline=True
            )
            
            confirm_embed.add_field(
                name="💰 Tiền hiện tại:",
                value=f"{current_money:,} xu",
                inline=True
            )
            
            confirm_embed.add_field(
                name="🎮 Games có dữ liệu:",
                value="\n".join([f"• {game}" for game in games_data.keys()]) or "Không có",
                inline=False
            )
            
            confirm_embed.add_field(
                name="⚠️ Cảnh báo:",
                value="**Hành động này KHÔNG THỂ HOÀN TÁC!**\nTất cả dữ liệu sẽ bị xóa vĩnh viễn.",
                inline=False
            )
            
            confirm_embed.add_field(
                name="🔧 Cách xác nhận:",
                value="Reply tin nhắn này với `CONFIRM` để thực hiện reset",
                inline=False
            )
            
            confirm_embed.set_footer(text="Reset System • User Reset")
            
            confirm_message = await ctx.reply(embed=confirm_embed, mention_author=True)
            
            # Chờ xác nhận
            def check(message):
                return (message.author == ctx.author and 
                       message.reference and 
                       message.reference.message_id == confirm_message.id and
                       message.content.upper() == "CONFIRM")
            
            try:
                await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Hết thời gian xác nhận",
                    description="Reset user đã bị hủy do không có xác nhận trong 30 giây.",
                    color=discord.Color.red()
                )
                await ctx.followup.send(embed=timeout_embed)
                return
            
            # Thực hiện reset
            # 1. Reset tiền
            if hasattr(self.bot_instance, 'shared_wallet'):
                reset_summary['money_removed'] = current_money
                self.bot_instance.shared_wallet.set_balance(user.id, 0)
                reset_summary['files_affected'].append('shared_wallet')
            
            # 2. Reset từng game
            for game_name, data in games_data.items():
                if data:  # Nếu có dữ liệu
                    self.reset_user_from_file(user_id, self.data_files.get(f'{game_name}_data'))
                    reset_summary['games_reset'].append(game_name)
                    reset_summary['files_affected'].append(f'{game_name}_data')
            
            # 3. Reset shop data
            if os.path.exists(self.data_files['shop_data']):
                self.reset_user_from_file(user_id, self.data_files['shop_data'])
                reset_summary['games_reset'].append('shop')
                reset_summary['files_affected'].append('shop_data')
            
            # 4. Reset daily data
            if os.path.exists(self.data_files['daily_data']):
                self.reset_user_from_file(user_id, self.data_files['daily_data'])
                reset_summary['games_reset'].append('daily')
                reset_summary['files_affected'].append('daily_data')
            
            # 5. Reset weekly leaderboard
            if os.path.exists(self.data_files['weekly_leaderboard']):
                self.reset_user_from_file(user_id, self.data_files['weekly_leaderboard'])
                reset_summary['games_reset'].append('weekly_leaderboard')
                reset_summary['files_affected'].append('weekly_leaderboard')
            
            # Thông báo thành công
            success_embed = discord.Embed(
                title="✅ Đã reset user thành công",
                description=f"Toàn bộ dữ liệu của {user.mention} đã được reset",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="👤 User đã reset:",
                value=f"{user.mention} ({user.display_name})",
                inline=True
            )
            
            success_embed.add_field(
                name="💰 Tiền đã xóa:",
                value=f"{reset_summary['money_removed']:,} xu",
                inline=True
            )
            
            success_embed.add_field(
                name="🎮 Games đã reset:",
                value=f"{len(reset_summary['games_reset'])} games" if reset_summary['games_reset'] else "Không có",
                inline=True
            )
            
            success_embed.add_field(
                name="📁 Files đã cập nhật:",
                value="\n".join([f"• {file}" for file in set(reset_summary['files_affected'])]),
                inline=False
            )
            
            success_embed.add_field(
                name="👨‍💼 Thực hiện bởi:",
                value=f"{ctx.author.mention} ({ctx.author.name})",
                inline=False
            )
            
            success_embed.set_footer(text="Reset System • User Reset Completed")
            
            await ctx.followup.send(embed=success_embed)
            
            # Log action
            logger.info(f"User reset by {ctx.author.name} ({ctx.author.id}): User {user.name} ({user.id}), {reset_summary['money_removed']} xu removed, {len(reset_summary['games_reset'])} games reset")
            
        except Exception as e:
            logger.error(f"Lỗi khi reset user {user.id}: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra khi reset user: {str(e)}", mention_author=True)
    
    async def reset_all_users(self, ctx):
        """Reset toàn bộ dữ liệu của tất cả users"""
        try:
            # Thu thập thống kê trước khi reset
            total_users = 0
            total_money = 0
            
            if hasattr(self.bot_instance, 'shared_wallet'):
                total_users = self.bot_instance.shared_wallet.get_user_count()
                total_money = self.bot_instance.shared_wallet.get_total_money_in_system()
            
            # Tạo embed xác nhận
            confirm_embed = discord.Embed(
                title="🚨 XÁC NHẬN RESET TOÀN BỘ HỆ THỐNG",
                description="**CẢNH BÁO: Bạn sắp xóa toàn bộ dữ liệu của tất cả users!**",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            confirm_embed.add_field(
                name="📊 Thống kê hiện tại:",
                value=f"• **{total_users:,}** users\n• **{total_money:,}** xu tổng cộng",
                inline=False
            )
            
            confirm_embed.add_field(
                name="🗑️ Sẽ bị xóa:",
                value=(
                    "• Toàn bộ tiền của tất cả users\n"
                    "• Lịch sử chơi tất cả games\n"
                    "• Dữ liệu shop và daily\n"
                    "• Weekly leaderboard\n"
                    "• Tất cả thống kê"
                ),
                inline=False
            )
            
            confirm_embed.add_field(
                name="⚠️ CẢNH BÁO NGHIÊM TRỌNG:",
                value="**HÀNH ĐỘNG NÀY KHÔNG THỂ HOÀN TÁC!**\nToàn bộ dữ liệu sẽ bị xóa vĩnh viễn.",
                inline=False
            )
            
            confirm_embed.add_field(
                name="🔧 Cách xác nhận:",
                value="Reply tin nhắn này với `RESET ALL CONFIRM` để thực hiện",
                inline=False
            )
            
            confirm_embed.set_footer(text="Reset System • FULL SYSTEM RESET")
            
            confirm_message = await ctx.reply(embed=confirm_embed, mention_author=True)
            
            # Chờ xác nhận
            def check(message):
                return (message.author == ctx.author and 
                       message.reference and 
                       message.reference.message_id == confirm_message.id and
                       message.content.upper() == "RESET ALL CONFIRM")
            
            try:
                await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Hết thời gian xác nhận",
                    description="Reset toàn bộ đã bị hủy do không có xác nhận trong 60 giây.",
                    color=discord.Color.red()
                )
                await ctx.followup.send(embed=timeout_embed)
                return
            
            # Thực hiện reset toàn bộ
            files_reset = []
            
            # Reset từng file
            for file_name, file_path in self.data_files.items():
                if os.path.exists(file_path):
                    try:
                        # Backup file trước khi reset
                        backup_path = f"{file_path}.backup_{int(datetime.now().timestamp())}"
                        os.rename(file_path, backup_path)
                        
                        # Tạo file mới rỗng
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump({}, f, ensure_ascii=False, indent=2)
                        
                        files_reset.append(file_name)
                        logger.info(f"Reset file {file_path}, backup saved as {backup_path}")
                        
                    except Exception as e:
                        logger.error(f"Lỗi khi reset file {file_path}: {e}")
            
            # Reload shared wallet
            if hasattr(self.bot_instance, 'shared_wallet'):
                self.bot_instance.shared_wallet.reload_data()
            
            # Thông báo thành công
            success_embed = discord.Embed(
                title="✅ ĐÃ RESET TOÀN BỘ HỆ THỐNG",
                description="Toàn bộ dữ liệu đã được reset thành công",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="📊 Dữ liệu đã xóa:",
                value=f"• **{total_users:,}** users\n• **{total_money:,}** xu",
                inline=True
            )
            
            success_embed.add_field(
                name="📁 Files đã reset:",
                value=f"**{len(files_reset)}** files",
                inline=True
            )
            
            success_embed.add_field(
                name="💾 Backup:",
                value="Tất cả files đã được backup với timestamp",
                inline=True
            )
            
            success_embed.add_field(
                name="🗂️ Files đã reset:",
                value="\n".join([f"• {file}" for file in files_reset]),
                inline=False
            )
            
            success_embed.add_field(
                name="👨‍💼 Thực hiện bởi:",
                value=f"{ctx.author.mention} ({ctx.author.name})",
                inline=False
            )
            
            success_embed.set_footer(text="Reset System • FULL RESET COMPLETED")
            
            await ctx.followup.send(embed=success_embed)
            
            # Log action
            logger.warning(f"FULL SYSTEM RESET by {ctx.author.name} ({ctx.author.id}): {total_users} users, {total_money} xu, {len(files_reset)} files reset")
            
        except Exception as e:
            logger.error(f"Lỗi khi reset toàn bộ hệ thống: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra khi reset hệ thống: {str(e)}", mention_author=True)
    
    async def reset_user_games_only(self, ctx, user):
        """Reset chỉ lịch sử games, giữ nguyên tiền"""
        try:
            user_id = str(user.id)
            games_reset = []
            
            # Reset từng game (trừ shared_wallet)
            game_files = {k: v for k, v in self.data_files.items() if k != 'shared_wallet'}
            
            for game_name, file_path in game_files.items():
                if os.path.exists(file_path):
                    if self.reset_user_from_file(user_id, file_path):
                        games_reset.append(game_name)
            
            # Thông báo kết quả
            embed = discord.Embed(
                title="✅ Đã reset lịch sử games",
                description=f"Lịch sử chơi game của {user.mention} đã được reset",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User:",
                value=f"{user.mention} ({user.display_name})",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Games đã reset:",
                value=f"{len(games_reset)} games" if games_reset else "Không có dữ liệu",
                inline=True
            )
            
            embed.add_field(
                name="💰 Tiền:",
                value="Giữ nguyên",
                inline=True
            )
            
            if games_reset:
                embed.add_field(
                    name="📁 Files đã cập nhật:",
                    value="\n".join([f"• {game}" for game in games_reset]),
                    inline=False
                )
            
            embed.set_footer(text="Reset System • Games Only")
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Games reset by {ctx.author.name}: User {user.name}, {len(games_reset)} games")
            
        except Exception as e:
            logger.error(f"Lỗi khi reset games user {user.id}: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra: {str(e)}", mention_author=True)
    
    async def reset_user_money_only(self, ctx, user):
        """Reset chỉ tiền, giữ nguyên lịch sử games"""
        try:
            current_money = 0
            if hasattr(self.bot_instance, 'shared_wallet'):
                current_money = self.bot_instance.shared_wallet.get_balance(user.id)
                self.bot_instance.shared_wallet.set_balance(user.id, 0)
            
            embed = discord.Embed(
                title="✅ Đã reset tiền",
                description=f"Tiền của {user.mention} đã được reset về 0",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User:",
                value=f"{user.mention} ({user.display_name})",
                inline=True
            )
            
            embed.add_field(
                name="💰 Tiền đã xóa:",
                value=f"{current_money:,} xu",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Lịch sử games:",
                value="Giữ nguyên",
                inline=True
            )
            
            embed.set_footer(text="Reset System • Money Only")
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Money reset by {ctx.author.name}: User {user.name}, {current_money} xu removed")
            
        except Exception as e:
            logger.error(f"Lỗi khi reset money user {user.id}: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra: {str(e)}", mention_author=True)
    
    async def show_reset_stats(self, ctx):
        """Hiển thị thống kê trước khi reset"""
        try:
            embed = discord.Embed(
                title="📊 Thống kê hệ thống",
                description="Tổng quan dữ liệu hiện tại trong hệ thống",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Thống kê tiền
            if hasattr(self.bot_instance, 'shared_wallet'):
                total_users = self.bot_instance.shared_wallet.get_user_count()
                total_money = self.bot_instance.shared_wallet.get_total_money_in_system()
                users_with_money = len(self.bot_instance.shared_wallet.get_all_users_with_money())
                
                embed.add_field(
                    name="💰 Thống kê tiền:",
                    value=f"• **{total_users:,}** users trong hệ thống\n• **{users_with_money:,}** users có tiền\n• **{total_money:,}** xu tổng cộng",
                    inline=False
                )
            
            # Thống kê files
            file_stats = []
            for file_name, file_path in self.data_files.items():
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                file_stats.append(f"• **{file_name}**: {len(data)} entries")
                            else:
                                file_stats.append(f"• **{file_name}**: Có dữ liệu")
                    except:
                        file_stats.append(f"• **{file_name}**: Lỗi đọc file")
                else:
                    file_stats.append(f"• **{file_name}**: Không tồn tại")
            
            embed.add_field(
                name="📁 Thống kê files:",
                value="\n".join(file_stats),
                inline=False
            )
            
            embed.add_field(
                name="🔧 Lệnh reset có sẵn:",
                value=(
                    "• `;resetuser [@user]` - Reset 1 user\n"
                    "• `;resetall` - Reset toàn bộ (Supreme Admin)\n"
                    "• `;resetgames [@user]` - Reset chỉ games\n"
                    "• `;resetmoney [@user]` - Reset chỉ tiền"
                ),
                inline=False
            )
            
            embed.set_footer(text="Reset System • Statistics")
            
            await ctx.reply(embed=embed, mention_author=True)
            
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị thống kê: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra: {str(e)}", mention_author=True)
    
    def get_user_games_data(self, user_id):
        """Lấy dữ liệu games của user từ tất cả files"""
        games_data = {}
        
        game_files = {k: v for k, v in self.data_files.items() if k != 'shared_wallet'}
        
        for game_name, file_path in game_files.items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if user_id in data:
                            games_data[game_name] = data[user_id]
                        else:
                            games_data[game_name] = None
                except:
                    games_data[game_name] = None
            else:
                games_data[game_name] = None
        
        return games_data
    
    def reset_user_from_file(self, user_id, file_path):
        """Reset user khỏi 1 file cụ thể"""
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if user_id in data:
                del data[user_id]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Lỗi khi reset user {user_id} từ file {file_path}: {e}")
            return False
