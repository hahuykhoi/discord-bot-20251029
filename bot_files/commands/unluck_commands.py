import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UnluckCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.unluck_data_file = 'data/unluck_data.json'
        self.unluck_data = self.load_unluck_data()
        
        # Cấu hình - unluck vĩnh viễn cho đến khi xóa
        self.max_duration_hours = 999999  # Không giới hạn thời gian
        self.min_duration_minutes = 1  # Tối thiểu 1 phút
        self.cooldown_hours = 0  # Không có cooldown
        self.max_uses_per_day = 999  # Không giới hạn số lần
    
    def load_unluck_data(self):
        """Load unluck data from JSON file"""
        if os.path.exists(self.unluck_data_file):
            try:
                with open(self.unluck_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {
                    "unlucky_users": {},
                    "usage_history": {},
                    "admin_usage": {}
                }
        return {
            "unlucky_users": {},
            "usage_history": {},
            "admin_usage": {}
        }
    
    def save_unluck_data(self):
        """Save unluck data to JSON file"""
        os.makedirs(os.path.dirname(self.unluck_data_file), exist_ok=True)
        with open(self.unluck_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.unluck_data, f, ensure_ascii=False, indent=2)
    
    def is_user_unlucky(self, user_id):
        """Kiểm tra user có đang bị unluck không - unluck vĩnh viễn"""
        user_str = str(user_id)
        if user_str not in self.unluck_data["unlucky_users"]:
            return False
        
        # Unluck vĩnh viễn - không kiểm tra thời gian hết hạn
        return True
    
    def get_unluck_info(self, user_id):
        """Lấy thông tin unluck của user"""
        user_str = str(user_id)
        if user_str in self.unluck_data["unlucky_users"]:
            return self.unluck_data["unlucky_users"][user_str]
        return None
    
    def can_admin_use_unluck(self, admin_id):
        """Admin luôn có thể sử dụng unluck - không có giới hạn"""
        return True, "OK"
    
    def add_unlucky_user(self, admin_id, target_id, reason=""):
        """Thêm user vào danh sách unlucky - vĩnh viễn"""
        target_str = str(target_id)
        now = datetime.now()
        
        # Thêm vào danh sách unlucky - vĩnh viễn
        self.unluck_data["unlucky_users"][target_str] = {
            "admin_id": admin_id,
            "start_time": now.isoformat(),
            "reason": reason,
            "games_affected": 0
        }
        
        # Cập nhật usage history
        if target_str not in self.unluck_data["usage_history"]:
            self.unluck_data["usage_history"][target_str] = []
        
        self.unluck_data["usage_history"][target_str].append({
            "admin_id": admin_id,
            "start_time": now.isoformat(),
            "reason": reason
        })
        
        self.save_unluck_data()
    
    def remove_unlucky_user(self, user_id):
        """Xóa user khỏi danh sách unlucky"""
        user_str = str(user_id)
        if user_str in self.unluck_data["unlucky_users"]:
            del self.unluck_data["unlucky_users"][user_str]
            self.save_unluck_data()
            return True
        return False
    
    def increment_game_affected(self, user_id):
        """Tăng số game bị ảnh hưởng"""
        user_str = str(user_id)
        if user_str in self.unluck_data["unlucky_users"]:
            self.unluck_data["unlucky_users"][user_str]["games_affected"] += 1
            self.save_unluck_data()
    
    def register_commands(self):
        """Register all unluck commands"""
        
        @self.bot.command(name='unluck')
        async def unluck_command(ctx, action=None, target: discord.Member = None, *, reason=""):
            """Quản lý hệ thống unluck"""
            
            if action == "add" and target:
                await self.add_unluck(ctx, target, reason)
            elif action == "remove" and target:
                await self.remove_unluck(ctx, target)
            elif action == "list":
                await self.list_unlucky_users(ctx)
            elif action == "check" and target:
                await self.check_unluck_status(ctx, target)
            elif action == "history" and target:
                await self.show_unluck_history(ctx, target)
            elif action == "stats":
                await self.show_unluck_stats(ctx)
            else:
                await self.show_unluck_help(ctx)
        
    
    async def show_unluck_help(self, ctx):
        """Hiển thị hướng dẫn sử dụng unluck"""
        embed = discord.Embed(
            title="🎲 Hệ thống Unluck",
            description="Làm cho ai đó 100% thua trong tất cả game",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🔧 Lệnh Admin:",
            value=(
                "• ; add @user [lý do]` - Thêm unluck vĩnh viễn\n"
                "• ; remove @user` - Xóa unluck\n"
                "• ; list` - Xem danh sách unlucky\n"
                "• ; check @user` - Kiểm tra trạng thái\n"
                "• ; history @user` - Xem lịch sử\n"
                "• ; stats` - Thống kê hệ thống"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎮 Game bị ảnh hưởng:",
            value=(
                "• **Tài Xỉu** - Luôn thua\n"
                "• **Slot Machine** - Không bao giờ Jackpot\n"
                "• **Blackjack** - Luôn bị bust hoặc thua dealer\n"
                "• **Rock Paper Scissors** - Luôn chọn sai\n"
                "• **Flip Coin** - Luôn đoán sai\n"
                "• **Tất cả game khác** - 100% thua"
            ),
            inline=False
        )
        
        embed.set_footer(
            text="Unluck vĩnh viễn • Chỉ Admin có thể gỡ bỏ",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def add_unluck(self, ctx, target, reason):
        """Thêm unluck cho user"""
        # Kiểm tra quyền admin
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể sử dụng lệnh này!", mention_author=True)
            return
        
        # Kiểm tra không thể unluck chính mình
        if target.id == ctx.author.id:
            await ctx.reply("❌ Không thể unluck chính mình!", mention_author=True)
            return
        
        # Kiểm tra không thể unluck admin khác
        if self.bot_instance.is_admin(target.id):
            await ctx.reply("❌ Không thể unluck Admin khác!", mention_author=True)
            return
        
        # Unluck vĩnh viễn - không cần kiểm tra thời gian
        
        # Kiểm tra chống lạm dụng
        can_use, message = self.can_admin_use_unluck(ctx.author.id)
        if not can_use:
            await ctx.reply(f"❌ {message}", mention_author=True)
            return
        
        # Kiểm tra user đã bị unluck chưa
        if self.is_user_unlucky(target.id):
            await ctx.reply(f"❌ {target.mention} đã bị unluck rồi!", mention_author=True)
            return
        
        # Thêm unluck vĩnh viễn
        self.add_unlucky_user(ctx.author.id, target.id, reason)
        
        # Thông báo ngắn gọn cho admin - không thông báo cho user
        await ctx.reply(f"✅ Đã unluck {target.mention}", mention_author=True)
    
    async def remove_unluck(self, ctx, target):
        """Xóa unluck của user"""
        # Kiểm tra quyền admin
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể sử dụng lệnh này!", mention_author=True)
            return
        
        # Kiểm tra user có bị unluck không
        if not self.is_user_unlucky(target.id):
            await ctx.reply(f"❌ {target.mention} không bị unluck!", mention_author=True)
            return
        
        # Xóa unluck
        self.remove_unlucky_user(target.id)
        
        # Thông báo ngắn gọn cho admin - không thông báo cho user
        await ctx.reply(f"✅ Đã gỡ unluck {target.mention}", mention_author=True)
    
    async def check_unluck_status(self, ctx, target):
        """Kiểm tra trạng thái unluck của user"""
        if self.is_user_unlucky(target.id):
            unluck_info = self.get_unluck_info(target.id)
            
            embed = discord.Embed(
                title="💀 User đang bị Unluck",
                description=f"{target.mention} đang bị unluck vĩnh viễn",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="⏳ Thời gian:",
                value="Vĩnh viễn",
                inline=True
            )
            
            embed.add_field(
                name="📊 Game bị ảnh hưởng:",
                value=f"{unluck_info['games_affected']} game",
                inline=True
            )
            
            if unluck_info.get("reason"):
                embed.add_field(
                    name="📝 Lý do:",
                    value=unluck_info["reason"],
                    inline=False
                )
            
        else:
            embed = discord.Embed(
                title="🍀 User Lucky",
                description=f"{target.mention} không bị unluck",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="✅ Trạng thái:",
                value="Có thể chơi game bình thường",
                inline=False
            )
        
        embed.set_footer(
            text=f"Kiểm tra bởi {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def list_unlucky_users(self, ctx):
        """Liệt kê tất cả user đang bị unluck"""
        # Kiểm tra quyền admin
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể xem danh sách này!", mention_author=True)
            return
        
        unlucky_users = []
        for user_id, info in self.unluck_data["unlucky_users"].items():
            # Unluck vĩnh viễn - không cần kiểm tra thời gian hết hạn
            user = ctx.guild.get_member(int(user_id))
            if user:
                start_time = datetime.fromisoformat(info["start_time"])
                unlucky_users.append({
                    "user": user,
                    "start_time": start_time,
                    "info": info
                })
        
        embed = discord.Embed(
            title="💀 Danh sách User Unlucky",
            description=f"Có {len(unlucky_users)} user đang bị unluck vĩnh viễn",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        if unlucky_users:
            user_list = []
            for i, data in enumerate(unlucky_users[:10], 1):  # Giới hạn 10 user
                user = data["user"]
                start_time = data["start_time"]
                games_affected = data["info"]["games_affected"]
                reason = data["info"].get("reason", "Không có lý do")
                
                # Tính thời gian đã bị unluck
                duration = datetime.now() - start_time
                days = duration.days
                hours = duration.seconds // 3600
                
                user_list.append(
                    f"{i}. **{user.name}** - "
                    f"Vĩnh viễn ({days}d {hours}h) - "
                    f"{games_affected} games"
                )
            
            embed.add_field(
                name="👥 Unlucky Users:",
                value="\n".join(user_list),
                inline=False
            )
            
            if len(unlucky_users) > 10:
                embed.add_field(
                    name="📝 Lưu ý:",
                    value=f"Chỉ hiển thị 10/{len(unlucky_users)} user",
                    inline=False
                )
        else:
            embed.add_field(
                name="✅ Trạng thái:",
                value="Không có user nào bị unluck",
                inline=False
            )
        
        embed.set_footer(text="Unluck System • Admin Only • Vĩnh viễn")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def show_unluck_history(self, ctx, target):
        """Hiển thị lịch sử unluck của user"""
        # Kiểm tra quyền admin
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể xem lịch sử!", mention_author=True)
            return
        
        user_str = str(target.id)
        history = self.unluck_data["usage_history"].get(user_str, [])
        
        embed = discord.Embed(
            title="📜 Lịch sử Unluck",
            description=f"Lịch sử unluck của {target.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        if history:
            history_list = []
            for i, record in enumerate(history[-5:], 1):  # 5 lần gần nhất
                start_time = datetime.fromisoformat(record["start_time"])
                admin = ctx.guild.get_member(record["admin_id"])
                admin_name = admin.name if admin else f"ID: {record['admin_id']}"
                reason = record.get("reason", "Không có lý do")
                
                history_list.append(
                    f"{i}. **Vĩnh viễn** - "
                    f"<t:{int(start_time.timestamp())}:d> - "
                    f"by {admin_name}"
                    f"{f' - {reason}' if reason != 'Không có lý do' else ''}"
                )
            
            embed.add_field(
                name="📋 Lịch sử (5 lần gần nhất):",
                value="\n".join(history_list),
                inline=False
            )
            
            embed.add_field(
                name="📊 Thống kê:",
                value=f"Tổng số lần: {len(history)}",
                inline=True
            )
        else:
            embed.add_field(
                name="📝 Trạng thái:",
                value="Chưa từng bị unluck",
                inline=False
            )
        
        embed.set_footer(text="Unluck System • History • Vĩnh viễn")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def show_unluck_stats(self, ctx):
        """Hiển thị thống kê hệ thống unluck"""
        # Kiểm tra quyền admin
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể xem thống kê!", mention_author=True)
            return
        
        # Tính toán thống kê
        total_unlucky = len(self.unluck_data["unlucky_users"])
        total_history = sum(len(history) for history in self.unluck_data["usage_history"].values())
        total_admins = len(self.unluck_data["admin_usage"])
        
        embed = discord.Embed(
            title="📊 Thống kê Unluck System",
            description="Thống kê tổng quan hệ thống unluck",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="💀 Hiện tại:",
            value=f"{total_unlucky} user đang unlucky",
            inline=True
        )
        
        embed.add_field(
            name="📜 Lịch sử:",
            value=f"{total_history} lần sử dụng",
            inline=True
        )
        
        embed.add_field(
            name="👨‍💼 Admin:",
            value=f"{total_admins} admin đã sử dụng",
            inline=True
        )
        
        # Top admin sử dụng nhiều nhất
        admin_usage_count = {}
        for admin_id, data in self.unluck_data["admin_usage"].items():
            total_uses = sum(data["daily_usage"].values())
            admin_usage_count[admin_id] = total_uses
        
        if admin_usage_count:
            top_admin = max(admin_usage_count.items(), key=lambda x: x[1])
            admin = ctx.guild.get_member(int(top_admin[0]))
            admin_name = admin.name if admin else f"ID: {top_admin[0]}"
            
            embed.add_field(
                name="🏆 Top Admin:",
                value=f"{admin_name} ({top_admin[1]} lần)",
                inline=True
            )
        
        embed.add_field(
            name="⚙️ Cấu hình:",
            value=(
                f"• Max duration: {self.max_duration_hours}h\n"
                f"• Cooldown: {self.cooldown_hours}h\n"
                f"• Daily limit: {self.max_uses_per_day}/day"
            ),
            inline=False
        )
        
        embed.set_footer(text="Unluck System • Statistics")
        
        await ctx.reply(embed=embed, mention_author=True)
