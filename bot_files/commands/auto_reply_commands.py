import discord
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AutoReplyCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        
        # File để lưu auto-reply rules
        self.auto_reply_file = os.path.join('data', 'auto_reply_rules.json')
        self.auto_reply_rules = self.load_auto_reply_rules()
    
    def load_auto_reply_rules(self):
        """Load auto-reply rules from file"""
        if os.path.exists(self.auto_reply_file):
            try:
                with open(self.auto_reply_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi khi load auto-reply rules: {e}")
                return {}
        return {}
    
    def save_auto_reply_rules(self):
        """Save auto-reply rules to file"""
        try:
            os.makedirs(os.path.dirname(self.auto_reply_file), exist_ok=True)
            with open(self.auto_reply_file, 'w', encoding='utf-8') as f:
                json.dump(self.auto_reply_rules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save auto-reply rules: {e}")
    
    async def handle_auto_reply(self, message):
        """Xử lý auto-reply cho tin nhắn"""
        try:
            # Không reply cho bot hoặc tin nhắn bắt đầu bằng prefix
            if message.author.bot or message.content.startswith(';'):
                return False
            
            user_id_str = str(message.author.id)
            
            # Kiểm tra có rule cho user này không
            if user_id_str in self.auto_reply_rules:
                rule = self.auto_reply_rules[user_id_str]
                
                # Kiểm tra rule có active không
                if rule.get('active', True):
                    reply_content = rule.get('content', '')
                    
                    if reply_content:
                        # Tạo embed reply
                        embed = discord.Embed(
                            title="🤖 Auto Reply",
                            description=reply_content,
                            color=discord.Color.blue(),
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(
                            name="📝 Thiết lập bởi:",
                            value=rule.get('set_by_name', 'Admin'),
                            inline=True
                        )
                        
                        embed.add_field(
                            name="⏰ Thiết lập lúc:",
                            value=f"<t:{int(datetime.fromisoformat(rule.get('created_at', datetime.now().isoformat())).timestamp())}:R>",
                            inline=True
                        )
                        
                        embed.set_footer(
                            text=f"Auto-reply cho {message.author.display_name}",
                            icon_url=message.author.display_avatar.url
                        )
                        
                        # Reply với mention
                        await message.reply(embed=embed, mention_author=True)
                        
                        # Log auto-reply
                        logger.info(f"Auto-replied to {message.author.name} ({message.author.id}) with: {reply_content[:50]}...")
                        
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Lỗi trong handle_auto_reply: {e}")
            return False
    
    def register_commands(self):
        """Register auto-reply commands"""
        
        @self.bot.command(name='reply')
        async def auto_reply_command(ctx, user_id=None, *, content=None):
            """Thiết lập auto-reply cho user - Admin only"""
            # Kiểm tra quyền admin
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply(
                    "❌ **Chỉ Admin mới có thể sử dụng lệnh này!**",
                    mention_author=True
                )
                return
            
            # Kiểm tra parameters
            if not user_id:
                await self.show_auto_reply_help(ctx)
                return
            
            # Xử lý các sub-commands
            if user_id.lower() == "list":
                await self.list_auto_reply_rules(ctx)
                return
            elif user_id.lower() == "clear":
                if content:
                    await self.remove_auto_reply_rule(ctx, content)
                else:
                    await ctx.reply(
                        "❌ **Cách sử dụng:** `;reply clear <user_id>`",
                        mention_author=True
                    )
                return
            
            # Validate user_id
            try:
                user_id_int = int(user_id)
            except ValueError:
                await ctx.reply(
                    "❌ **User ID không hợp lệ!** Phải là số.",
                    mention_author=True
                )
                return
            
            # Kiểm tra content
            if not content:
                await ctx.reply(
                    "❌ **Thiếu nội dung reply!**\n\n"
                    "📝 **Cách sử dụng:** `;reply <user_id> <nội dung>`\n"
                    "💡 **Ví dụ:** `;reply 123456789 Xin chào! Bot sẽ tự động reply tin nhắn này.`",
                    mention_author=True
                )
                return
            
            # Thêm/cập nhật rule
            await self.add_auto_reply_rule(ctx, user_id_int, content)
        
        @self.bot.command(name='autoreply', aliases=['areply'])
        async def auto_reply_status_command(ctx, action=None, user_id=None):
            """Quản lý trạng thái auto-reply - Admin only"""
            # Kiểm tra quyền admin
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply(
                    "❌ **Chỉ Admin mới có thể sử dụng lệnh này!**",
                    mention_author=True
                )
                return
            
            if not action:
                await self.show_auto_reply_status(ctx)
                return
            
            if action.lower() == "on" and user_id:
                await self.toggle_auto_reply(ctx, user_id, True)
            elif action.lower() == "off" and user_id:
                await self.toggle_auto_reply(ctx, user_id, False)
            elif action.lower() == "list":
                await self.list_auto_reply_rules(ctx)
            else:
                await ctx.reply(
                    "❌ **Cách sử dụng:**\n"
                    "`;autoreply on <user_id>` - Bật auto-reply\n"
                    "`;autoreply off <user_id>` - Tắt auto-reply\n"
                    "`;autoreply list` - Xem danh sách rules",
                    mention_author=True
                )
    
    async def show_auto_reply_help(self, ctx):
        """Hiển thị hướng dẫn sử dụng auto-reply"""
        embed = discord.Embed(
            title="🤖 AUTO-REPLY SYSTEM",
            description="Hệ thống tự động reply tin nhắn cho user cụ thể",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📝 Thiết lập Auto-Reply",
            value=(
                "`;reply <user_id> <nội dung>`\n"
                "💡 **Ví dụ:** `;reply 123456789 Xin chào!`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 Quản lý Rules",
            value=(
                "`;reply list` - Xem tất cả rules\n"
                "`;reply clear <user_id>` - Xóa rule\n"
                "`;autoreply on/off <user_id>` - Bật/tắt rule"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Cách hoạt động",
            value=(
                "• Khi user được thiết lập gửi tin nhắn\n"
                "• Bot sẽ tự động reply với nội dung đã thiết lập\n"
                "• Không reply cho bot hoặc lệnh (bắt đầu bằng `;`)\n"
                "• Chỉ Admin mới có thể thiết lập"
            ),
            inline=False
        )
        
        embed.set_footer(
            text="Auto-Reply System • Admin Only",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def add_auto_reply_rule(self, ctx, user_id, content):
        """Thêm/cập nhật auto-reply rule"""
        try:
            # Lấy thông tin user
            try:
                user = await self.bot.fetch_user(user_id)
                user_name = user.display_name
            except:
                user_name = f"User {user_id}"
            
            user_id_str = str(user_id)
            
            # Tạo rule mới
            rule = {
                'content': content,
                'active': True,
                'created_at': datetime.now().isoformat(),
                'set_by_id': ctx.author.id,
                'set_by_name': ctx.author.display_name,
                'target_user_name': user_name
            }
            
            # Lưu rule
            self.auto_reply_rules[user_id_str] = rule
            self.save_auto_reply_rules()
            
            # Tạo embed thông báo
            embed = discord.Embed(
                title="✅ Auto-Reply Đã Thiết Lập",
                description=f"Đã thiết lập auto-reply cho **{user_name}**",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 Target User:",
                value=f"{user_name} (`{user_id}`)",
                inline=True
            )
            
            embed.add_field(
                name="📝 Nội dung reply:",
                value=f"```{content[:200]}{'...' if len(content) > 200 else ''}```",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Trạng thái:",
                value="🟢 Active",
                inline=True
            )
            
            embed.add_field(
                name="👑 Thiết lập bởi:",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.set_footer(
                text="Auto-Reply Rule Created",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            
            logger.info(f"Auto-reply rule created for {user_id} by {ctx.author.name}")
            
        except Exception as e:
            logger.error(f"Lỗi khi thêm auto-reply rule: {e}")
            await ctx.reply(
                f"❌ **Có lỗi xảy ra:** {str(e)}",
                mention_author=True
            )
    
    async def list_auto_reply_rules(self, ctx):
        """Hiển thị danh sách auto-reply rules"""
        if not self.auto_reply_rules:
            embed = discord.Embed(
                title="📋 Auto-Reply Rules",
                description="Hiện tại không có rule nào được thiết lập!",
                color=discord.Color.blue()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        embed = discord.Embed(
            title="📋 DANH SÁCH AUTO-REPLY RULES",
            description=f"Có **{len(self.auto_reply_rules)}** rules được thiết lập",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for i, (user_id, rule) in enumerate(self.auto_reply_rules.items(), 1):
            if i > 10:  # Chỉ hiển thị 10 rules đầu tiên
                embed.add_field(
                    name="⚠️ Thông báo",
                    value=f"Còn {len(self.auto_reply_rules) - 10} rules khác...",
                    inline=False
                )
                break
            
            status = "🟢 Active" if rule.get('active', True) else "🔴 Inactive"
            content_preview = rule.get('content', '')[:50]
            if len(rule.get('content', '')) > 50:
                content_preview += "..."
            
            embed.add_field(
                name=f"👤 {rule.get('target_user_name', f'User {user_id}')}",
                value=(
                    f"**ID:** `{user_id}`\n"
                    f"**Content:** {content_preview}\n"
                    f"**Status:** {status}\n"
                    f"**Set by:** {rule.get('set_by_name', 'Unknown')}"
                ),
                inline=True
            )
        
        embed.add_field(
            name="💡 Quản lý:",
            value=(
                "`;reply clear <user_id>` - Xóa rule\n"
                "`;autoreply on/off <user_id>` - Bật/tắt rule"
            ),
            inline=False
        )
        
        embed.set_footer(text="Auto-Reply Rules Management")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def remove_auto_reply_rule(self, ctx, user_id):
        """Xóa auto-reply rule"""
        try:
            user_id_int = int(user_id)
            user_id_str = str(user_id_int)
            
            if user_id_str not in self.auto_reply_rules:
                await ctx.reply(
                    f"❌ **Không tìm thấy auto-reply rule cho user ID `{user_id}`**",
                    mention_author=True
                )
                return
            
            # Lấy thông tin rule trước khi xóa
            rule = self.auto_reply_rules[user_id_str]
            user_name = rule.get('target_user_name', f'User {user_id}')
            
            # Xóa rule
            del self.auto_reply_rules[user_id_str]
            self.save_auto_reply_rules()
            
            embed = discord.Embed(
                title="🗑️ Auto-Reply Rule Đã Xóa",
                description=f"Đã xóa auto-reply rule cho **{user_name}**",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User:",
                value=f"{user_name} (`{user_id}`)",
                inline=True
            )
            
            embed.add_field(
                name="🗑️ Xóa bởi:",
                value=ctx.author.mention,
                inline=True
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            
            logger.info(f"Auto-reply rule removed for {user_id} by {ctx.author.name}")
            
        except ValueError:
            await ctx.reply(
                "❌ **User ID không hợp lệ!** Phải là số.",
                mention_author=True
            )
        except Exception as e:
            logger.error(f"Lỗi khi xóa auto-reply rule: {e}")
            await ctx.reply(
                f"❌ **Có lỗi xảy ra:** {str(e)}",
                mention_author=True
            )
    
    async def toggle_auto_reply(self, ctx, user_id, active):
        """Bật/tắt auto-reply rule"""
        try:
            user_id_int = int(user_id)
            user_id_str = str(user_id_int)
            
            if user_id_str not in self.auto_reply_rules:
                await ctx.reply(
                    f"❌ **Không tìm thấy auto-reply rule cho user ID `{user_id}`**",
                    mention_author=True
                )
                return
            
            # Cập nhật trạng thái
            self.auto_reply_rules[user_id_str]['active'] = active
            self.save_auto_reply_rules()
            
            rule = self.auto_reply_rules[user_id_str]
            user_name = rule.get('target_user_name', f'User {user_id}')
            status_text = "🟢 Đã bật" if active else "🔴 Đã tắt"
            
            embed = discord.Embed(
                title=f"⚙️ Auto-Reply {status_text}",
                description=f"{status_text} auto-reply cho **{user_name}**",
                color=discord.Color.green() if active else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 User:",
                value=f"{user_name} (`{user_id}`)",
                inline=True
            )
            
            embed.add_field(
                name="⚙️ Trạng thái:",
                value=status_text,
                inline=True
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            
            logger.info(f"Auto-reply rule {'enabled' if active else 'disabled'} for {user_id} by {ctx.author.name}")
            
        except ValueError:
            await ctx.reply(
                "❌ **User ID không hợp lệ!** Phải là số.",
                mention_author=True
            )
        except Exception as e:
            logger.error(f"Lỗi khi toggle auto-reply rule: {e}")
            await ctx.reply(
                f"❌ **Có lỗi xảy ra:** {str(e)}",
                mention_author=True
            )
    
    async def show_auto_reply_status(self, ctx):
        """Hiển thị tổng quan auto-reply system"""
        total_rules = len(self.auto_reply_rules)
        active_rules = sum(1 for rule in self.auto_reply_rules.values() if rule.get('active', True))
        inactive_rules = total_rules - active_rules
        
        embed = discord.Embed(
            title="📊 AUTO-REPLY SYSTEM STATUS",
            description="Tổng quan hệ thống auto-reply",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📈 Thống kê:",
            value=(
                f"📋 **Tổng rules:** {total_rules}\n"
                f"🟢 **Active:** {active_rules}\n"
                f"🔴 **Inactive:** {inactive_rules}"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔧 Quản lý:",
            value=(
                "`;reply list` - Xem tất cả rules\n"
                "`;autoreply on/off <id>` - Bật/tắt\n"
                "`;reply clear <id>` - Xóa rule"
            ),
            inline=True
        )
        
        if total_rules > 0:
            # Hiển thị 3 rules gần nhất
            recent_rules = list(self.auto_reply_rules.items())[-3:]
            recent_text = ""
            for user_id, rule in recent_rules:
                status = "🟢" if rule.get('active', True) else "🔴"
                user_name = rule.get('target_user_name', f'User {user_id}')
                recent_text += f"{status} {user_name}\n"
            
            embed.add_field(
                name="📝 Rules gần nhất:",
                value=recent_text,
                inline=False
            )
        
        embed.set_footer(
            text="Auto-Reply System • Admin Only",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
