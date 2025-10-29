import discord
import json
import os
import time
from datetime import datetime

class GetKeyCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        
        # Cấu hình hệ thống
        
        # Giới hạn sử dụng
        self.MAX_USAGE_COUNT = 5  # Tối đa 5 lần getkey và nhận thưởng
        
        # File lưu trữ
        self.user_keys_file = 'data/user_keys.json'
        self.user_keys = self.load_user_keys()
        
    def load_user_keys(self):
        """Load user keys data"""
        if os.path.exists(self.user_keys_file):
            try:
                with open(self.user_keys_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_user_keys(self):
        """Save user keys data"""
        os.makedirs(os.path.dirname(self.user_keys_file), exist_ok=True)
        with open(self.user_keys_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_keys, f, ensure_ascii=False, indent=2)
    
    
    def register_commands(self):
        """Đăng ký các lệnh"""
        
        @self.bot.command(name='getkey')
        async def getkey_command(ctx):
            """Tự động nhận 500k xu sau 70 giây hoặc tạo key để check thủ công"""
            user_id = ctx.author.id
            user_id_str = str(user_id)
            current_time = int(time.time())
            
            # Kiểm tra có bị cấm không
            if user_id_str in self.user_keys:
                ban_until = self.user_keys[user_id_str].get('banned_until', 0)
                if current_time < ban_until:
                    remaining = ban_until - current_time
                    minutes = remaining // 60
                    seconds = remaining % 60
                    
                    await ctx.reply(
                        f"🚫 **Bạn đã bị cấm sử dụng GetKey!**\n\n"
                        f"⏰ **Thời gian còn lại:** {minutes}m {seconds}s\n"
                        f"❌ **Lý do:** Spam hoặc lạm dụng hệ thống\n"
                        f"💡 **Lưu ý:** Vui lòng sử dụng dịch vụ một cách hợp lệ",
                        mention_author=True
                    )
                    return
                
                # Kiểm tra giới hạn sử dụng
                usage_count = self.user_keys[user_id_str].get('usage_count', 0)
                if usage_count >= self.MAX_USAGE_COUNT:
                    await ctx.reply(
                        f"🚫 **Đã hết lượt sử dụng GetKey!**\n\n"
                        f"📊 **Thống kê của bạn:**\n"
                        f"• Đã sử dụng: **{usage_count}/{self.MAX_USAGE_COUNT}** lần\n"
                        f"• Tổng xu nhận được: **{usage_count * 500000:,}** xu\n\n"
                        f"💡 **Lưu ý:** Mỗi user chỉ được sử dụng tối đa {self.MAX_USAGE_COUNT} lần",
                        mention_author=True
                    )
                    return
                
                # Kiểm tra cooldown (để tránh spam)
                last_getkey = self.user_keys[user_id_str].get('last_getkey_time', 0)
                cooldown_time = 300  # 5 phút cooldown
                if current_time - last_getkey < cooldown_time:
                    remaining_cooldown = cooldown_time - (current_time - last_getkey)
                    minutes = remaining_cooldown // 60
                    seconds = remaining_cooldown % 60
                    
                    await ctx.reply(
                        f"⏰ **Vui lòng chờ cooldown!**\n\n"
                        f"🕐 **Thời gian còn lại:** {minutes}m {seconds}s\n"
                        f"💡 **Lưu ý:** Mỗi lần getkey cách nhau 5 phút",
                        mention_author=True
                    )
                    return
            
            # Khởi tạo user data nếu chưa có
            if user_id_str not in self.user_keys:
                self.user_keys[user_id_str] = {
                    'usage_count': 0,
                    'total_rewards': 0,
                    'banned_until': 0
                }
            
            # Cập nhật thông tin user
            self.user_keys[user_id_str]['last_getkey_time'] = current_time
            self.user_keys[user_id_str]['key_already_checked'] = False  # Reset trạng thái
            self.save_user_keys()
            
            # Thông báo bắt đầu với key
            current_usage = self.user_keys[user_id_str].get('usage_count', 0)
            remaining_uses = self.MAX_USAGE_COUNT - current_usage
            
            success_embed = discord.Embed(
                title="✅ GetKey đã được tạo!",
                description=f"Xin chào {ctx.author.mention}! Timestamp đã được ghi nhận.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="📋 Hướng dẫn:",
                value=(
                    "1️⃣ Lấy key từ nguồn bên ngoài (link4m, etc.)\n"
                    "2️⃣ Dùng `;checkkey <key>` để nhận 500,000 xu\n"
                    "3️⃣ Phải chờ ít nhất **70 giây** sau lệnh này"
                ),
                inline=False
            )
            
            success_embed.add_field(
                name="⚠️ Cảnh báo:",
                value="**Nghiêm cấm bypass!** Nếu check key dưới 70 giây sẽ bị cấm 1 giờ",
                inline=False
            )
            
            success_embed.add_field(
                name="📊 Thống kê:",
                value=f"**Lượt còn lại:** {remaining_uses}/{self.MAX_USAGE_COUNT}",
                inline=False
            )
            
            success_embed.add_field(
                name="⏰ Thời gian tạo:",
                value=f"<t:{current_time}:T> (<t:{current_time}:R>)",
                inline=False
            )
            
            success_embed.set_footer(
                text="Bây giờ bạn có thể đi lấy key từ nguồn khác!",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=success_embed, mention_author=True)
        
        @self.bot.command(name='checkkey')
        async def checkkey_command(ctx, *, key_input=None):
            """Check key thủ công và nhận 500k xu ngay lập tức"""
            if not key_input:
                await ctx.reply(
                    "❌ **Cách sử dụng:**\n"
                    "`;checkkey <key>`\n\n"
                    "**Ví dụ:** `;checkkey mttoolsrv-abc123def456`\n\n"
                    "💡 **Lưu ý:** \n"
                    "• Phải dùng `;getkey` trước và chờ ít nhất 70 giây\n"
                    "• Key phải lấy từ nguồn bên ngoài (link4m, etc.)\n"
                    "• Bypass detection sẽ cấm 1 giờ!",
                    mention_author=True
                )
                return
            
            user_id = ctx.author.id
            user_id_str = str(user_id)
            current_time = int(time.time())
            
            # Kiểm tra có bị cấm không
            if user_id_str in self.user_keys:
                ban_until = self.user_keys[user_id_str].get('banned_until', 0)
                if current_time < ban_until:
                    remaining = ban_until - current_time
                    minutes = remaining // 60
                    seconds = remaining % 60
                    
                    await ctx.reply(
                        f"🚫 **Bạn đã bị cấm sử dụng GetKey!**\n\n"
                        f"⏰ **Thời gian còn lại:** {minutes}m {seconds}s\n"
                        f"❌ **Lý do:** Spam hoặc lạm dụng hệ thống\n"
                        f"💡 **Lưu ý:** Vui lòng sử dụng dịch vụ một cách hợp lệ",
                        mention_author=True
                    )
                    return
                
                # Kiểm tra giới hạn sử dụng
                usage_count = self.user_keys[user_id_str].get('usage_count', 0)
                if usage_count >= self.MAX_USAGE_COUNT:
                    await ctx.reply(
                        f"🚫 **Đã hết lượt nhận thưởng GetKey!**\n\n"
                        f"📊 **Thống kê của bạn:**\n"
                        f"• Đã nhận thưởng: **{usage_count}/{self.MAX_USAGE_COUNT}** lần\n"
                        f"• Tổng xu đã nhận: **{usage_count * 500000:,}** xu\n\n"
                        f"💡 **Lưu ý:** Mỗi user chỉ được nhận thưởng tối đa {self.MAX_USAGE_COUNT} lần",
                        mention_author=True
                    )
                    return
                
                # Kiểm tra đã check key này rồi chưa
                if self.user_keys[user_id_str].get('key_already_checked', False):
                    await ctx.reply(
                        "❌ **Bạn đã check key và nhận thưởng rồi!**\n\n"
                        "💡 **Lưu ý:** Mỗi lần getkey chỉ có thể nhận thưởng 1 lần\n"
                        "🔄 **Sử dụng:** `;getkey` để tạo key mới",
                        mention_author=True
                    )
                    return
                
                # BYPASS DETECTION - Kiểm tra thời gian giữa getkey và checkkey
                last_getkey_time = self.user_keys[user_id_str].get('last_getkey_time', 0)
                if last_getkey_time > 0:  # Nếu user đã dùng getkey
                    time_diff = current_time - last_getkey_time
                    if time_diff < 70:  # Nếu checkkey trong vòng 70s sau getkey
                        # Cấm user 1 giờ
                        ban_until = current_time + 3600  # 1 giờ = 3600 giây
                        self.user_keys[user_id_str]['banned_until'] = ban_until
                        self.user_keys[user_id_str]['bypass_detected'] = True
                        self.user_keys[user_id_str]['bypass_time'] = current_time
                        self.save_user_keys()
                        
                        await ctx.reply(
                            f"🚫 **PHÁT HIỆN HÀNH VI BYPASS!**\n\n"
                            f"⚠️ **Bạn đã bị cấm sử dụng GetKey trong 1 giờ!**\n\n"
                            f"❌ **Lý do:** Bypass detection - Checkkey quá nhanh ({time_diff}s < 70s)\n"
                            f"🔓 **Mở khóa lúc:** <t:{ban_until}:T>\n\n"
                            f"💡 **Lưu ý:** Phải chờ ít nhất 70 giây sau `;getkey` mới được `;checkkey`",
                            mention_author=True
                        )
                        return
            
            # Kiểm tra format key (phải bắt đầu với mttoolsrv-)
            if not key_input.startswith("mttoolsrv-"):
                await ctx.reply(
                    "❌ **Format key không đúng!**\n\n"
                    "🔑 **Format đúng:** `mttoolsrv-xxxxxxxxxx`\n"
                    "💡 **Lưu ý:** Key phải có format mttoolsrv- ở đầu",
                    mention_author=True
                )
                return
            
            # Kiểm tra độ dài key hợp lệ
            if len(key_input) < 15:
                await ctx.reply(
                    "❌ **Key quá ngắn!**\n\n"
                    "🔑 **Độ dài tối thiểu:** 15 ký tự\n"
                    "💡 **Lưu ý:** Key hợp lệ phải có đủ độ dài",
                    mention_author=True
                )
                return
            
            # Key đúng - trao thưởng ngay lập tức
            await ctx.reply("🔄 **Đang xử lý key...**", mention_author=True)
            
            # Cập nhật dữ liệu user
            current_usage = self.user_keys[user_id_str].get('usage_count', 0)
            new_usage = current_usage + 1
            
            self.user_keys[user_id_str]['key_already_checked'] = True
            self.user_keys[user_id_str]['check_time'] = current_time
            self.user_keys[user_id_str]['usage_count'] = new_usage
            self.user_keys[user_id_str]['total_rewards'] = new_usage * 500000
            self.save_user_keys()
            
            # Thêm 500k xu cho user
            if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
                self.bot_instance.shared_wallet.add_balance(user_id, 500000)
            
            # Thông báo thành công
            success_embed = discord.Embed(
                title="✅ Check Key Thành Công!",
                description=f"Chúc mừng {ctx.author.mention} đã check key và nhận thưởng!",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="🎁 Phần thưởng:",
                value="**+500,000 xu** đã được thêm vào tài khoản",
                inline=False
            )
            
            success_embed.add_field(
                name="🔑 Key đã check:",
                value=f"`{key_input}`",
                inline=False
            )
            
            success_embed.add_field(
                name="📊 Thống kê:",
                value=f"**{new_usage}/{self.MAX_USAGE_COUNT}** lần đã sử dụng",
                inline=True
            )
            
            success_embed.add_field(
                name="💰 Tổng đã nhận:",
                value=f"**{new_usage * 500000:,}** xu",
                inline=True
            )
            
            # Kiểm tra còn lượt không
            remaining_uses = self.MAX_USAGE_COUNT - new_usage
            if remaining_uses > 0:
                success_embed.add_field(
                    name="🔄 Còn lại:",
                    value=f"**{remaining_uses}** lần sử dụng",
                    inline=True
                )
                success_embed.add_field(
                    name="⏰ Cooldown:",
                    value="**5 phút** trước lần tiếp theo",
                    inline=False
                )
            else:
                success_embed.add_field(
                    name="🚫 Trạng thái:",
                    value="**Đã hết lượt sử dụng**",
                    inline=True
                )
            
            success_embed.set_footer(
                text="Cảm ơn bạn đã sử dụng dịch vụ!",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=success_embed, mention_author=True)
        
