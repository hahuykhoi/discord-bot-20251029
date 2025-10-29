import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_commands, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_commands = giveaway_commands
        self.giveaway_id = giveaway_id
    
    @discord.ui.button(emoji='🎉', label='Tham gia', style=discord.ButtonStyle.primary, custom_id='join_giveaway')
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button tham gia giveaway"""
        await self.giveaway_commands.handle_join_giveaway(interaction, self.giveaway_id)
    
    @discord.ui.button(emoji='👥', label='Xem người tham gia', style=discord.ButtonStyle.secondary, custom_id='view_participants')
    async def view_participants(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button xem danh sách người tham gia"""
        await self.giveaway_commands.handle_view_participants(interaction, self.giveaway_id)

class GiveawayCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.data_file = 'data/giveaway_data.json'
        self.blacklist_file = 'data/giveaway_blacklist.json'
        self.giveaway_data = self.load_giveaway_data()
        self.blacklist_data = self.load_blacklist_data()
        
        # Đảm bảo thư mục data tồn tại
        os.makedirs('data', exist_ok=True)
    
    def load_giveaway_data(self):
        """Load dữ liệu giveaway từ file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"active_giveaways": {}, "completed_giveaways": {}}
        except Exception as e:
            logger.error(f"Lỗi khi load giveaway data: {e}")
            return {"active_giveaways": {}, "completed_giveaways": {}}
    
    def save_giveaway_data(self):
        """Lưu dữ liệu giveaway vào file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.giveaway_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu giveaway data: {e}")
    
    def load_blacklist_data(self):
        """Load dữ liệu blacklist từ file"""
        try:
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"blacklisted_users": []}
        except Exception as e:
            logger.error(f"Lỗi khi load blacklist data: {e}")
            return {"blacklisted_users": []}
    
    def save_blacklist_data(self):
        """Lưu dữ liệu blacklist vào file"""
        try:
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(self.blacklist_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu blacklist data: {e}")
    
    def is_user_blacklisted(self, user_id):
        """Kiểm tra user có bị blacklist không"""
        return user_id in self.blacklist_data.get("blacklisted_users", [])
    
    def generate_giveaway_id(self):
        """Tạo ID duy nhất cho giveaway"""
        import time
        return f"gw_{int(time.time())}_{random.randint(1000, 9999)}"
    
    async def handle_join_giveaway(self, interaction, giveaway_id):
        """Xử lý khi user tham gia giveaway"""
        user_id = interaction.user.id
        
        # Kiểm tra giveaway có tồn tại không
        if giveaway_id not in self.giveaway_data["active_giveaways"]:
            await interaction.response.send_message("❌ Giveaway này không tồn tại hoặc đã kết thúc!", ephemeral=True)
            return
        
        giveaway = self.giveaway_data["active_giveaways"][giveaway_id]
        
        # Kiểm tra giveaway đã kết thúc chưa
        end_time = datetime.fromisoformat(giveaway["end_time"])
        if datetime.now() >= end_time:
            await interaction.response.send_message("❌ Giveaway này đã kết thúc!", ephemeral=True)
            return
        
        # Kiểm tra user có bị blacklist không
        if self.is_user_blacklisted(user_id):
            await interaction.response.send_message("❌ Bạn đã bị cấm tham gia giveaway!", ephemeral=True)
            return
        
        # Kiểm tra user đã tham gia chưa
        if user_id in giveaway["participants"]:
            await interaction.response.send_message("❌ Bạn đã tham gia giveaway này rồi!", ephemeral=True)
            return
        
        # Thêm user vào danh sách tham gia
        giveaway["participants"].append(user_id)
        self.save_giveaway_data()
        
        await interaction.response.send_message("✅ Bạn đã tham gia giveaway thành công! 🎉", ephemeral=True)
        logger.info(f"User {user_id} joined giveaway {giveaway_id}")
    
    async def handle_view_participants(self, interaction, giveaway_id):
        """Xử lý khi xem danh sách người tham gia"""
        # Kiểm tra giveaway có tồn tại không
        if giveaway_id not in self.giveaway_data["active_giveaways"]:
            await interaction.response.send_message("❌ Giveaway này không tồn tại hoặc đã kết thúc!", ephemeral=True)
            return
        
        giveaway = self.giveaway_data["active_giveaways"][giveaway_id]
        participants = giveaway["participants"]
        
        if not participants:
            await interaction.response.send_message("📝 Chưa có ai tham gia giveaway này!", ephemeral=True)
            return
        
        # Tạo embed hiển thị người tham gia
        embed = discord.Embed(
            title="👥 Danh sách người tham gia",
            description=f"**Giveaway:** {giveaway['prize']}\n**Tổng số người tham gia:** {len(participants)}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Hiển thị tối đa 20 người đầu tiên
        participant_list = []
        for i, user_id in enumerate(participants[:20]):
            try:
                user = self.bot.get_user(user_id)
                if user:
                    participant_list.append(f"{i+1}. {user.display_name}")
                else:
                    participant_list.append(f"{i+1}. User {user_id}")
            except:
                participant_list.append(f"{i+1}. User {user_id}")
        
        embed.add_field(
            name="🎯 Người tham gia",
            value="\n".join(participant_list) if participant_list else "Không có",
            inline=False
        )
        
        if len(participants) > 20:
            embed.add_field(
                name="📊 Thông tin thêm",
                value=f"Và {len(participants) - 20} người khác...",
                inline=False
            )
        
        embed.set_footer(text="Giveaway System • Danh sách người tham gia")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def end_giveaway(self, giveaway_id):
        """Kết thúc giveaway và chọn người thắng"""
        if giveaway_id not in self.giveaway_data["active_giveaways"]:
            return
        
        giveaway = self.giveaway_data["active_giveaways"][giveaway_id]
        participants = giveaway["participants"]
        
        # Chuyển giveaway sang completed
        self.giveaway_data["completed_giveaways"][giveaway_id] = giveaway.copy()
        self.giveaway_data["completed_giveaways"][giveaway_id]["completed_at"] = datetime.now().isoformat()
        
        # Chọn người thắng
        winners = []
        if participants:
            num_winners = min(giveaway["winners"], len(participants))
            winners = random.sample(participants, num_winners)
            self.giveaway_data["completed_giveaways"][giveaway_id]["winners"] = winners
        
        # Xóa khỏi active giveaways
        del self.giveaway_data["active_giveaways"][giveaway_id]
        self.save_giveaway_data()
        
        # Gửi thông báo kết quả
        try:
            channel = self.bot.get_channel(giveaway["channel_id"])
            if channel:
                embed = discord.Embed(
                    title="🎉 GIVEAWAY KẾT THÚC!",
                    description=f"**Giải thưởng:** {giveaway['prize']}",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                if winners:
                    winner_mentions = []
                    for winner_id in winners:
                        user = self.bot.get_user(winner_id)
                        if user:
                            winner_mentions.append(user.mention)
                        else:
                            winner_mentions.append(f"<@{winner_id}>")
                    
                    embed.add_field(
                        name="🏆 Người thắng cuộc",
                        value="\n".join(winner_mentions),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="🎊 Chúc mừng!",
                        value="Hãy liên hệ admin để nhận giải thưởng!",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="😢 Không có người thắng",
                        value="Không có ai tham gia giveaway này!",
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Thống kê",
                    value=f"**Tổng người tham gia:** {len(participants)}\n**Số người thắng:** {len(winners)}",
                    inline=False
                )
                
                embed.set_footer(text="Giveaway System • Kết thúc")
                
                await channel.send(embed=embed)
                
                # Ping winners
                if winners:
                    winner_pings = " ".join([f"<@{winner_id}>" for winner_id in winners])
                    await channel.send(f"🎉 {winner_pings} Chúc mừng bạn đã thắng giveaway!")
        
        except Exception as e:
            logger.error(f"Lỗi khi gửi thông báo kết thúc giveaway {giveaway_id}: {e}")
    
    def register_commands(self):
        """Đăng ký các slash commands"""
        
        @self.bot.tree.command(name="giveaway", description="Tạo giveaway mới")
        @app_commands.describe(
            winners="Số lượng người thắng",
            duration="Thời gian (phút)",
            prize="Giải thưởng"
        )
        async def giveaway_command(interaction: discord.Interaction, winners: int, duration: int, prize: str):
            """Tạo giveaway mới"""
            # Kiểm tra quyền admin
            if not self.bot_instance.is_admin(interaction.user.id):
                await interaction.response.send_message("❌ Chỉ Admin mới có thể tạo giveaway!", ephemeral=True)
                return
            
            # Validate input
            if winners <= 0:
                await interaction.response.send_message("❌ Số người thắng phải lớn hơn 0!", ephemeral=True)
                return
            
            if duration <= 0:
                await interaction.response.send_message("❌ Thời gian phải lớn hơn 0 phút!", ephemeral=True)
                return
            
            if len(prize.strip()) == 0:
                await interaction.response.send_message("❌ Giải thưởng không được để trống!", ephemeral=True)
                return
            
            # Tạo giveaway
            giveaway_id = self.generate_giveaway_id()
            end_time = datetime.now() + timedelta(minutes=duration)
            
            giveaway_data = {
                "id": giveaway_id,
                "host_id": interaction.user.id,
                "channel_id": interaction.channel.id,
                "guild_id": interaction.guild.id,
                "prize": prize.strip(),
                "winners": winners,
                "duration": duration,
                "start_time": datetime.now().isoformat(),
                "end_time": end_time.isoformat(),
                "participants": []
            }
            
            self.giveaway_data["active_giveaways"][giveaway_id] = giveaway_data
            self.save_giveaway_data()
            
            # Tạo embed giveaway
            embed = discord.Embed(
                title="🎉 GIVEAWAY!",
                description=f"**Giải thưởng:** {prize}",
                color=discord.Color.gold(),
                timestamp=end_time
            )
            
            embed.add_field(
                name="🏆 Số người thắng",
                value=f"{winners} người",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Thời gian",
                value=f"{duration} phút",
                inline=True
            )
            
            embed.add_field(
                name="👥 Người tham gia",
                value="0 người",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Cách tham gia",
                value="Nhấn nút 🎉 bên dưới để tham gia!",
                inline=False
            )
            
            embed.set_footer(text="Kết thúc lúc")
            embed.set_author(
                name=f"Tạo bởi {interaction.user.display_name}",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            
            # Tạo view với buttons
            view = GiveawayView(self, giveaway_id)
            
            await interaction.response.send_message(embed=embed, view=view)
            
            # Lên lịch kết thúc giveaway
            asyncio.create_task(self.schedule_giveaway_end(giveaway_id, duration * 60))
            
            logger.info(f"Giveaway {giveaway_id} created by {interaction.user.id} - Prize: {prize}, Winners: {winners}, Duration: {duration}m")
        
        @self.bot.tree.command(name="giveaway_blacklist", description="Blacklist user khỏi giveaway")
        @app_commands.describe(user="User cần blacklist")
        async def giveaway_blacklist_command(interaction: discord.Interaction, user: discord.Member):
            """Blacklist user khỏi giveaway"""
            # Kiểm tra quyền admin
            if not self.bot_instance.is_admin(interaction.user.id):
                await interaction.response.send_message("❌ Chỉ Admin mới có thể blacklist user!", ephemeral=True)
                return
            
            # Kiểm tra không thể blacklist chính mình
            if user.id == interaction.user.id:
                await interaction.response.send_message("❌ Bạn không thể blacklist chính mình!", ephemeral=True)
                return
            
            # Kiểm tra không thể blacklist admin khác
            if self.bot_instance.is_admin(user.id):
                await interaction.response.send_message("❌ Không thể blacklist Admin khác!", ephemeral=True)
                return
            
            # Kiểm tra user đã bị blacklist chưa
            if self.is_user_blacklisted(user.id):
                await interaction.response.send_message(f"❌ {user.mention} đã bị blacklist rồi!", ephemeral=True)
                return
            
            # Thêm vào blacklist
            self.blacklist_data["blacklisted_users"].append(user.id)
            self.save_blacklist_data()
            
            embed = discord.Embed(
                title="🚫 User đã bị blacklist",
                description=f"**User:** {user.mention}\n**Bởi:** {interaction.user.mention}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📝 Thông tin",
                value="User này không thể tham gia bất kỳ giveaway nào!",
                inline=False
            )
            
            embed.set_footer(text="Giveaway System • Blacklist")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user.id} blacklisted from giveaways by {interaction.user.id}")
        
        @self.bot.tree.command(name="giveaway_unblacklist", description="Gỡ blacklist user khỏi giveaway")
        @app_commands.describe(user="User cần gỡ blacklist")
        async def giveaway_unblacklist_command(interaction: discord.Interaction, user: discord.Member):
            """Gỡ blacklist user khỏi giveaway"""
            # Kiểm tra quyền admin
            if not self.bot_instance.is_admin(interaction.user.id):
                await interaction.response.send_message("❌ Chỉ Admin mới có thể gỡ blacklist user!", ephemeral=True)
                return
            
            # Kiểm tra user có bị blacklist không
            if not self.is_user_blacklisted(user.id):
                await interaction.response.send_message(f"❌ {user.mention} không bị blacklist!", ephemeral=True)
                return
            
            # Gỡ khỏi blacklist
            self.blacklist_data["blacklisted_users"].remove(user.id)
            self.save_blacklist_data()
            
            embed = discord.Embed(
                title="✅ Đã gỡ blacklist user",
                description=f"**User:** {user.mention}\n**Bởi:** {interaction.user.mention}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📝 Thông tin",
                value="User này có thể tham gia giveaway trở lại!",
                inline=False
            )
            
            embed.set_footer(text="Giveaway System • Unblacklist")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user.id} unblacklisted from giveaways by {interaction.user.id}")
        
        @self.bot.tree.command(name="giveaway_list", description="Xem danh sách giveaway đang diễn ra")
        async def giveaway_list_command(interaction: discord.Interaction):
            """Xem danh sách giveaway đang diễn ra"""
            active_giveaways = self.giveaway_data["active_giveaways"]
            
            if not active_giveaways:
                await interaction.response.send_message("📝 Hiện tại không có giveaway nào đang diễn ra!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🎉 Danh sách Giveaway đang diễn ra",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            for giveaway_id, giveaway in active_giveaways.items():
                end_time = datetime.fromisoformat(giveaway["end_time"])
                time_left = end_time - datetime.now()
                
                if time_left.total_seconds() > 0:
                    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"{hours}h {minutes}m {seconds}s"
                else:
                    time_str = "Đã kết thúc"
                
                embed.add_field(
                    name=f"🎁 {giveaway['prize']}",
                    value=(
                        f"**Người thắng:** {giveaway['winners']}\n"
                        f"**Tham gia:** {len(giveaway['participants'])}\n"
                        f"**Thời gian còn lại:** {time_str}"
                    ),
                    inline=True
                )
            
            embed.set_footer(text="Giveaway System • Danh sách")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def schedule_giveaway_end(self, giveaway_id, delay_seconds):
        """Lên lịch kết thúc giveaway"""
        await asyncio.sleep(delay_seconds)
        await self.end_giveaway(giveaway_id)
