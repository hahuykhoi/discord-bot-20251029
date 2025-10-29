import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

class AdminNicknameProtection:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.protection_file = 'data/admin_nickname_protection.json'
        self.protected_nicknames = {}
        self.user_history = {}  # Lưu lịch sử nickname của user
        self.load_protection_data()
        self.setup_commands()
    
    def load_protection_data(self):
        """Load protection data from file"""
        try:
            if os.path.exists(self.protection_file):
                with open(self.protection_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.protected_nicknames = data.get('protected_nicknames', {})
                    self.user_history = data.get('user_history', {})
                logger.info(f"Loaded {len(self.protected_nicknames)} protected nicknames")
            else:
                logger.info("No admin nickname protection file found, creating new")
                self.protected_nicknames = {}
                self.user_history = {}
                self.save_protection_data()
        except Exception as e:
            logger.error(f"Error loading admin nickname protection data: {e}")
            self.protected_nicknames = {}
            self.user_history = {}
    
    def save_protection_data(self):
        """Save protection data to file"""
        try:
            os.makedirs('data', exist_ok=True)
            data = {
                'protected_nicknames': self.protected_nicknames,
                'user_history': self.user_history,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.protection_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info("Admin nickname protection data saved successfully")
        except Exception as e:
            logger.error(f"Error saving admin nickname protection data: {e}")
    
    def setup_commands(self):
        """Setup admin nickname protection commands"""
        
        @self.bot.command(name='protectnick')
        async def protectnick_command(ctx, action=None, *, nickname=None):
            """
            Bảo vệ nickname admin - tự động đổi về tên cũ khi user copy
            
            Usage:
            ;protectnick add <nickname> - Thêm nickname cần bảo vệ
            ;protectnick remove <nickname> - Gỡ bỏ bảo vệ
            ;protectnick list - Xem danh sách nickname được bảo vệ
            ;protectnick - Hiển thị hướng dẫn
            """
            # Kiểm tra quyền admin
            if not self.bot_instance.has_warn_permission(ctx.author.id, ctx.author.guild_permissions):
                embed = discord.Embed(
                    title="❌ Không có quyền",
                    description="Chỉ Admin mới có thể sử dụng lệnh protectnick!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Hiển thị help nếu không có tham số
            if not action:
                await self.show_help(ctx)
                return
            
            # Xử lý các action
            if action.lower() == 'add':
                await self.add_protection(ctx, nickname)
            elif action.lower() == 'remove':
                await self.remove_protection(ctx, nickname)
            elif action.lower() == 'list':
                await self.show_protected_list(ctx)
            else:
                await self.show_help(ctx)
    
    async def add_protection(self, ctx, nickname):
        """Add nickname to protection list"""
        if not nickname:
            embed = discord.Embed(
                title="❌ Thiếu nickname",
                description="Vui lòng nhập nickname cần bảo vệ!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;protectnick add <nickname>`",
                inline=False
            )
            embed.add_field(
                name="📝 Ví dụ",
                value="`;protectnick add Claude`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Kiểm tra độ dài nickname
        if len(nickname) > 32:
            embed = discord.Embed(
                title="❌ Nickname quá dài",
                description="Nickname không được vượt quá 32 ký tự!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Chuẩn hóa nickname (case-insensitive)
        nickname_lower = nickname.lower()
        
        # Kiểm tra đã tồn tại chưa
        if nickname_lower in self.protected_nicknames:
            embed = discord.Embed(
                title="⚠️ Nickname đã được bảo vệ",
                description=f"Nickname **{nickname}** đã có trong danh sách bảo vệ!",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Thêm vào danh sách bảo vệ
        self.protected_nicknames[nickname_lower] = {
            'original_nickname': nickname,
            'protected_by': ctx.author.id,
            'protected_at': datetime.now().isoformat(),
            'guild_id': ctx.guild.id,
            'violations': 0
        }
        
        self.save_protection_data()
        
        # Thông báo thành công
        embed = discord.Embed(
            title="✅ Đã thêm bảo vệ nickname",
            description=f"Nickname **{nickname}** giờ được bảo vệ khỏi việc copy!",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🛡️ Nickname được bảo vệ",
            value=f"**{nickname}**",
            inline=True
        )
        
        embed.add_field(
            name="👮 Được bảo vệ bởi",
            value=ctx.author.mention,
            inline=True
        )
        
        embed.add_field(
            name="⚡ Tự động phát hiện",
            value="Khi user đổi tên giống nickname này, sẽ tự động đổi về tên cũ",
            inline=False
        )
        
        embed.set_footer(text="Sử dụng ;protectnick remove để gỡ bỏ bảo vệ")
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} added nickname protection for: {nickname}")
    
    async def remove_protection(self, ctx, nickname):
        """Remove nickname from protection list"""
        if not nickname:
            embed = discord.Embed(
                title="❌ Thiếu nickname",
                description="Vui lòng nhập nickname cần gỡ bỏ bảo vệ!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;protectnick remove <nickname>`",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        nickname_lower = nickname.lower()
        
        if nickname_lower not in self.protected_nicknames:
            embed = discord.Embed(
                title="⚠️ Nickname không được bảo vệ",
                description=f"Nickname **{nickname}** không có trong danh sách bảo vệ!",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Lấy thông tin trước khi xóa
        protection_data = self.protected_nicknames[nickname_lower]
        original_nickname = protection_data.get('original_nickname', nickname)
        violations = protection_data.get('violations', 0)
        
        # Xóa khỏi danh sách
        del self.protected_nicknames[nickname_lower]
        self.save_protection_data()
        
        # Thông báo thành công
        embed = discord.Embed(
            title="✅ Đã gỡ bỏ bảo vệ nickname",
            description=f"Nickname **{original_nickname}** không còn được bảo vệ",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🛡️ Nickname",
            value=f"**{original_nickname}**",
            inline=True
        )
        
        embed.add_field(
            name="📊 Vi phạm đã chặn",
            value=f"{violations} lần",
            inline=True
        )
        
        embed.add_field(
            name="🔓 Trạng thái",
            value="User có thể sử dụng nickname này",
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author} removed nickname protection for: {original_nickname}")
    
    async def show_protected_list(self, ctx):
        """Show list of protected nicknames"""
        if not self.protected_nicknames:
            embed = discord.Embed(
                title="📝 Danh sách bảo vệ nickname trống",
                description="Hiện không có nickname nào được bảo vệ",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="💡 Cách sử dụng",
                value="`;protectnick add <nickname>` để thêm nickname vào bảo vệ",
                inline=False
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        embed = discord.Embed(
            title="🛡️ Danh sách bảo vệ nickname",
            description=f"Tổng cộng: {len(self.protected_nicknames)} nickname",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Hiển thị tối đa 10 nickname
        count = 0
        for nickname_lower, data in list(self.protected_nicknames.items())[:10]:
            count += 1
            original_nickname = data.get('original_nickname', nickname_lower)
            protected_by = data.get('protected_by', 'Unknown')
            violations = data.get('violations', 0)
            protected_at = data.get('protected_at', 'Unknown')
            
            # Parse thời gian
            try:
                dt = datetime.fromisoformat(protected_at)
                time_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                time_str = "Unknown"
            
            embed.add_field(
                name=f"#{count} - {original_nickname}",
                value=(
                    f"**Bởi:** <@{protected_by}>\n"
                    f"**Vi phạm chặn:** {violations} lần\n"
                    f"**Thời gian:** {time_str}"
                ),
                inline=False
            )
        
        if len(self.protected_nicknames) > 10:
            embed.add_field(
                name="📊 Thống kê",
                value=f"Hiển thị 10/{len(self.protected_nicknames)} nickname đầu tiên",
                inline=False
            )
        
        embed.set_footer(text="Sử dụng ;protectnick remove để gỡ bỏ bảo vệ")
        await ctx.reply(embed=embed, mention_author=True)
    
    async def show_help(self, ctx):
        """Show help menu"""
        embed = discord.Embed(
            title="🛡️ Admin Nickname Protection",
            description="Bảo vệ nickname admin - tự động đổi về tên cũ khi user sử dụng tên chứa từ được bảo vệ",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Lệnh quản lý",
            value=(
                "`;protectnick add <nickname>` - Thêm nickname cần bảo vệ\n"
                "`;protectnick remove <nickname>` - Gỡ bỏ bảo vệ\n"
                "`;protectnick list` - Xem danh sách nickname được bảo vệ"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Tính năng tự động",
            value=(
                "• Phát hiện khi user đổi tên **chứa** từ được bảo vệ\n"
                "• **AI Detection**: Phát hiện biến thể ký tự đặc biệt của 'Claude'\n"
                "• Tự động đổi về nickname trước đó\n"
                "• Thông báo cho user về vi phạm\n"
                "• Tracking số lần vi phạm"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔒 Bảo mật",
            value=(
                "• Chỉ Admin mới có quyền quản lý\n"
                "• So sánh case-insensitive và substring\n"
                "• **AI-Powered**: Phát hiện ký tự Unicode giả mạo\n"
                "• Chuẩn hóa text để chống ký tự đặc biệt\n"
                "• Lưu lịch sử nickname của user"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Ví dụ sử dụng",
            value=(
                "`;protectnick add Claude` - Bảo vệ từ \"Claude\"\n"
                "User đổi tên: \"Claude Sonnet 4.5 Pro\" → AI phát hiện và chặn\n"
                "User đổi tên: \"𝐂𝐥𝐚𝐮𝐝𝐞\" → AI phát hiện và chặn\n"
                "User đổi tên: \"C|@ud3\" → AI phát hiện và chặn\n"
                "`;protectnick list` - Xem danh sách"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Lưu ý",
            value=(
                "• Bot cần quyền 'Manage Nicknames'\n"
                "• Role bot phải cao hơn role của user\n"
                "• Hoạt động real-time 24/7"
            ),
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    def update_user_history(self, user_id, old_nickname, new_nickname):
        """Update user nickname history"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_history:
            self.user_history[user_id_str] = {
                'history': [],
                'last_updated': datetime.now().isoformat()
            }
        
        # Thêm vào lịch sử (giữ tối đa 10 entries)
        history_entry = {
            'old_nickname': old_nickname,
            'new_nickname': new_nickname,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_history[user_id_str]['history'].append(history_entry)
        self.user_history[user_id_str]['last_updated'] = datetime.now().isoformat()
        
        # Giữ tối đa 10 entries
        if len(self.user_history[user_id_str]['history']) > 10:
            self.user_history[user_id_str]['history'] = self.user_history[user_id_str]['history'][-10:]
        
        self.save_protection_data()
    
    def get_previous_nickname(self, user_id):
        """Get previous nickname of user"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_history:
            return None
        
        history = self.user_history[user_id_str]['history']
        if not history:
            return None
        
        # Lấy nickname trước đó (old_nickname của entry cuối cùng)
        return history[-1]['old_nickname']
    
    def normalize_text(self, text):
        """Chuẩn hóa text để phát hiện ký tự đặc biệt giả mạo"""
        if not text:
            return ""
        
        # Loại bỏ dấu và chuyển về ASCII
        normalized = unicodedata.normalize('NFD', text)
        ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # Thay thế các ký tự đặc biệt thường dùng để giả mạo
        replacements = {
            # Ký tự giống C
            'Ç': 'C', 'ç': 'c', 'Ć': 'C', 'ć': 'c', 'Č': 'C', 'č': 'c',
            'Ĉ': 'C', 'ĉ': 'c', 'Ċ': 'C', 'ċ': 'c', '¢': 'c', 'ℂ': 'C',
            'ⅽ': 'c', 'Ⅽ': 'C', '𝐂': 'C', '𝐜': 'c', '𝑪': 'C', '𝒄': 'c',
            '𝒞': 'C', '𝓬': 'c', '𝕮': 'C', '𝖈': 'c', '𝖢': 'C', '𝗰': 'c',
            '𝘊': 'C', '𝘤': 'c', '𝙲': 'C', '𝚌': 'c', 'Ⲥ': 'C', 'ⲥ': 'c',
            
            # Ký tự giống L
            'Ł': 'L', 'ł': 'l', 'Ĺ': 'L', 'ĺ': 'l', 'Ľ': 'L', 'ľ': 'l',
            'Ļ': 'L', 'ļ': 'l', 'Ŀ': 'L', 'ŀ': 'l', 'ℒ': 'L', 'ℓ': 'l',
            'Ⅼ': 'L', 'ⅼ': 'l', '𝐋': 'L', '𝐥': 'l', '𝑳': 'L', '𝒍': 'l',
            '𝓛': 'L', '𝓵': 'l', '𝕃': 'L', '𝕝': 'l', '𝖫': 'L', '𝗅': 'l',
            '𝗟': 'L', '𝗹': 'l', '𝘓': 'L', '𝘭': 'l', '𝙇': 'L', '𝙡': 'l',
            
            # Ký tự giống A
            'À': 'A', 'à': 'a', 'Á': 'A', 'á': 'a', 'Â': 'A', 'â': 'a',
            'Ã': 'A', 'ã': 'a', 'Ä': 'A', 'ä': 'a', 'Å': 'A', 'å': 'a',
            'Ā': 'A', 'ā': 'a', 'Ă': 'A', 'ă': 'a', 'Ą': 'A', 'ą': 'a',
            'Ǎ': 'A', 'ǎ': 'a', 'Ǻ': 'A', 'ǻ': 'a', 'Α': 'A', 'α': 'a',
            '𝐀': 'A', '𝐚': 'a', '𝑨': 'A', '𝒂': 'a', '𝒜': 'A', '𝓪': 'a',
            
            # Ký tự giống U
            'Ù': 'U', 'ù': 'u', 'Ú': 'U', 'ú': 'u', 'Û': 'U', 'û': 'u',
            'Ü': 'U', 'ü': 'u', 'Ũ': 'U', 'ũ': 'u', 'Ū': 'U', 'ū': 'u',
            'Ŭ': 'U', 'ŭ': 'u', 'Ů': 'U', 'ů': 'u', 'Ű': 'U', 'ű': 'u',
            'Ų': 'U', 'ų': 'u', 'Ǔ': 'U', 'ǔ': 'u', 'Ǖ': 'U', 'ǖ': 'u',
            
            # Ký tự giống D
            'Ď': 'D', 'ď': 'd', 'Đ': 'D', 'đ': 'd', 'Ḋ': 'D', 'ḋ': 'd',
            'Ḍ': 'D', 'ḍ': 'd', 'Ḏ': 'D', 'ḏ': 'd', 'Ḑ': 'D', 'ḑ': 'd',
            'Ḓ': 'D', 'ḓ': 'd', '𝐃': 'D', '𝐝': 'd', '𝑫': 'D', '𝒅': 'd',
            
            # Ký tự giống E
            'È': 'E', 'è': 'e', 'É': 'E', 'é': 'e', 'Ê': 'E', 'ê': 'e',
            'Ë': 'E', 'ë': 'e', 'Ē': 'E', 'ē': 'e', 'Ĕ': 'E', 'ĕ': 'e',
            'Ė': 'E', 'ė': 'e', 'Ę': 'E', 'ę': 'e', 'Ě': 'E', 'ě': 'e',
            '𝐄': 'E', '𝐞': 'e', '𝑬': 'E', '𝒆': 'e', 'ℰ': 'E', '𝓮': 'e'
        }
        
        # Áp dụng thay thế
        for special_char, normal_char in replacements.items():
            ascii_text = ascii_text.replace(special_char, normal_char)
        
        # Loại bỏ các ký tự không phải chữ cái và số
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', ascii_text)
        
        return clean_text.lower().strip()
    
    async def ask_ai_about_name(self, nickname, protected_name="Claude"):
        """Hỏi AI xem nickname có phải là biến thể của tên được bảo vệ không"""
        try:
            # Kiểm tra AI commands có sẵn không
            if not hasattr(self.bot_instance, 'ai_commands'):
                logger.warning("AI Commands không có sẵn, sử dụng phương pháp cơ bản")
                return False
            
            ai_commands = self.bot_instance.ai_commands
            
            # Tạo prompt để hỏi AI
            prompt = f"""
Phân tích nickname sau và cho biết có phải là biến thể của tên "{protected_name}" không:
Nickname: "{nickname}"

Hãy kiểm tra:
1. Có phải là "{protected_name}" được viết bằng ký tự đặc biệt, Unicode, hoặc ký tự giống nhau không?
2. Có phải là "{protected_name}" với thêm số, ký tự, hoặc từ khác không?
3. Có phải là cách viết khác của "{protected_name}" (như {protected_name[:-1]}, {protected_name}d, etc.) không?
4. Có phải là "{protected_name}" được ngụy trang bằng ký tự đặc biệt không?

Ví dụ biến thể của "{protected_name}":
- {protected_name} Sonnet 4.5 Pro
- 𝐂𝐥𝐚𝐮𝐝𝐞 (Unicode bold)
- Ċłαυđē (mixed diacritics)
- C|@ud3 (leet speak)

Chỉ trả lời "YES" nếu đây là biến thể của {protected_name}, "NO" nếu không phải.
Không giải thích thêm, chỉ trả lời YES hoặc NO."""
            
            # Gọi AI để phân tích
            if ai_commands.current_provider == "gemini" and ai_commands.gemini_model:
                try:
                    response = ai_commands.gemini_model.generate_content(prompt)
                    ai_response = response.text.strip().upper()
                    logger.info(f"AI Gemini response for '{nickname}' vs '{protected_name}': {ai_response}")
                    return "YES" in ai_response
                except Exception as e:
                    logger.error(f"Error calling Gemini AI: {e}")
            
            elif ai_commands.current_provider == "grok" and ai_commands.grok_client:
                try:
                    response = ai_commands.grok_client.chat.completions.create(
                        model="grok-beta",
                        messages=[
                            {"role": "system", "content": "You are a text analysis assistant. Answer only YES or NO."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=10,
                        temperature=0.1
                    )
                    ai_response = response.choices[0].message.content.strip().upper()
                    logger.info(f"AI Grok response for '{nickname}' vs '{protected_name}': {ai_response}")
                    return "YES" in ai_response
                except Exception as e:
                    logger.error(f"Error calling Grok AI: {e}")
            
            # Fallback: sử dụng phương pháp cơ bản
            logger.info("AI không khả dụng, sử dụng phương pháp cơ bản")
            return False
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return False
    
    def basic_name_detection(self, nickname, protected_name):
        """Phương pháp cơ bản để phát hiện biến thể của tên được bảo vệ"""
        normalized = self.normalize_text(nickname)
        protected_normalized = self.normalize_text(protected_name)
        
        # Kiểm tra chứa tên được bảo vệ
        if protected_normalized in normalized:
            return True
        
        # Các pattern phổ biến dựa trên tên được bảo vệ
        if protected_normalized == "claude":
            claude_patterns = [
                r'\bclaud[e]?\b',  # claude, claud
                r'\bc[l1][a@4][u][d][e3]?\b',  # c1aud3, cl@ude, etc.
                r'\bc.*l.*a.*u.*d.*e\b',  # c...l...a...u...d...e
            ]
            
            for pattern in claude_patterns:
                if re.search(pattern, normalized, re.IGNORECASE):
                    return True
        
        return False
    
    async def handle_member_update(self, before, after):
        """Handle member update events to protect admin nicknames"""
        # Chỉ xử lý thay đổi nickname
        if before.display_name == after.display_name:
            return
        
        # Bỏ qua admin
        if self.bot_instance.has_warn_permission(after.id, after.guild_permissions):
            return
        
        # Cập nhật lịch sử nickname
        self.update_user_history(after.id, before.display_name, after.display_name)
        
        # Kiểm tra nickname mới có chứa từ được bảo vệ không
        new_nickname_lower = after.display_name.lower()
        
        # Tìm nickname được bảo vệ trong nickname mới (phương pháp cũ)
        protected_found = None
        for protected_nick_lower, data in self.protected_nicknames.items():
            if protected_nick_lower in new_nickname_lower:
                protected_found = (protected_nick_lower, data)
                break
        
        # Nếu không tìm thấy bằng phương pháp cũ, kiểm tra AI cho tất cả tên được bảo vệ
        if not protected_found:
            for protected_nick_lower, data in self.protected_nicknames.items():
                original_protected_name = data.get('original_nickname', protected_nick_lower)
                
                # Sử dụng AI để phát hiện biến thể
                logger.info(f"Checking nickname '{after.display_name}' for '{original_protected_name}' variants using AI...")
                
                # Thử AI trước
                is_variant = await self.ask_ai_about_name(after.display_name, original_protected_name)
                
                # Nếu AI không khả dụng, dùng phương pháp cơ bản
                if not is_variant:
                    is_variant = self.basic_name_detection(after.display_name, original_protected_name)
                
                if is_variant:
                    protected_found = (protected_nick_lower, data)
                    logger.info(f"AI/Basic detection: '{after.display_name}' is a '{original_protected_name}' variant")
                    break
                else:
                    logger.info(f"AI/Basic detection: '{after.display_name}' is NOT a '{original_protected_name}' variant")
        
        if protected_found:
            # Tìm nickname trước đó
            previous_nickname = self.get_previous_nickname(after.id)
            
            # Nếu không có lịch sử, sử dụng username
            if not previous_nickname:
                previous_nickname = after.name
            
            try:
                # Đổi về nickname trước đó
                await after.edit(nick=previous_nickname, reason="Admin nickname protection - auto restore")
                
                # Cập nhật số vi phạm
                protected_nick_lower, protected_data = protected_found
                self.protected_nicknames[protected_nick_lower]['violations'] += 1
                self.save_protection_data()
                
                logger.info(f"Protected admin nickname: {after} tried to use '{after.display_name}' (contains '{protected_nick_lower}') -> restored to '{previous_nickname}'")
                
                # Gửi thông báo cho user
                try:
                    original_protected_nickname = protected_data.get('original_nickname', protected_nick_lower)
                    violations = protected_data.get('violations', 0)
                    
                    embed = discord.Embed(
                        title="🛡️ Nickname được bảo vệ",
                        description=f"Nickname **{original_protected_nickname}** được bảo vệ và không thể sử dụng",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="⚡ Đã khôi phục",
                        value=f"Nickname của bạn đã được đổi về: **{previous_nickname}**",
                        inline=False
                    )
                    
                    # Xác định loại phát hiện
                    detection_method = "AI Detection" if protected_found else "Direct Match"
                    
                    embed.add_field(
                        name="🚫 Nickname vi phạm",
                        value=f"**{after.display_name}** (phát hiện: **{original_protected_nickname}** - {detection_method})",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📊 Vi phạm",
                        value=f"Đây là lần thứ {violations} bạn vi phạm quy định nickname",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="💡 Lưu ý",
                        value="Vui lòng không sử dụng nickname chứa tên Admin",
                        inline=True
                    )
                    
                    embed.set_footer(text="Liên hệ Admin nếu có thắc mắc")
                    
                    await after.send(embed=embed)
                except:
                    # Không thể gửi DM, bỏ qua
                    pass
                    
            except discord.Forbidden:
                logger.warning(f"Cannot restore nickname for {after}: Missing permissions")
            except Exception as e:
                logger.error(f"Error protecting admin nickname for {after}: {e}")
    
    def register_commands(self):
        """Register all commands"""
        logger.info("Admin Nickname Protection commands đã được đăng ký")
