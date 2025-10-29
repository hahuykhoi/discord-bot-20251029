import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class ShopCommands:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.shop_data_file = 'data/shop_data.json'
        self.orders_data_file = 'data/shop_orders.json'
        self.pending_orders_file = 'data/pending_orders.json'
        self.shop_config_file = 'data/shop_config.json'
        self.shop_data = self.load_shop_data()
        self.shop_config = self.load_shop_config()
        self.pending_orders = self.load_pending_orders()
        self.daily_purchases_file = 'data/daily_purchases.json'
        self.daily_purchases = self.load_daily_purchases()
        
        # EXP Rare packages removed - only Gmail and TikTok now
        self.exp_packages = {}
        
        # Other products configuration
        self.other_products = {
            "gmail": {
                "name": "Gmail 1 tuần",
                "price": 1000000,  # 1 triệu xu
                "description": "Tài khoản Gmail mới sử dụng được 1 tuần",
                "type": "digital"
            },
            "tiktok": {
                "name": "TikTok Account",
                "price": 1000000,  # 1 triệu xu
                "description": "Tài khoản TikTok đã tạo sẵn",
                "type": "digital"
            }
        }
        
        # Product inventory (admin can manage)
        self.product_inventory_file = 'data/product_inventory.json'
        self.product_inventory = self.load_product_inventory()
    
    def load_shop_data(self):
        """Load shop data from file"""
        if os.path.exists(self.shop_data_file):
            try:
                with open(self.shop_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi khi load shop data: {e}")
                return {}
        return {}
    
    def save_shop_data(self):
        """Save shop data to file"""
        try:
            os.makedirs(os.path.dirname(self.shop_data_file), exist_ok=True)
            with open(self.shop_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.shop_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save shop data: {e}")
    
    def load_shop_config(self):
        """Load shop configuration from file"""
        if os.path.exists(self.shop_config_file):
            try:
                with open(self.shop_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi khi load shop config: {e}")
                return {}
        return {}
    
    def save_shop_config(self):
        """Save shop configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.shop_config_file), exist_ok=True)
            with open(self.shop_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.shop_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save shop config: {e}")
    
    def load_pending_orders(self):
        """Load pending orders from file"""
        if os.path.exists(self.pending_orders_file):
            try:
                with open(self.pending_orders_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi khi load pending orders: {e}")
                return {}
        return {}
    
    def save_pending_orders(self):
        """Save pending orders to file"""
        try:
            os.makedirs(os.path.dirname(self.pending_orders_file), exist_ok=True)
            with open(self.pending_orders_file, 'w', encoding='utf-8') as f:
                json.dump(self.pending_orders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save pending orders: {e}")
    
    def load_daily_purchases(self):
        """Load daily purchases from file"""
        if os.path.exists(self.daily_purchases_file):
            try:
                with open(self.daily_purchases_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi khi load daily purchases: {e}")
                return {}
        return {}
    
    def save_daily_purchases(self):
        """Save daily purchases to file"""
        try:
            os.makedirs(os.path.dirname(self.daily_purchases_file), exist_ok=True)
            with open(self.daily_purchases_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_purchases, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save daily purchases: {e}")
    
    # check_purchase_eligibility removed - no restrictions for Gmail/TikTok
    
    # record_daily_purchase removed - no daily restrictions for Gmail/TikTok
    
    def get_user_balance(self, user_id):
        """Get user balance from shared wallet"""
        try:
            if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
                return self.bot_instance.shared_wallet.get_balance(user_id)
            return 0
        except:
            return 0
    
    def deduct_user_balance(self, user_id, amount):
        """Deduct amount from user balance"""
        try:
            if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
                if self.bot_instance.shared_wallet.has_sufficient_balance(user_id, amount):
                    self.bot_instance.shared_wallet.subtract_balance(user_id, amount)
                    return True
            return False
        except Exception as e:
            logger.error(f"Lỗi khi trừ tiền user {user_id}: {e}")
            return False
    
    def add_user_exp(self, user_id, exp_amount):
        """Add EXP Rare to user"""
        user_str = str(user_id)
        if user_str not in self.shop_data:
            self.shop_data[user_str] = {"exp_rare": 0, "purchases": []}
        
        self.shop_data[user_str]["exp_rare"] += exp_amount
        self.save_shop_data()
    
    def get_user_exp(self, user_id):
        """Get user EXP Rare"""
        user_str = str(user_id)
        if user_str in self.shop_data:
            return self.shop_data[user_str].get("exp_rare", 0)
        return 0
    
    def load_product_inventory(self):
        """Load product inventory from JSON file"""
        if os.path.exists(self.product_inventory_file):
            try:
                with open(self.product_inventory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"gmail": [], "tiktok": []}
        return {"gmail": [], "tiktok": []}
    
    def save_product_inventory(self):
        """Save product inventory to JSON file"""
        os.makedirs(os.path.dirname(self.product_inventory_file), exist_ok=True)
        with open(self.product_inventory_file, 'w', encoding='utf-8') as f:
            json.dump(self.product_inventory, f, ensure_ascii=False, indent=2)
    
    async def create_order_channel(self, guild, user, package_id, package_info):
        """Create a private channel for the order"""
        try:
            # Kiểm tra chi tiết các quyền cần thiết
            bot_permissions = guild.me.guild_permissions
            logger.info(f"Checking permissions in guild {guild.name}:")
            logger.info(f"- manage_channels: {bot_permissions.manage_channels}")
            logger.info(f"- send_messages: {bot_permissions.send_messages}")
            logger.info(f"- embed_links: {bot_permissions.embed_links}")
            logger.info(f"- read_message_history: {bot_permissions.read_message_history}")
            
            if not bot_permissions.manage_channels:
                logger.error(f"Bot không có quyền manage_channels trong guild {guild.name}")
                return None
            
            # Tạo tên channel
            channel_name = f"order-{user.name}-{package_id}-{datetime.now().strftime('%m%d%H%M')}"
            
            # Tạo category nếu chưa có
            category = discord.utils.get(guild.categories, name="🛒 Shop Orders")
            if not category:
                try:
                    logger.info(f"Tạo category '🛒 Shop Orders' trong guild {guild.name}")
                    category = await guild.create_category("🛒 Shop Orders")
                    logger.info(f"✅ Đã tạo category thành công: {category.name} (ID: {category.id})")
                except discord.Forbidden as e:
                    logger.error(f"❌ Bot không có quyền tạo category trong guild {guild.name}: {e}")
                    category = None
                except Exception as e:
                    logger.error(f"❌ Lỗi không xác định khi tạo category: {e}")
                    category = None
            else:
                logger.info(f"✅ Category '🛒 Shop Orders' đã tồn tại: {category.name} (ID: {category.id})")
            
            # Tạo channel PRIVATE - chỉ role Administrator, Support và user mua hàng xem được
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=False,  # Everyone KHÔNG xem được
                    send_messages=False
                ),
                user: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    read_message_history=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
            }
            
            # Thêm quyền cho các role được phép (từ config)
            allowed_roles = self.shop_config.get("allowed_roles", [])
            roles_found = 0
            
            for role_id in allowed_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=True,
                        read_message_history=True,
                        manage_messages=True  # Role có thể xóa tin nhắn
                    )
                    logger.info(f"✅ Đã cấp quyền cho role: {role.name} (ID: {role.id})")
                    roles_found += 1
                else:
                    logger.warning(f"⚠️ Không tìm thấy role với ID {role_id} trong server")
            
            # Fallback: Nếu không có role nào được cấu hình hoặc tìm thấy, sử dụng hard-code roles
            if roles_found == 0:
                logger.info("🔄 Fallback: Sử dụng hard-code roles vì không có role nào được cấu hình")
                
                # Thêm quyền cho role Administrator (fallback)
                admin_role = discord.utils.get(guild.roles, name="Administrator")
                if admin_role:
                    overwrites[admin_role] = discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=True,
                        read_message_history=True,
                        manage_messages=True
                    )
                    logger.info(f"✅ Fallback: Đã cấp quyền cho role Administrator: {admin_role.name}")
                    roles_found += 1
                
                # Thêm quyền cho role Support (fallback)
                support_role = discord.utils.get(guild.roles, name="Support")
                if support_role:
                    overwrites[support_role] = discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=True,
                        read_message_history=True,
                        manage_messages=True
                    )
                    logger.info(f"✅ Fallback: Đã cấp quyền cho role Support: {support_role.name}")
                    roles_found += 1
                
                # Nếu vẫn không có role nào, sử dụng admin IDs
                if roles_found == 0:
                    logger.info("🔄 Final fallback: Sử dụng admin IDs vì không tìm thấy role nào")
                    for admin_id in self.shop_config.get("admin_ids", []):
                        admin_user = guild.get_member(admin_id)
                        if admin_user:
                            overwrites[admin_user] = discord.PermissionOverwrite(
                                read_messages=True, 
                                send_messages=True,
                                read_message_history=True,
                                manage_messages=True
                            )
                    
                    for supreme_admin_id in self.shop_config.get("supreme_admin_ids", []):
                        supreme_admin_user = guild.get_member(supreme_admin_id)
                        if supreme_admin_user:
                            overwrites[supreme_admin_user] = discord.PermissionOverwrite(
                                read_messages=True, 
                                send_messages=True,
                                read_message_history=True,
                                manage_messages=True
                            )
            
            try:
                logger.info(f"Tạo text channel '{channel_name}' trong guild {guild.name}")
                if category:
                    logger.info(f"Sử dụng category: {category.name} (ID: {category.id})")
                    # Kiểm tra permissions trong category
                    category_permissions = category.permissions_for(guild.me)
                    logger.info(f"Category permissions - manage_channels: {category_permissions.manage_channels}")
                    logger.info(f"Category permissions - send_messages: {category_permissions.send_messages}")
                else:
                    logger.info("Tạo channel không có category")
                
                channel = await guild.create_text_channel(
                    channel_name,
                    category=category,
                    overwrites=overwrites
                )
                logger.info(f"✅ Đã tạo text channel thành công: {channel.name} (ID: {channel.id})")
                return channel
            except discord.Forbidden as e:
                logger.error(f"❌ Bot không có quyền tạo text channel trong guild {guild.name}: {e}")
                logger.error(f"Error details: {e.code} - {e.text}")
                
                # Thử tạo channel không có category
                if category:
                    logger.info("Thử tạo channel không có category...")
                    try:
                        channel = await guild.create_text_channel(
                            channel_name,
                            overwrites=overwrites
                        )
                        logger.info(f"✅ Đã tạo text channel thành công (không có category): {channel.name} (ID: {channel.id})")
                        return channel
                    except discord.Forbidden as e2:
                        logger.error(f"❌ Vẫn không thể tạo text channel (không có category): {e2}")
                        return None
                    except Exception as e2:
                        logger.error(f"❌ Lỗi khi tạo channel không có category: {e2}")
                        return None
                else:
                    return None
            except Exception as e:
                logger.error(f"❌ Lỗi không xác định khi tạo text channel: {e}")
                return None
            
        except discord.Forbidden:
            logger.error(f"Bot không có quyền tạo order channel trong guild {guild.name}")
            return None
        except Exception as e:
            logger.error(f"Lỗi tạo order channel: {e}")
            return None
    
    async def create_order_embed(self, user, package_id, package_info, order_id):
        """Create order confirmation embed"""
        embed = discord.Embed(
            title="🛒 Xác nhận đơn hàng EXP Rare",
            description=f"Đơn hàng #{order_id}",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👤 Khách hàng:",
            value=f"{user.mention} ({user.name})",
            inline=True
        )
        
        embed.add_field(
            name="📦 Sản phẩm:",
            value=f"**{package_info['name']}**",
            inline=True
        )
        
        embed.add_field(
            name="💰 Giá:",
            value=f"{package_info['price']:,} xu",
            inline=True
        )
        
        embed.add_field(
            name="⭐ EXP Rare nhận được:",
            value=f"{package_info['exp']:,} EXP",
            inline=True
        )
        
        embed.add_field(
            name="📅 Thời gian đặt:",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Trạng thái:",
            value="⏳ **Đang xử lý**",
            inline=True
        )
        
        embed.add_field(
            name="📋 Hướng dẫn:",
            value=(
                "• Admin sẽ xử lý đơn hàng của bạn\n"
                "• Vui lòng chờ xác nhận\n"
                "• Sử dụng ;stop để hoàn thành đơn hàng\n"
                "• Kênh này sẽ bị xóa sau khi hoàn thành"
            ),
            inline=False
        )
        
        embed.set_footer(
            text="EXP Rare Shop • Đơn hàng tự động",
            icon_url=user.display_avatar.url
        )
        
        return embed
    
    async def notify_order_handlers(self, guild, order_id, user, package_info, channel):
        """Gửi thông báo đến các order handlers và admin tối cao"""
        try:
            # Tạo embed thông báo
            embed = discord.Embed(
                title="🔔 Thông báo đơn hàng mới",
                description=f"Có đơn hàng EXP Rare cần xử lý!",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📦 Đơn hàng:",
                value=f"#{order_id}",
                inline=True
            )
            
            embed.add_field(
                name="👤 Khách hàng:",
                value=f"{user.mention} ({user.name})",
                inline=True
            )
            
            embed.add_field(
                name="🛒 Sản phẩm:",
                value=package_info['name'],
                inline=True
            )
            
            embed.add_field(
                name="💰 Giá trị:",
                value=f"{package_info['price']:,} xu",
                inline=True
            )
            
            embed.add_field(
                name="⭐ EXP Rare:",
                value=f"{package_info['exp']:,} EXP",
                inline=True
            )
            
            embed.add_field(
                name="🏠 Kênh xử lý:",
                value=channel.mention,
                inline=True
            )
            
            embed.add_field(
                name="📋 Hướng dẫn:",
                value="Vào kênh và sử dụng ;stop để hoàn thành đơn hàng",
                inline=False
            )
            
            embed.set_footer(
                text="Shop Order Notification",
                icon_url=user.display_avatar.url
            )
            
            # Gửi thông báo cho Supreme Admin
            supreme_admin_id = self.bot_instance.config.get('supreme_admin_id')
            if supreme_admin_id:
                try:
                    supreme_admin = self.bot.get_user(supreme_admin_id)
                    if supreme_admin:
                        # Tạo embed đặc biệt cho Supreme Admin
                        supreme_embed = discord.Embed(
                            title="👑 THÔNG BÁO ĐƠN HÀNG MỚI - SUPREME ADMIN",
                            description=f"Có đơn hàng EXP Rare mới cần được xử lý!",
                            color=discord.Color.gold(),
                            timestamp=datetime.now()
                        )
                        
                        supreme_embed.add_field(
                            name="📦 Mã đơn hàng:",
                            value=f"**#{order_id}**",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="👤 Khách hàng:",
                            value=f"{user.mention} ({user.name})\nID: {user.id}",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="🛒 Sản phẩm:",
                            value=f"**{package_info['name']}**",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="💰 Giá trị giao dịch:",
                            value=f"**{package_info['price']:,} xu**",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="⭐ EXP Rare:",
                            value=f"**{package_info['exp']:,} EXP**",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="🏠 Kênh xử lý:",
                            value=f"{channel.mention}\n(Chỉ role được cấu hình truy cập được)",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="🕐 Thời gian:",
                            value=f"<t:{int(datetime.now().timestamp())}:F>",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="📊 Trạng thái:",
                            value="⏳ **Đang chờ xử lý**",
                            inline=True
                        )
                        
                        supreme_embed.add_field(
                            name="👨‍💼 Quyền hạn Supreme Admin:",
                            value=(
                                "• Có thể truy cập kênh order\n"
                                "• Có thể sử dụng ;stop để hoàn thành\n"
                                "• Giám sát toàn bộ giao dịch\n"
                                "• Quản lý order handlers"
                            ),
                            inline=False
                        )
                        
                        supreme_embed.set_footer(
                            text="Supreme Admin Notification • EXP Rare Shop",
                            icon_url=user.display_avatar.url
                        )
                        
                        await supreme_admin.send(embed=supreme_embed)
                        logger.info(f"Đã gửi thông báo đơn hàng {order_id} cho Supreme Admin {supreme_admin_id}")
                        
                except Exception as e:
                    logger.error(f"Không thể gửi thông báo đến Supreme Admin {supreme_admin_id}: {e}")
            
            # Gửi thông báo cho tất cả Admin
            for admin_id in self.bot_instance.config.get('admin_ids', []):
                try:
                    admin_user = self.bot.get_user(admin_id)
                    if admin_user:
                        # Tạo embed cho Admin
                        admin_embed = discord.Embed(
                            title="🛡️ THÔNG BÁO ĐƠN HÀNG MỚI - ADMIN",
                            description=f"Có đơn hàng EXP Rare mới cần được xử lý!",
                            color=discord.Color.blue(),
                            timestamp=datetime.now()
                        )
                        
                        admin_embed.add_field(
                            name="📦 Mã đơn hàng:",
                            value=f"**#{order_id}**",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="👤 Khách hàng:",
                            value=f"{user.mention} ({user.name})\nID: {user.id}",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="🛒 Sản phẩm:",
                            value=f"**{package_info['name']}**",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="💰 Giá trị giao dịch:",
                            value=f"**{package_info['price']:,} xu**",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="⭐ EXP Rare:",
                            value=f"**{package_info['exp']:,} EXP**",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="🏠 Kênh xử lý:",
                            value=f"{channel.mention}\n(Chỉ role được cấu hình truy cập được)",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="🕐 Thời gian:",
                            value=f"<t:{int(datetime.now().timestamp())}:F>",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="📊 Trạng thái:",
                            value="⏳ **Đang chờ xử lý**",
                            inline=True
                        )
                        
                        admin_embed.add_field(
                            name="🛡️ Quyền hạn Admin:",
                            value=(
                                "• Có thể truy cập kênh order\n"
                                "• Có thể sử dụng ;stop để hoàn thành\n"
                                "• Giám sát giao dịch\n"
                                "• Quản lý đơn hàng"
                            ),
                            inline=False
                        )
                        
                        admin_embed.set_footer(
                            text="Admin Notification • EXP Rare Shop",
                            icon_url=user.display_avatar.url
                        )
                        
                        await admin_user.send(embed=admin_embed)
                        logger.info(f"Đã gửi thông báo đơn hàng {order_id} cho Admin {admin_id}")
                        
                except Exception as e:
                    logger.error(f"Không thể gửi thông báo đến Admin {admin_id}: {e}")
            
            # Gửi thông báo cho Order Handlers
            for handler_id in self.shop_config.get("order_handlers", []):
                handler_user = guild.get_member(handler_id)
                if handler_user:
                    try:
                        await handler_user.send(embed=embed)
                        logger.info(f"Đã gửi thông báo đơn hàng {order_id} cho handler {handler_id}")
                        
                    except Exception as e:
                        logger.error(f"Không thể gửi thông báo đến handler {handler_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Lỗi khi gửi thông báo order handlers: {e}")
    
    def is_shop_channel(self, channel):
        """Kiểm tra xem có phải kênh shop không"""
        # Kiểm tra kênh được cấu hình trong config trước
        configured_shop_channel = self.shop_config.get("shop_channel_id")
        if configured_shop_channel and channel.id == configured_shop_channel:
            return True
        
        # Fallback: Kiểm tra theo tên kênh (cũ)
        shop_keywords = ['shop', 'store', 'mua-ban', 'cua-hang', 'exp-rare']
        channel_name = channel.name.lower()
        
        # Kiểm tra tên kênh có chứa từ khóa shop không
        for keyword in shop_keywords:
            if keyword in channel_name:
                return True
        
        # Kiểm tra category có phải shop không
        if channel.category:
            category_name = channel.category.name.lower()
            for keyword in shop_keywords:
                if keyword in category_name:
                    return True
        
        return False
    
    async def refund_order(self, ctx, reason="Yêu cầu hoàn tiền"):
        """Hoàn tiền đơn hàng và xóa kênh"""
        try:
            # Tìm order ID từ tên kênh
            channel_name = ctx.channel.name
            order_id = None
            
            # Parse order ID từ tên kênh: order-user-package-timestamp
            parts = channel_name.split('-')
            if len(parts) >= 4:
                # Tạo order ID từ các phần
                order_id = f"{parts[1]}-{parts[2]}-{parts[3]}"
            
            if not order_id:
                await ctx.reply("❌ Không thể xác định mã đơn hàng từ tên kênh!", mention_author=True)
                return
            
            # Tìm thông tin đơn hàng
            order_info = None
            for oid, odata in self.orders_data.items():
                if oid.endswith(order_id) or order_id in oid:
                    order_info = odata
                    order_id = oid
                    break
            
            if not order_info:
                await ctx.reply(f"❌ Không tìm thấy thông tin đơn hàng: {order_id}", mention_author=True)
                return
            
            user_id = order_info['user_id']
            refund_amount = order_info['price']
            
            # Hoàn tiền cho user
            if hasattr(self.bot_instance, 'shared_wallet') and self.bot_instance.shared_wallet:
                self.bot_instance.shared_wallet.add_balance(user_id, refund_amount)
                logger.info(f"Refunded {refund_amount:,} xu to user {user_id} for order {order_id}")
            
            # Cập nhật trạng thái đơn hàng
            self.orders_data[order_id]['status'] = 'refunded'
            self.orders_data[order_id]['refund_reason'] = reason
            self.orders_data[order_id]['refunded_by'] = ctx.author.id
            self.orders_data[order_id]['refund_time'] = datetime.now().isoformat()
            self.save_orders_data()
            
            # Thông báo hoàn tiền thành công
            refund_embed = discord.Embed(
                title="💰 Đơn hàng đã được hoàn tiền",
                description=f"Đơn hàng #{order_id} đã được hoàn tiền thành công",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            refund_embed.add_field(
                name="💵 Số tiền hoàn:",
                value=f"{refund_amount:,} xu",
                inline=True
            )
            
            refund_embed.add_field(
                name="👤 Khách hàng:",
                value=f"<@{user_id}>",
                inline=True
            )
            
            refund_embed.add_field(
                name="📝 Lý do:",
                value=reason,
                inline=True
            )
            
            refund_embed.add_field(
                name="👨‍💼 Xử lý bởi:",
                value=f"{ctx.author.mention}",
                inline=True
            )
            
            refund_embed.set_footer(text="Kênh sẽ bị xóa sau 10 giây")
            
            await ctx.send(embed=refund_embed)
            
            # Thông báo cho user
            try:
                user = self.bot.get_user(user_id)
                if user:
                    user_embed = discord.Embed(
                        title="💰 Đơn hàng được hoàn tiền",
                        description=f"Đơn hàng #{order_id} của bạn đã được hoàn tiền",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    
                    user_embed.add_field(
                        name="💵 Số tiền nhận lại:",
                        value=f"{refund_amount:,} xu",
                        inline=True
                    )
                    
                    user_embed.add_field(
                        name="📝 Lý do hoàn tiền:",
                        value=reason,
                        inline=True
                    )
                    
                    user_embed.add_field(
                        name="👨‍💼 Xử lý bởi:",
                        value=f"Admin {ctx.author.name}",
                        inline=True
                    )
                    
                    current_balance = self.get_user_balance(user_id)
                    user_embed.add_field(
                        name="💰 Số dư hiện tại:",
                        value=f"{current_balance:,} xu",
                        inline=False
                    )
                    
                    user_embed.set_footer(text="Cảm ơn bạn đã sử dụng dịch vụ!")
                    
                    await user.send(embed=user_embed)
            except:
                pass
            
            # Xóa kênh sau 10 giây
            await asyncio.sleep(10)
            await ctx.channel.delete(reason=f"Order refunded by {ctx.author.name}: {reason}")
            
        except Exception as e:
            logger.error(f"Lỗi khi hoàn tiền order: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra khi hoàn tiền: {str(e)}", mention_author=True)
    
    async def notify_order_completion(self, user_id, order_id, package_info, completed_by):
        """Gửi thông báo hoàn thành đơn hàng đến người mua"""
        try:
            user = self.bot.get_user(user_id)
            if user:
                embed = discord.Embed(
                    title="✅ Đơn hàng hoàn thành!",
                    description=f"Đơn hàng #{order_id} đã được xử lý thành công",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📦 Sản phẩm:",
                    value=package_info,
                    inline=True
                )
                
                embed.add_field(
                    name="⭐ EXP Rare nhận được:",
                    value=f"{self.orders_data[order_id]['exp_amount']:,} EXP",
                    inline=True
                )
                
                embed.add_field(
                    name="👨‍💼 Xử lý bởi:",
                    value=f"<@{completed_by}>",
                    inline=True
                )
                
                embed.add_field(
                    name="💎 Tổng EXP Rare hiện có:",
                    value=f"{self.get_user_exp(user_id):,} EXP",
                    inline=False
                )
                
                embed.set_footer(
                    text="Cảm ơn bạn đã mua hàng!",
                    icon_url=user.display_avatar.url
                )
                
                await user.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Không thể gửi thông báo hoàn thành đến user {user_id}: {e}")
    
    async def add_allowed_role(self, ctx, role):
        """Thêm role vào danh sách được phép truy cập kênh order"""
        try:
            role_id = role.id
            role_name = role.name
            
            # Kiểm tra role đã tồn tại chưa
            if role_id in self.shop_config.get("allowed_roles", []):
                embed = discord.Embed(
                    title="⚠️ Role đã tồn tại",
                    description=f"Role **{role_name}** đã có trong danh sách được phép truy cập kênh order.",
                    color=discord.Color.orange()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Thêm role vào config
            if "allowed_roles" not in self.shop_config:
                self.shop_config["allowed_roles"] = []
            
            self.shop_config["allowed_roles"].append(role_id)
            self.save_shop_config()
            
            # Tạo embed thông báo thành công
            embed = discord.Embed(
                title="✅ Đã thêm role thành công",
                description=f"Role **{role_name}** đã được thêm vào danh sách được phép truy cập kênh order.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎭 Role được thêm:",
                value=f"{role.mention} ({role_name})",
                inline=True
            )
            
            embed.add_field(
                name="🆔 Role ID:",
                value=f"`{role_id}`",
                inline=True
            )
            
            embed.add_field(
                name="👨‍💼 Được thêm bởi:",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.add_field(
                name="🔑 Quyền hạn:",
                value=(
                    "• Xem tất cả kênh order\n"
                    "• Gửi tin nhắn trong kênh order\n"
                    "• Xóa tin nhắn (manage_messages)\n"
                    "• Xem lịch sử tin nhắn"
                ),
                inline=False
            )
            
            embed.set_footer(
                text="Shop System • Role Management",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Admin {ctx.author.id} đã thêm role {role_name} ({role_id}) vào allowed_roles")
            
        except Exception as e:
            logger.error(f"Lỗi khi thêm role {role.name}: {e}")
            embed = discord.Embed(
                title="❌ Lỗi khi thêm role",
                description=f"Có lỗi xảy ra khi thêm role **{role.name}**.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
    
    async def remove_allowed_role(self, ctx, role):
        """Xóa role khỏi danh sách được phép truy cập kênh order"""
        try:
            role_id = role.id
            role_name = role.name
            
            # Kiểm tra role có tồn tại không
            if role_id not in self.shop_config.get("allowed_roles", []):
                embed = discord.Embed(
                    title="⚠️ Role không tồn tại",
                    description=f"Role **{role_name}** không có trong danh sách được phép truy cập kênh order.",
                    color=discord.Color.orange()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            # Xóa role khỏi config
            self.shop_config["allowed_roles"].remove(role_id)
            self.save_shop_config()
            
            # Tạo embed thông báo thành công
            embed = discord.Embed(
                title="✅ Đã xóa role thành công",
                description=f"Role **{role_name}** đã được xóa khỏi danh sách được phép truy cập kênh order.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎭 Role được xóa:",
                value=f"{role.mention} ({role_name})",
                inline=True
            )
            
            embed.add_field(
                name="🆔 Role ID:",
                value=f"`{role_id}`",
                inline=True
            )
            
            embed.add_field(
                name="👨‍💼 Được xóa bởi:",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.add_field(
                name="⚠️ Lưu ý:",
                value="Role này sẽ không thể truy cập các kênh order mới được tạo.",
                inline=False
            )
            
            embed.set_footer(
                text="Shop System • Role Management",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Admin {ctx.author.id} đã xóa role {role_name} ({role_id}) khỏi allowed_roles")
            
        except Exception as e:
            logger.error(f"Lỗi khi xóa role {role.name}: {e}")
            embed = discord.Embed(
                title="❌ Lỗi khi xóa role",
                description=f"Có lỗi xảy ra khi xóa role **{role.name}**.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
    
    async def list_allowed_roles(self, ctx):
        """Hiển thị danh sách role được phép truy cập kênh order"""
        try:
            allowed_roles = self.shop_config.get("allowed_roles", [])
            
            embed = discord.Embed(
                title="🎭 Danh sách Role được phép truy cập kênh order",
                description="Các role này có thể xem và chat trong tất cả kênh order EXP Rare",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            if not allowed_roles:
                embed.add_field(
                    name="📝 Danh sách trống",
                    value="Chưa có role nào được thêm vào danh sách.\nSử dụng ; add @Role` để thêm role.",
                    inline=False
                )
            else:
                role_list = []
                for role_id in allowed_roles:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        role_list.append(f"• {role.mention} (`{role.name}` - ID: `{role_id}`)")
                    else:
                        role_list.append(f"• ⚠️ Role không tồn tại (ID: `{role_id}`)")
                
                embed.add_field(
                    name=f"📋 Danh sách ({len(allowed_roles)} role):",
                    value="\n".join(role_list) if role_list else "Không có role hợp lệ",
                    inline=False
                )
            
            embed.add_field(
                name="🔧 Quản lý:",
                value=(
                    "• ; add @Role` - Thêm role\n"
                    "• ; remove @Role` - Xóa role\n"
                    "• ; list` - Xem danh sách"
                ),
                inline=False
            )
            
            embed.set_footer(
                text="Shop System • Role Management",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị danh sách role: {e}")
            embed = discord.Embed(
                title="❌ Lỗi khi hiển thị danh sách",
                description="Có lỗi xảy ra khi hiển thị danh sách role.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
    
    async def buy_other_product(self, ctx, product_type):
        """Mua sản phẩm khác (Gmail, TikTok)"""
        if product_type not in self.other_products:
            await ctx.reply("❌ Sản phẩm không tồn tại!", mention_author=True)
            return
        
        product_info = self.other_products[product_type]
        user_balance = self.get_user_balance(ctx.author.id)
        
        if user_balance < product_info['price']:
            embed = discord.Embed(
                title="❌ Không đủ tiền",
                description="Bạn không có đủ xu để mua sản phẩm này!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="💰 Số dư hiện tại:",
                value=f"{user_balance:,} xu",
                inline=True
            )
            
            embed.add_field(
                name="💸 Cần thêm:",
                value=f"{product_info['price'] - user_balance:,} xu",
                inline=True
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            return
        
        # Kiểm tra có hàng trong kho không
        if product_type not in self.product_inventory or not self.product_inventory[product_type]:
            await ctx.reply(f"❌ Hiện tại hết hàng {product_info['name']}! Vui lòng liên hệ admin.", mention_author=True)
            return
        
        # Trừ tiền
        if not self.deduct_user_balance(ctx.author.id, product_info['price']):
            await ctx.reply("❌ Có lỗi xảy ra khi trừ tiền!", mention_author=True)
            return
        
        # Lấy sản phẩm từ kho
        product_item = self.product_inventory[product_type].pop(0)
        self.save_product_inventory()
        
        # Gửi sản phẩm qua DM
        try:
            dm_embed = discord.Embed(
                title=f"🎁 {product_info['name']} của bạn",
                description=f"Cảm ơn bạn đã mua {product_info['name']}!",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            dm_embed.add_field(
                name="📦 Sản phẩm:",
                value=product_info['name'],
                inline=True
            )
            
            dm_embed.add_field(
                name="💰 Giá:",
                value=f"{product_info['price']:,} xu",
                inline=True
            )
            
            dm_embed.add_field(
                name="📋 Thông tin sản phẩm:",
                value=f"```{product_item}```",
                inline=False
            )
            
            dm_embed.set_footer(text="Cảm ơn bạn đã sử dụng dịch vụ!")
            
            await ctx.author.send(embed=dm_embed)
            
            # Thông báo thành công
            success_embed = discord.Embed(
                title="✅ Mua hàng thành công!",
                description=f"Đã gửi {product_info['name']} vào DM của bạn!",
                color=discord.Color.green()
            )
            
            await ctx.reply(embed=success_embed, mention_author=True)
            
        except discord.Forbidden:
            # Không gửi được DM, hoàn tiền
            self.bot_instance.shared_wallet.add_balance(ctx.author.id, product_info['price'])
            self.product_inventory[product_type].insert(0, product_item)  # Trả lại hàng
            self.save_product_inventory()
            
            await ctx.reply(
                "❌ Không thể gửi DM cho bạn! Vui lòng bật DM và thử lại. Đã hoàn tiền.",
                mention_author=True
            )
    
    async def manage_product_inventory(self, ctx):
        """Quản lý kho hàng - chỉ Admin"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể quản lý kho hàng!", mention_author=True)
            return
        
        embed = discord.Embed(
            title="📦 Quản lý kho hàng",
            description="Hệ thống quản lý sản phẩm Gmail và TikTok",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Hiển thị số lượng hàng hiện có
        gmail_count = len(self.product_inventory.get("gmail", []))
        tiktok_count = len(self.product_inventory.get("tiktok", []))
        
        embed.add_field(
            name="📧 Gmail 1 tuần:",
            value=f"**{gmail_count}** sản phẩm có sẵn\n💰 Giá: 1,000,000 xu",
            inline=True
        )
        
        embed.add_field(
            name="📱 TikTok Account:",
            value=f"**{tiktok_count}** sản phẩm có sẵn\n💰 Giá: 1,000,000 xu",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Lệnh quản lý:",
            value=(
                "**📝 Thêm từ text:**\n"
                "`;shop hanghoa gmail user@gmail.com:password`\n"
                "`;shop hanghoa tiktok @username:password`\n\n"
                "**📁 Thêm từ file:**\n"
                "`;shop hanghoa gmail` + đính kèm file .txt\n"
                "`;shop hanghoa tiktok` + đính kèm file .txt\n\n"
                "**💡 File format:** Mỗi dòng = 1 tài khoản"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 Hướng dẫn:",
            value=(
                "• Nội dung sản phẩm sẽ được gửi trực tiếp cho khách hàng qua DM\n"
                "• Định dạng tùy ý, khách hàng sẽ nhận được chính xác nội dung bạn nhập\n"
                "• Khi hết hàng, khách hàng sẽ được thông báo liên hệ admin"
            ),
            inline=False
        )
        
        embed.set_footer(text="Shop System • Inventory Management")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def add_product_to_inventory(self, ctx, product_type, content):
        """Thêm sản phẩm vào kho - hỗ trợ file txt và text thường"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể thêm sản phẩm vào kho!", mention_author=True)
            return
        
        if product_type not in ["gmail", "tiktok"]:
            await ctx.reply("❌ Loại sản phẩm không hợp lệ! Chỉ hỗ trợ: gmail, tiktok", mention_author=True)
            return
        
        # Khởi tạo inventory nếu chưa có
        if product_type not in self.product_inventory:
            self.product_inventory[product_type] = []
        
        added_count = 0
        
        # Kiểm tra có file đính kèm không
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.filename.endswith('.txt'):
                    try:
                        # Đọc file txt
                        file_content = await attachment.read()
                        file_text = file_content.decode('utf-8')
                        
                        # Tách từng dòng và loại bỏ dòng trống
                        lines = [line.strip() for line in file_text.split('\n') if line.strip()]
                        
                        # Thêm từng dòng vào kho
                        for line in lines:
                            self.product_inventory[product_type].append(line)
                            added_count += 1
                        
                        self.save_product_inventory()
                        
                        # Thông báo thành công với file
                        product_name = self.other_products[product_type]['name']
                        embed = discord.Embed(
                            title="✅ Đã import sản phẩm từ file",
                            description=f"Đã thêm **{added_count}** {product_name} từ file `{attachment.filename}`!",
                            color=discord.Color.green(),
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(
                            name="📦 Loại sản phẩm:",
                            value=product_name,
                            inline=True
                        )
                        
                        embed.add_field(
                            name="📁 File xử lý:",
                            value=attachment.filename,
                            inline=True
                        )
                        
                        embed.add_field(
                            name="➕ Số lượng thêm:",
                            value=f"{added_count} tài khoản",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="📊 Tổng hiện có:",
                            value=f"{len(self.product_inventory[product_type])} sản phẩm",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="👨‍💼 Thêm bởi:",
                            value=ctx.author.mention,
                            inline=True
                        )
                        
                        embed.add_field(
                            name="📈 Tỷ lệ thành công:",
                            value="100%",
                            inline=True
                        )
                        
                        # Hiển thị preview 3 dòng đầu
                        if lines:
                            preview_lines = lines[:3]
                            preview_text = '\n'.join(preview_lines)
                            if len(lines) > 3:
                                preview_text += f"\n... và {len(lines) - 3} tài khoản khác"
                            
                            embed.add_field(
                                name="👀 Preview nội dung:",
                                value=f"```{preview_text}```",
                                inline=False
                            )
                        
                        embed.set_footer(text="Shop System • File Import Success")
                        
                        await ctx.reply(embed=embed, mention_author=True)
                        logger.info(f"Admin {ctx.author.id} import {added_count} {product_type} từ file {attachment.filename}")
                        return
                        
                    except UnicodeDecodeError:
                        await ctx.reply("❌ **Lỗi encoding!** File phải là UTF-8. Hãy save file với encoding UTF-8.", mention_author=True)
                        return
                    except Exception as e:
                        await ctx.reply(f"❌ **Lỗi khi đọc file:** {str(e)}", mention_author=True)
                        return
                else:
                    await ctx.reply("❌ **File không hợp lệ!** Chỉ hỗ trợ file .txt", mention_author=True)
                    return
        
        # Nếu không có file, xử lý text thường
        elif content:
            self.product_inventory[product_type].append(content)
            self.save_product_inventory()
            added_count = 1
            
            # Thông báo thành công với text
            product_name = self.other_products[product_type]['name']
            embed = discord.Embed(
                title="✅ Đã thêm sản phẩm vào kho",
                description=f"Đã thêm {product_name} vào kho hàng thành công!",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📦 Loại sản phẩm:",
                value=product_name,
                inline=True
            )
            
            embed.add_field(
                name="📊 Số lượng hiện có:",
                value=f"{len(self.product_inventory[product_type])} sản phẩm",
                inline=True
            )
            
            embed.add_field(
                name="👨‍💼 Được thêm bởi:",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.add_field(
                name="📋 Nội dung đã thêm:",
                value=f"```{content[:100]}{'...' if len(content) > 100 else ''}```",
                inline=False
            )
            
            embed.set_footer(text="Shop System • Manual Add")
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Admin {ctx.author.id} đã thêm {product_type} vào kho: {content[:50]}...")
        
        # Nếu không có cả file và content
        else:
            await ctx.reply(
                "❌ **Thiếu nội dung hoặc file!**\n\n"
                "**📝 Cách sử dụng:**\n"
                "• **Text:** `;shop hanghoa gmail user@gmail.com:password`\n"
                "• **File:** `;shop hanghoa gmail` + đính kèm file .txt\n\n"
                "**📁 Format file .txt:**\n"
                "```\n"
                "user1@gmail.com:password1\n"
                "user2@gmail.com:password2\n"
                "user3@gmail.com:password3\n"
                "...\n"
                "```\n\n"
                "**💡 Lưu ý:**\n"
                "• Mỗi dòng = 1 tài khoản\n"
                "• File phải là UTF-8 encoding\n"
                "• Dòng trống sẽ bị bỏ qua",
                mention_author=True
            )
    
    def register_commands(self):
        """Register all shop commands"""
        
        @self.bot.command(name='shop')
        async def shop_command(ctx, action=None, product_type=None, *, content=None):
            """Hiển thị shop EXP Rare hoặc quản lý sản phẩm"""
            # Kiểm tra kênh shop (DM chỉ cho admin)
            is_dm = isinstance(ctx.channel, discord.DMChannel)
            is_admin = self.bot_instance.is_admin(ctx.author.id)
            
            # Nếu không phải DM và không phải kênh shop
            if not is_dm and not self.is_shop_channel(ctx.channel):
                if is_admin:
                    await ctx.reply(
                        "❌ **Lệnh shop chỉ có thể sử dụng trong kênh shop hoặc DM!**\n\n"
                        "🛒 **Tìm kênh có tên chứa:** `shop`, `store`, `mua-ban`\n"
                        "💬 **Admin có thể sử dụng qua DM (tin nhắn riêng)**",
                        mention_author=True
                    )
                else:
                    await ctx.reply(
                        "❌ **Lệnh shop chỉ có thể sử dụng trong kênh shop!**\n\n"
                        "🛒 **Tìm kênh có tên chứa:** `shop`, `store`, `mua-ban`\n"
                        "📝 **Hoặc liên hệ admin để được hỗ trợ**",
                        mention_author=True
                    )
                return
            
            if action == "add" and isinstance(product_type, int):
                # Legacy: add order handler
                await self.add_order_handler(ctx, product_type)
            elif action == "remove" and isinstance(product_type, int):
                # Legacy: remove order handler  
                await self.remove_order_handler(ctx, product_type)
            elif action == "list":
                await self.list_order_handlers(ctx)
            elif action == "test":
                await self.test_wallet_connection(ctx)
            elif action == "hanghoa" and not product_type:
                # Hiển thị menu quản lý kho hàng
                await self.manage_product_inventory(ctx)
            elif action == "hanghoa" and product_type in ["gmail", "tiktok"]:
                # Thêm sản phẩm vào kho (có thể từ file hoặc content)
                await self.add_product_to_inventory(ctx, product_type, content)
            else:
                await self.show_shop(ctx)
        
        @self.bot.command(name='pendingorders', aliases=['pending', 'donhang'])
        async def pending_orders_command(ctx):
            """Xem danh sách đơn hàng đang chờ xử lý (Admin only)"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể xem danh sách đơn hàng!", mention_author=True)
                return
            
            if not self.pending_orders:
                embed = discord.Embed(
                    title="📋 Danh sách đơn hàng",
                    description="Hiện tại không có đơn hàng nào đang chờ xử lý!",
                    color=discord.Color.blue()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return
            
            embed = discord.Embed(
                title="📋 DANH SÁCH ĐƠN HÀNG ĐANG CHỜ",
                description=f"Có **{len(self.pending_orders)}** đơn hàng đang chờ xử lý",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            for i, (order_id, order_data) in enumerate(self.pending_orders.items(), 1):
                if i > 10:  # Chỉ hiển thị 10 đơn hàng đầu tiên
                    embed.add_field(
                        name="⚠️ Thông báo",
                        value=f"Còn {len(self.pending_orders) - 10} đơn hàng khác...",
                        inline=False
                    )
                    break
                
                try:
                    user = self.bot.get_user(order_data["user_id"])
                    username = user.display_name if user else f"User {order_data['user_id']}"
                    
                    order_time = datetime.fromisoformat(order_data["order_time"])
                    time_ago = datetime.now() - order_time
                    
                    if time_ago.days > 0:
                        time_str = f"{time_ago.days} ngày trước"
                    elif time_ago.seconds > 3600:
                        time_str = f"{time_ago.seconds // 3600} giờ trước"
                    else:
                        time_str = f"{time_ago.seconds // 60} phút trước"
                    
                    embed.add_field(
                        name=f"🆔 {order_id}",
                        value=(
                            f"👤 **{username}**\n"
                            f"📦 {order_data['package_name']}\n"
                            f"💰 {order_data['price']:,} xu → ⭐ {order_data['exp_amount']:,} EXP\n"
                            f"🕐 {time_str}"
                        ),
                        inline=True
                    )
                except Exception as e:
                    logger.error(f"Lỗi khi hiển thị đơn hàng {order_id}: {e}")
            
            embed.add_field(
                name="💡 Hướng dẫn xử lý:",
                value=(
                    "• **Reply tin nhắn DM** từ bot để hoàn thành đơn hàng\n"
                    "• Bot sẽ tự động cấp EXP và thông báo cho khách hàng\n"
                    "• Đơn hàng sẽ được chuyển vào lịch sử sau khi hoàn thành"
                ),
                inline=False
            )
            
            embed.set_footer(text="Sử dụng ;pendingorders để cập nhật danh sách")
            
            await ctx.reply(embed=embed, mention_author=True)
        
        @self.bot.command(name='buy')
        async def buy_command(ctx, package_type=None, package_id=None):
            """Mua sản phẩm - Có thể dùng trong kênh shop hoặc DM (Admin)"""
            # Kiểm tra kênh shop hoặc DM (chỉ admin)
            is_dm = isinstance(ctx.channel, discord.DMChannel)
            is_admin = self.bot_instance.is_admin(ctx.author.id)
            
            if not is_dm and not self.is_shop_channel(ctx.channel):
                if is_admin:
                    await ctx.reply(
                        "❌ **Lệnh mua hàng chỉ có thể sử dụng trong kênh shop hoặc DM!**\n\n"
                        "🛒 **Tìm kênh có tên chứa:** `shop`, `store`, `mua-ban`\n"
                        "💬 **Admin có thể sử dụng qua DM (tin nhắn riêng)**",
                        mention_author=True
                    )
                else:
                    await ctx.reply(
                        "❌ **Lệnh mua hàng chỉ có thể sử dụng trong kênh shop!**\n\n"
                        "🛒 **Tìm kênh có tên chứa:** `shop`, `store`, `mua-ban`\n"
                        "📝 **Hoặc liên hệ admin để được hỗ trợ**",
                        mention_author=True
                    )
                return
                
            if package_type == "gmail":
                await self.buy_other_product(ctx, "gmail")
            elif package_type == "tiktok":
                await self.buy_other_product(ctx, "tiktok")
            else:
                await ctx.reply(
                    "❌ **Cách sử dụng:**\n"
                    "`;buy gmail` - Mua Gmail 1 tuần (1 triệu xu)\n"
                    "`;buy tiktok` - Mua TikTok Account (1 triệu xu)\n\n"
                    "**Ví dụ:** `;buy gmail` - Mua Gmail 1 tuần\n\n"
                    "💡 **Lưu ý:** Chỉ sử dụng trong kênh shop này!",
                    mention_author=True
                )
        
        # EXP Rare command removed since we no longer sell EXP
        
        @self.bot.command(name='stop')
        async def stop_order_command(ctx):
            """Hoàn thành đơn hàng - chỉ Admin trong kênh order"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply(
                    "❌ **Chỉ Admin mới có thể hoàn thành đơn hàng!**\n\n"
                    "👑 **Quyền hạn:** Admin, Supreme Admin\n"
                    "📍 **Vị trí:** Kênh order (order-*)",
                    mention_author=True
                )
                return
            
            # Kiểm tra xem có phải kênh order không
            if not ctx.channel.name.startswith("order-"):
                await ctx.reply(
                    "❌ **Lệnh này chỉ sử dụng trong kênh đơn hàng!**\n\n"
                    "📍 **Kênh hợp lệ:** order-*\n"
                    "🔍 **Kênh hiện tại:** #{ctx.channel.name}",
                    mention_author=True
                )
                return
            
            await self.complete_order(ctx)
            
        @self.bot.command(name='refund')
        async def refund_order_command(ctx, reason=None):
            """Hoàn tiền đơn hàng - chỉ Admin trong kênh order"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply(
                    "❌ **Chỉ Admin mới có thể hoàn tiền!**\n\n"
                    "👑 **Quyền hạn:** Admin, Supreme Admin\n"
                    "📍 **Vị trí:** Kênh order (order-*)",
                    mention_author=True
                )
                return
            
            # Kiểm tra xem có phải kênh order không
            if not ctx.channel.name.startswith("order-"):
                await ctx.reply(
                    "❌ **Lệnh này chỉ sử dụng trong kênh đơn hàng!**\n\n"
                    "📍 **Kênh hợp lệ:** order-*\n"
                    "🔍 **Kênh hiện tại:** #{ctx.channel.name}",
                    mention_author=True
                )
                return
            
            await self.refund_order(ctx, reason or "Yêu cầu hoàn tiền")
        
        @self.bot.command(name='checkshoppermissions')
        async def check_shop_permissions_command(ctx):
            """Kiểm tra quyền của bot cho shop system - chỉ Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể kiểm tra permissions!", mention_author=True)
                return
            
            await self.check_shop_permissions(ctx)
        
        @self.bot.command(name='shopmanage')
        async def shop_management_command(ctx, action=None, target=None):
            """Quản lý shop system - chỉ Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể sử dụng lệnh này!", mention_author=True)
                return
            
            if action == "add" and target:
                await self.add_user_to_order_channel(ctx, target)
            else:
                # Hiển thị help
                help_embed = discord.Embed(
                    title="🛠️ Shop Management Commands",
                    description="Các lệnh quản lý shop system",
                    color=discord.Color.blue()
                )
                
                help_embed.add_field(
                    name=";shopmanage add <user_id>",
                    value="Thêm user vào kênh order để kiểm duyệt",
                    inline=False
                )
                
                help_embed.add_field(
                    name="Cách sử dụng:",
                    value=(
                        "• Sử dụng trong kênh order\n"
                        "• User sẽ có quyền xem và chat\n"
                        "• Dùng để thêm admin kiểm duyệt"
                    ),
                    inline=False
                )
                
                await ctx.reply(embed=help_embed, mention_author=True)
        
        @self.bot.command(name='role')
        async def role_command(ctx, action=None, role: discord.Role = None):
            """Quản lý role được phép truy cập kênh order - chỉ Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể quản lý role!", mention_author=True)
                return
            
            if action == "add" and role:
                await self.add_allowed_role(ctx, role)
            elif action == "remove" and role:
                await self.remove_allowed_role(ctx, role)
            elif action == "list":
                await self.list_allowed_roles(ctx)
            else:
                # Hiển thị help
                help_embed = discord.Embed(
                    title="🎭 Role Management Commands",
                    description="Quản lý role được phép truy cập kênh order EXP Rare",
                    color=discord.Color.blue()
                )
                
                help_embed.add_field(
                    name=";role add @Role",
                    value="Thêm role vào danh sách được phép truy cập kênh order",
                    inline=False
                )
                
                help_embed.add_field(
                    name=";role remove @Role",
                    value="Xóa role khỏi danh sách được phép truy cập kênh order",
                    inline=False
                )
                
                help_embed.add_field(
                    name=";role list",
                    value="Xem danh sách tất cả role được phép truy cập",
                    inline=False
                )
                
                help_embed.add_field(
                    name="🔑 Quyền hạn role:",
                    value=(
                        "• Xem tất cả kênh order EXP Rare\n"
                        "• Gửi tin nhắn trong kênh order\n"
                        "• Xóa tin nhắn (manage_messages)\n"
                        "• Xem lịch sử tin nhắn"
                    ),
                    inline=False
                )
                
                help_embed.add_field(
                    name="📝 Lưu ý:",
                    value=(
                        "• Chỉ Admin mới có thể quản lý role\n"
                        "• Role sẽ áp dụng cho tất cả kênh order mới\n"
                        "• Kênh order cũ không bị ảnh hưởng"
                    ),
                    inline=False
                )
                
                help_embed.set_footer(
                    text="Shop System • Role Management",
                    icon_url=ctx.author.display_avatar.url
                )
                
                await ctx.reply(embed=help_embed, mention_author=True)
        
        @self.bot.command(name='resetexp')
        async def reset_all_exp_command(ctx):
            """Reset tất cả EXP Rare về 0 - chỉ Supreme Admin"""
            if not self.bot_instance.is_supreme_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Supreme Admin mới có thể reset EXP Rare!", mention_author=True)
                return
            
            await self.reset_all_exp_rare(ctx)
        
        @self.bot.command(name='giveexp')
        async def give_exp_command_handler(ctx, user: discord.Member, amount: int):
            """Trao EXP Rare cho user - Admin only"""
            await self.give_exp_command(ctx, user, amount)
        
        @self.bot.command(name='setshop')
        async def set_shop_channel_command(ctx, channel: discord.TextChannel = None):
            """Cấu hình kênh shop chính thức - chỉ Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể cấu hình kênh shop!", mention_author=True)
                return
            
            await self.set_shop_channel(ctx, channel)
        
        @self.bot.command(name='shopconfig')
        async def shop_config_command(ctx):
            """Xem cấu hình shop hiện tại - chỉ Admin"""
            if not self.bot_instance.is_admin(ctx.author.id):
                await ctx.reply("❌ Chỉ Admin mới có thể xem cấu hình shop!", mention_author=True)
                return
            
            await self.show_shop_config(ctx)
    
    async def check_shop_permissions(self, ctx):
        """Kiểm tra chi tiết permissions của bot"""
        guild = ctx.guild
        bot_member = guild.me
        bot_permissions = bot_member.guild_permissions
        
        embed = discord.Embed(
            title="🔍 Kiểm tra quyền Bot - Shop System",
            description=f"Permissions của bot trong server **{guild.name}**",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Kiểm tra các quyền cần thiết
        required_permissions = {
            "manage_channels": "Tạo category và text channel",
            "send_messages": "Gửi tin nhắn trong channel",
            "embed_links": "Gửi embed",
            "read_message_history": "Xem lịch sử tin nhắn",
            "manage_messages": "Xóa tin nhắn (optional)",
            "add_reactions": "Thêm reaction (optional)"
        }
        
        permissions_status = ""
        all_good = True
        
        for perm_name, description in required_permissions.items():
            has_permission = getattr(bot_permissions, perm_name, False)
            status_icon = "✅" if has_permission else "❌"
            permissions_status += f"{status_icon} **{perm_name}**: {description}\n"
            
            if perm_name in ["manage_channels", "send_messages", "embed_links"] and not has_permission:
                all_good = False
        
        embed.add_field(
            name="📋 Quyền cần thiết:",
            value=permissions_status,
            inline=False
        )
        
        # Kiểm tra category Shop Orders
        category = discord.utils.get(guild.categories, name="🛒 Shop Orders")
        if category:
            # Kiểm tra permissions trong category
            category_permissions = category.permissions_for(bot_member)
            category_manage = category_permissions.manage_channels
            category_send = category_permissions.send_messages
            
            category_status = f"✅ Đã tồn tại (ID: {category.id})\n"
            category_status += f"🔹 Manage Channels trong category: {'✅' if category_manage else '❌'}\n"
            category_status += f"🔹 Send Messages trong category: {'✅' if category_send else '❌'}"
            
            embed.add_field(
                name="📁 Category '🛒 Shop Orders':",
                value=category_status,
                inline=False
            )
            
            if not category_manage:
                all_good = False
        else:
            embed.add_field(
                name="📁 Category '🛒 Shop Orders':",
                value="❌ Chưa tồn tại - sẽ được tạo khi có đơn hàng đầu tiên",
                inline=True
            )
        
        # Tổng kết
        if all_good:
            embed.add_field(
                name="🎯 Tổng kết:",
                value="✅ **Bot có đủ quyền để tạo order channel**",
                inline=False
            )
            embed.color = discord.Color.green()
        else:
            embed.add_field(
                name="🎯 Tổng kết:",
                value="❌ **Bot thiếu quyền quan trọng - cần cấp thêm quyền**",
                inline=False
            )
            embed.color = discord.Color.red()
        
        embed.add_field(
            name="🔧 Cách cấp quyền:",
            value=(
                "**Quyền Server:**\n"
                "1. Vào **Server Settings** > **Roles**\n"
                "2. Chọn role của bot\n"
                "3. Bật các quyền cần thiết\n\n"
                "**Quyền Category (nếu có lỗi):**\n"
                "1. Right-click category **🛒 Shop Orders**\n"
                "2. Chọn **Edit Category**\n"
                "3. Vào tab **Permissions**\n"
                "4. Thêm role bot và bật **Manage Channels**"
            ),
            inline=False
        )
        
        embed.set_footer(text="Shop System Permission Check")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def reset_all_exp_rare(self, ctx):
        """Reset tất cả EXP Rare về 0 - Với xác nhận an toàn"""
        # Đếm số users có EXP Rare
        users_with_exp = 0
        total_exp_removed = 0
        
        for user_id, user_data in self.shop_data.items():
            if user_data.get("exp_rare", 0) > 0:
                users_with_exp += 1
                total_exp_removed += user_data["exp_rare"]
        
        if users_with_exp == 0:
            await ctx.reply("ℹ️ Không có user nào có EXP Rare để reset!", mention_author=True)
            return
        
        # Tạo embed xác nhận
        confirm_embed = discord.Embed(
            title="⚠️ Xác nhận reset EXP Rare",
            description="Bạn có chắc chắn muốn reset tất cả EXP Rare về 0?",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        confirm_embed.add_field(
            name="📊 Thống kê:",
            value=f"• **{users_with_exp:,}** users có EXP Rare\n• **{total_exp_removed:,}** EXP sẽ bị xóa",
            inline=False
        )
        
        confirm_embed.add_field(
            name="⚠️ Cảnh báo:",
            value="**Hành động này KHÔNG THỂ HOÀN TÁC!**\nTất cả EXP Rare sẽ bị xóa vĩnh viễn.",
            inline=False
        )
        
        confirm_embed.add_field(
            name="🔧 Cách xác nhận:",
            value="Reply tin nhắn này với `CONFIRM` để thực hiện reset",
            inline=False
        )
        
        confirm_embed.set_footer(text="Shop System • EXP Reset")
        
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
            # Timeout - hủy reset
            timeout_embed = discord.Embed(
                title="⏰ Hết thời gian xác nhận",
                description="Reset EXP Rare đã bị hủy do không có xác nhận trong 30 giây.",
                color=discord.Color.red()
            )
            await ctx.followup.send(embed=timeout_embed)
            return
        
        # Thực hiện reset
        reset_count = 0
        for user_id, user_data in self.shop_data.items():
            if user_data.get("exp_rare", 0) > 0:
                user_data["exp_rare"] = 0
                reset_count += 1
        
        # Lưu data
        self.save_shop_data()
        
        # Thông báo thành công
        success_embed = discord.Embed(
            title="✅ Đã reset EXP Rare thành công",
            description="Tất cả EXP Rare đã được reset về 0",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        success_embed.add_field(
            name="📊 Kết quả:",
            value=f"• **{reset_count:,}** users đã bị reset\n• **{total_exp_removed:,}** EXP đã bị xóa",
            inline=False
        )
        
        success_embed.add_field(
            name="👨‍💼 Thực hiện bởi:",
            value=f"{ctx.author.mention} ({ctx.author.name})",
            inline=False
        )
        
        success_embed.set_footer(text="Shop System • EXP Reset Completed")
        
        await ctx.followup.send(embed=success_embed)
        
        # Log action
        logger.info(f"EXP Rare reset by {ctx.author.name} ({ctx.author.id}): {reset_count} users, {total_exp_removed} EXP removed")
    
    async def add_user_to_order_channel(self, ctx, user_id_str):
        """Thêm user vào kênh order để kiểm duyệt"""
        # Kiểm tra xem có phải kênh order không
        if not ctx.channel.name.startswith("order-"):
            await ctx.reply("❌ Lệnh này chỉ có thể sử dụng trong kênh đơn hàng!", mention_author=True)
            return
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            await ctx.reply("❌ User ID không hợp lệ! Vui lòng nhập số ID.", mention_author=True)
            return
        
        # Tìm user trong server
        user = ctx.guild.get_member(user_id)
        if not user:
            await ctx.reply("❌ Không tìm thấy user này trong server!", mention_author=True)
            return
        
        # Kiểm tra user đã có quyền chưa
        current_permissions = ctx.channel.permissions_for(user)
        if current_permissions.read_messages:
            await ctx.reply(f"⚠️ {user.mention} đã có quyền xem kênh này rồi!", mention_author=True)
            return
        
        try:
            # Thêm quyền cho user
            await ctx.channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                read_message_history=True
            )
            
            # Thông báo thành công
            success_embed = discord.Embed(
                title="✅ Đã thêm user vào kênh",
                description=f"User {user.mention} đã được thêm vào kênh order",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="👤 User được thêm:",
                value=f"{user.mention} ({user.name})",
                inline=True
            )
            
            success_embed.add_field(
                name="🔧 Quyền được cấp:",
                value="• Xem kênh\n• Gửi tin nhắn\n• Xem lịch sử",
                inline=True
            )
            
            success_embed.add_field(
                name="👨‍💼 Được thêm bởi:",
                value=f"{ctx.author.mention}",
                inline=True
            )
            
            success_embed.set_footer(text="Shop System • User Management")
            
            await ctx.reply(embed=success_embed, mention_author=True)
            
            # Thông báo cho user được thêm
            try:
                welcome_embed = discord.Embed(
                    title="🛒 Bạn đã được thêm vào kênh order",
                    description=f"Admin {ctx.author.mention} đã thêm bạn vào kênh {ctx.channel.mention}",
                    color=discord.Color.blue()
                )
                
                welcome_embed.add_field(
                    name="📋 Mục đích:",
                    value="Kiểm duyệt và hỗ trợ xử lý đơn hàng",
                    inline=False
                )
                
                await user.send(embed=welcome_embed)
            except discord.Forbidden:
                # Không gửi được DM, thông báo trong kênh
                await ctx.channel.send(f"👋 {user.mention} Chào mừng bạn đến kênh order! Bạn có thể xem và chat trong kênh này.")
                
        except discord.Forbidden:
            await ctx.reply("❌ Bot không có quyền chỉnh sửa permissions của kênh này!", mention_author=True)
        except Exception as e:
            logger.error(f"Lỗi khi thêm user {user_id} vào kênh {ctx.channel.id}: {e}")
            await ctx.reply("❌ Có lỗi xảy ra khi thêm user vào kênh!", mention_author=True)
    
    async def add_order_handler(self, ctx, user_id):
        """Thêm order handler"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể thêm Order Handler!", mention_author=True)
            return
        
        # Kiểm tra user có tồn tại không
        user = ctx.guild.get_member(user_id)
        if not user:
            await ctx.reply("❌ Không tìm thấy user này trong server!", mention_author=True)
            return
        
        # Kiểm tra đã là handler chưa
        if user_id in self.shop_config.get("order_handlers", []):
            await ctx.reply(f"❌ {user.mention} đã là Order Handler rồi!", mention_author=True)
            return
        
        # Thêm vào danh sách
        if "order_handlers" not in self.shop_config:
            self.shop_config["order_handlers"] = []
        
        self.shop_config["order_handlers"].append(user_id)
        self.save_shop_config()
        
        embed = discord.Embed(
            title="✅ Thêm Order Handler thành công",
            description=f"Đã thêm {user.mention} vào danh sách Order Handler",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👤 Order Handler mới:",
            value=f"{user.mention} ({user.name})",
            inline=True
        )
        
        embed.add_field(
            name="🔔 Quyền hạn:",
            value=(
                "• Nhận thông báo đơn hàng mới\n"
                "• Truy cập kênh order\n"
                "• Sử dụng lệnh ;`"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📊 Tổng Order Handler:",
            value=f"{len(self.shop_config['order_handlers'])} người",
            inline=True
        )
        
        embed.set_footer(text="Shop Management")
        
        await ctx.reply(embed=embed, mention_author=True)
        
        # Thông báo cho user được thêm
        try:
            welcome_embed = discord.Embed(
                title="🎉 Chúc mừng! Bạn đã trở thành Order Handler",
                description="Bạn đã được thêm vào danh sách xử lý đơn hàng EXP Rare Shop",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            welcome_embed.add_field(
                name="🔔 Nhiệm vụ:",
                value=(
                    "• Nhận thông báo khi có đơn hàng mới\n"
                    "• Vào kênh order để xử lý\n"
                    "• Sử dụng ;stop để hoàn thành đơn hàng"
                ),
                inline=False
            )
            
            welcome_embed.add_field(
                name="📋 Lưu ý:",
                value=(
                    "• Bạn sẽ nhận DM khi có đơn hàng mới\n"
                    "• Chỉ sử dụng ;` trong kênh order\n"
                    "• Liên hệ admin nếu có vấn đề"
                ),
                inline=False
            )
            
            welcome_embed.set_footer(text="EXP Rare Shop • Order Handler")
            
            await user.send(embed=welcome_embed)
        except:
            pass
    
    async def remove_order_handler(self, ctx, user_id):
        """Xóa order handler"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể xóa Order Handler!", mention_author=True)
            return
        
        # Kiểm tra có trong danh sách không
        if user_id not in self.shop_config.get("order_handlers", []):
            await ctx.reply("❌ User này không phải Order Handler!", mention_author=True)
            return
        
        # Xóa khỏi danh sách
        self.shop_config["order_handlers"].remove(user_id)
        self.save_shop_config()
        
        user = ctx.guild.get_member(user_id)
        user_name = user.name if user else f"User ID: {user_id}"
        
        embed = discord.Embed(
            title="✅ Xóa Order Handler thành công",
            description=f"Đã xóa {user.mention if user else user_name} khỏi danh sách Order Handler",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Tổng Order Handler còn lại:",
            value=f"{len(self.shop_config['order_handlers'])} người",
            inline=True
        )
        
        embed.set_footer(text="Shop Management")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def list_order_handlers(self, ctx):
        """Liệt kê order handlers"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể xem danh sách Order Handler!", mention_author=True)
            return
        
        handlers = self.shop_config.get("order_handlers", [])
        
        embed = discord.Embed(
            title="📋 Danh sách Order Handler",
            description=f"Có {len(handlers)} Order Handler đang hoạt động",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if handlers:
            handler_list = []
            for i, handler_id in enumerate(handlers, 1):
                user = ctx.guild.get_member(handler_id)
                if user:
                    handler_list.append(f"{i}. {user.mention} ({user.name})")
                else:
                    handler_list.append(f"{i}. User ID: {handler_id} (Không trong server)")
            
            embed.add_field(
                name="👥 Order Handlers:",
                value="\n".join(handler_list),
                inline=False
            )
        else:
            embed.add_field(
                name="📝 Trạng thái:",
                value="Chưa có Order Handler nào",
                inline=False
            )
        
        embed.add_field(
            name="🔧 Quản lý:",
            value=(
                "• ; add <user_id>` - Thêm handler\n"
                "• ; remove <user_id>` - Xóa handler\n"
                "• ; list` - Xem danh sách"
            ),
            inline=False
        )
        
        embed.set_footer(text="Shop Management")
        
        await ctx.reply(embed=embed, mention_author=True)
    
    async def test_wallet_connection(self, ctx):
        """Test kết nối với shared wallet"""
        embed = discord.Embed(
            title="🔧 Test Wallet Connection",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Test bot instance
        embed.add_field(
            name="🤖 Bot Instance:",
            value="✅ OK" if self.bot_instance else "❌ Không có",
            inline=True
        )
        
        # Test shared wallet attribute
        has_wallet = hasattr(self.bot_instance, 'shared_wallet')
        embed.add_field(
            name="💰 Shared Wallet Attribute:",
            value="✅ Có" if has_wallet else "❌ Không có",
            inline=True
        )
        
        # Test shared wallet instance
        wallet_instance = None
        if has_wallet:
            wallet_instance = self.bot_instance.shared_wallet
        
        embed.add_field(
            name="💳 Wallet Instance:",
            value="✅ OK" if wallet_instance else "❌ None",
            inline=True
        )
        
        # Test get balance
        try:
            if wallet_instance:
                balance = wallet_instance.get_balance(ctx.author.id)
                embed.add_field(
                    name="💵 Số dư của bạn:",
                    value=f"✅ {balance:,} xu",
                    inline=True
                )
            else:
                embed.add_field(
                    name="💵 Số dư:",
                    value="❌ Không thể lấy",
                    inline=True
                )
        except Exception as e:
            embed.add_field(
                name="💵 Lỗi get balance:",
                value=f"❌ {str(e)}",
                inline=True
            )
        
        # Test file path
        if wallet_instance:
            embed.add_field(
                name="📁 File path:",
                value=f"✅ {wallet_instance.wallet_file}",
                inline=False
            )
        
        embed.set_footer(text="Shop Debug Info")
        await ctx.reply(embed=embed, mention_author=True)
    
    async def show_shop(self, ctx):
        """Hiển thị shop EXP Rare với giao diện đẹp"""
        embed = discord.Embed(
            title="✨ DIGITAL PRODUCTS SHOP ✨",
            description="🌟 **Cửa hàng sản phẩm số** - Gmail & TikTok chất lượng cao!",
            color=0xFFD700,  # Vàng đẹp hơn
            timestamp=datetime.now()
        )
        
        # Hiển thị thông tin user với style đẹp
        user_balance = self.get_user_balance(ctx.author.id)
        user_exp = self.get_user_exp(ctx.author.id)
        
        embed.add_field(
            name="💎 THÔNG TIN TÀI KHOẢN",
            value=(
                f"👤 **{ctx.author.display_name}**\n"
                f"💰 **Số dư:** {user_balance:,} xu\n"
                f"🛒 **Trạng thái:** Sẵn sàng mua sắm"
            ),
            inline=False
        )
        
        # Chỉ bán Gmail và TikTok
        embed.add_field(
            name="🎯 SẢN PHẨM HIỆN CÓ",
            value=(
                "📧 **Gmail 1 tuần** - 1 triệu xu\n"
                "📱 **TikTok Account** - 1 triệu xu\n\n"
                "🔒 **Giao hàng:** Tự động qua DM riêng tư\n"
                "✅ **Chất lượng:** Được kiểm tra kỹ lưỡng"
            ),
            inline=False
        )
        
        # Sản phẩm khác
        gmail_count = len(self.product_inventory.get("gmail", []))
        tiktok_count = len(self.product_inventory.get("tiktok", []))
        
        embed.add_field(
            name="📧 GMAIL 1 TUẦN",
            value=(
                f"💰 **Giá:** 1 triệu xu\n"
                f"📦 **Có sẵn:** {gmail_count} tài khoản\n"
                f"⏰ **Thời hạn:** 1 tuần sử dụng\n"
                f"🔒 **Giao hàng:** Qua DM riêng tư"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📱 TIKTOK ACCOUNT",
            value=(
                f"💰 **Giá:** 1 triệu xu\n"
                f"📦 **Có sẵn:** {tiktok_count} tài khoản\n"
                f"✨ **Chất lượng:** Tài khoản đã tạo sẵn\n"
                f"🔒 **Giao hàng:** Qua DM riêng tư"
            ),
            inline=True
        )
        
        # Hướng dẫn mua hàng
        embed.add_field(
            name="🛒 HƯỚNG DẪN MUA HÀNG",
            value=(
                "📧 **Gmail:** `;buy gmail`\n"
                "📱 **TikTok:** `;buy tiktok`\n\n"
                "💡 **Ví dụ:** `;buy gmail` - Mua Gmail 1 tuần\n"
                "✅ **Giao hàng:** Tự động qua DM riêng tư"
            ),
            inline=False
        )
        
        # Thêm thông tin admin nếu là admin
        if self.bot_instance.is_admin(ctx.author.id):
            embed.add_field(
                name="👑 LỆNH ADMIN - QUẢN LÝ HÀNG HÓA",
                value=(
                    "📦 **Xem kho:** `;shop hanghoa`\n"
                    "📝 **Thêm từ text:** `;shop hanghoa gmail user@gmail.com:pass`\n"
                    "📁 **Thêm từ file:** `;shop hanghoa gmail` + đính kèm file .txt\n"
                    "📱 **TikTok:** `;shop hanghoa tiktok @user:pass`\n\n"
                    "💬 **Có thể sử dụng qua DM** (chỉ Admin)\n"
                    "📄 **File format:** Mỗi dòng = 1 tài khoản"
                ),
                inline=False
            )
        
        # Thêm thumbnail và footer đẹp
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/741090906504290334.png")
        embed.set_footer(
            text="🌟 Digital Products Shop • Gmail & TikTok • 24/7 Support",
            icon_url=ctx.author.display_avatar.url
        )
        
        # Thêm author để làm đẹp
        embed.set_author(
            name="Premium Digital Store",
            icon_url="https://cdn.discordapp.com/emojis/741090906504290334.png"
        )
        
        await ctx.reply(embed=embed, mention_author=True)
    
    # buy_exp_package function removed - no longer selling EXP
    
    async def notify_admin_dm(self, ctx, order_id, package_info):
        """Gửi DM cho admin về đơn hàng mới"""
        try:
            # Tạo embed thông báo cho admin
            admin_embed = discord.Embed(
                title="🛒 ĐƠN HÀNG MỚI - THÔNG BÁO TẤT CẢ ADMIN",
                description=f"Có đơn hàng EXP Rare mới cần xử lý từ {ctx.author.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            admin_embed.add_field(
                name="🆔 Mã đơn hàng:",
                value=f"**{order_id}**",
                inline=False
            )
            
            admin_embed.add_field(
                name="👤 Khách hàng:",
                value=f"{ctx.author.mention} ({ctx.author.display_name})\nID: {ctx.author.id}",
                inline=True
            )
            
            admin_embed.add_field(
                name="📦 Sản phẩm:",
                value=f"**{package_info['name']}**",
                inline=True
            )
            
            admin_embed.add_field(
                name="💰 Giá trị:",
                value=f"**{package_info['price']:,} xu**",
                inline=True
            )
            
            admin_embed.add_field(
                name="⭐ EXP Rare:",
                value=f"**{package_info['exp']:,} EXP**",
                inline=True
            )
            
            admin_embed.add_field(
                name="🕐 Thời gian:",
                value=f"<t:{int(datetime.now().timestamp())}:F>",
                inline=True
            )
            
            admin_embed.add_field(
                name="📍 Server:",
                value=f"{ctx.guild.name}",
                inline=True
            )
            
            admin_embed.add_field(
                name="📝 Hướng dẫn xử lý:",
                value=(
                    "**Reply tin nhắn này** để hoàn thành đơn hàng!\n"
                    "• Bot sẽ tự động cấp EXP cho user\n"
                    "• User sẽ nhận thông báo hoàn thành\n"
                    "• Đơn hàng sẽ được đánh dấu hoàn thành\n"
                    "• Thông báo này được gửi đến tất cả Admin"
                ),
                inline=False
            )
            
            admin_embed.set_footer(text="Reply tin nhắn này để xử lý đơn hàng!")
            
            # Gửi DM cho Supreme Admin và Order Handlers
            admins_notified = []
            
            # Gửi cho Supreme Admin
            supreme_admin_id = self.bot_instance.supreme_admin_id
            if supreme_admin_id:
                try:
                    supreme_admin = self.bot.get_user(supreme_admin_id)
                    if supreme_admin:
                        await supreme_admin.send(embed=admin_embed)
                        admins_notified.append(f"Supreme Admin ({supreme_admin.display_name})")
                        logger.info(f"Đã gửi thông báo đơn hàng {order_id} cho Supreme Admin {supreme_admin_id}")
                except Exception as e:
                    logger.error(f"Không thể gửi DM cho Supreme Admin {supreme_admin_id}: {e}")
            
            # Gửi cho tất cả Admin
            admin_ids = self.bot_instance.config.get('admin_ids', [])
            for admin_id in admin_ids:
                try:
                    admin = self.bot.get_user(admin_id)
                    if admin:
                        await admin.send(embed=admin_embed)
                        admins_notified.append(f"Admin ({admin.display_name})")
                        logger.info(f"Đã gửi thông báo đơn hàng {order_id} cho admin {admin_id}")
                except Exception as e:
                    logger.error(f"Không thể gửi DM cho admin {admin_id}: {e}")
            
            # Gửi cho Order Handlers (nếu có)
            order_handlers = self.shop_config.get("order_handlers", [])
            for handler_id in order_handlers:
                try:
                    handler = self.bot.get_user(handler_id)
                    if handler:
                        await handler.send(embed=admin_embed)
                        admins_notified.append(f"Handler ({handler.display_name})")
                        logger.info(f"Đã gửi thông báo đơn hàng {order_id} cho handler {handler_id}")
                except Exception as e:
                    logger.error(f"Không thể gửi DM cho handler {handler_id}: {e}")
            
            if admins_notified:
                logger.info(f"Đã thông báo đơn hàng {order_id} cho: {', '.join(admins_notified)}")
            else:
                logger.warning(f"Không thể thông báo đơn hàng {order_id} cho admin nào!")
                
        except Exception as e:
            logger.error(f"Lỗi khi gửi thông báo admin cho đơn hàng {order_id}: {e}")
    
    async def process_admin_reply(self, message):
        """Xử lý khi admin reply DM để hoàn thành đơn hàng"""
        try:
            # Kiểm tra xem có phải admin không
            if not (self.bot_instance.is_admin(message.author.id) or 
                    message.author.id == self.bot_instance.supreme_admin_id):
                return False
            
            # Kiểm tra xem có phải reply không
            if not message.reference or not message.reference.message_id:
                return False
            
            # Lấy tin nhắn được reply
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
            except:
                return False
            
            # Kiểm tra xem tin nhắn được reply có phải từ bot không
            if replied_message.author.id != self.bot.user.id:
                return False
            
            # Tìm order ID từ embed
            if not replied_message.embeds:
                return False
            
            embed = replied_message.embeds[0]
            order_id = None
            
            # Tìm order ID trong embed fields
            for field in embed.fields:
                if field.name == "🆔 Mã đơn hàng:":
                    order_id = field.value.strip("*")
                    break
            
            if not order_id or order_id not in self.pending_orders:
                return False
            
            # Lấy thông tin đơn hàng
            order_data = self.pending_orders[order_id]
            
            # Cấp EXP cho user
            self.add_user_exp(order_data["user_id"], order_data["exp_amount"])
            
            # Chuyển đơn hàng sang completed
            self.orders_data[order_id] = {
                **order_data,
                "status": "completed",
                "completed_time": datetime.now().isoformat(),
                "completed_by": message.author.id,
                "admin_reply": message.content
            }
            self.save_orders_data()
            
            # Xóa khỏi pending orders
            del self.pending_orders[order_id]
            self.save_pending_orders()
            
            # Thông báo cho admin
            admin_success_embed = discord.Embed(
                title="✅ Đơn hàng đã hoàn thành!",
                description=f"Đơn hàng `{order_id}` đã được xử lý thành công",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            admin_success_embed.add_field(
                name="👤 Khách hàng:",
                value=f"<@{order_data['user_id']}> ({order_data['user_display_name']})",
                inline=True
            )
            
            admin_success_embed.add_field(
                name="⭐ EXP đã cấp:",
                value=f"**{order_data['exp_amount']:,} EXP Rare**",
                inline=True
            )
            
            admin_success_embed.add_field(
                name="💬 Ghi chú admin:",
                value=f"*{message.content}*" if message.content else "*Không có ghi chú*",
                inline=False
            )
            
            await message.reply(embed=admin_success_embed)
            
            # Thông báo cho user
            try:
                user = self.bot.get_user(order_data["user_id"])
                if user:
                    user_success_embed = discord.Embed(
                        title="🎉 Đơn hàng hoàn thành!",
                        description=f"Đơn hàng `{order_id}` của bạn đã được xử lý thành công!",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    
                    user_success_embed.add_field(
                        name="📦 Sản phẩm:",
                        value=f"**{order_data['package_name']}**",
                        inline=False
                    )
                    
                    user_success_embed.add_field(
                        name="⭐ EXP Rare nhận được:",
                        value=f"**+{order_data['exp_amount']:,} EXP**",
                        inline=True
                    )
                    
                    user_success_embed.add_field(
                        name="💰 Đã thanh toán:",
                        value=f"**{order_data['price']:,} xu**",
                        inline=True
                    )
                    
                    if message.content:
                        user_success_embed.add_field(
                            name="💬 Lời nhắn từ admin:",
                            value=f"*{message.content}*",
                            inline=False
                        )
                    
                    user_success_embed.set_footer(text="Cảm ơn bạn đã sử dụng dịch vụ!")
                    
                    await user.send(embed=user_success_embed)
                    logger.info(f"Đã thông báo hoàn thành đơn hàng {order_id} cho user {order_data['user_id']}")
            except Exception as e:
                logger.error(f"Không thể gửi thông báo hoàn thành cho user {order_data['user_id']}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý admin reply: {e}")
            return False
    
    async def complete_order(self, ctx):
        """Hoàn thành đơn hàng"""
        # Tìm đơn hàng từ tên kênh
        channel_name = ctx.channel.name
        order_id = None
        
        for oid, order_data in self.orders_data.items():
            if order_data.get("channel_id") == ctx.channel.id:
                order_id = oid
                break
        
        if not order_id:
            await ctx.send("❌ Không tìm thấy thông tin đơn hàng!")
            return
        
        order_data = self.orders_data[order_id]
        
        # Thêm EXP cho user
        self.add_user_exp(order_data["user_id"], order_data["exp_amount"])
        
        # Cập nhật trạng thái đơn hàng
        self.orders_data[order_id]["status"] = "completed"
        self.orders_data[order_id]["completed_time"] = datetime.now().isoformat()
        self.orders_data[order_id]["completed_by"] = ctx.author.id
        self.save_orders_data()
        
        # Thông báo hoàn thành
        complete_embed = discord.Embed(
            title="✅ Đơn hàng hoàn thành!",
            description=f"Đơn hàng #{order_id} đã được xử lý thành công",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        complete_embed.add_field(
            name="👤 Khách hàng:",
            value=f"<@{order_data['user_id']}>",
            inline=True
        )
        
        complete_embed.add_field(
            name="📦 Sản phẩm:",
            value=order_data["package_name"],
            inline=True
        )
        
        complete_embed.add_field(
            name="⭐ EXP đã thêm:",
            value=f"{order_data['exp_amount']:,} EXP Rare",
            inline=True
        )
        
        complete_embed.add_field(
            name="👨‍💼 Xử lý bởi:",
            value=ctx.author.mention,
            inline=True
        )
        
        complete_embed.set_footer(text="Kênh sẽ bị xóa sau 30 giây")
        
        await ctx.send(embed=complete_embed)
        
        # Gửi thông báo hoàn thành đến người mua
        await self.notify_order_completion(
            order_data["user_id"], 
            order_id, 
            order_data["package_name"], 
            ctx.author.id
        )
        
        # Xóa kênh sau 30 giây
        await asyncio.sleep(30)
        try:
            await ctx.channel.delete(reason=f"Đơn hàng #{order_id} hoàn thành")
        except:
            pass
    
    async def handle_admin_reply(self, message):
        """Xử lý khi admin reply tin nhắn DM để hoàn thành đơn hàng"""
        try:
            # Kiểm tra xem có phải admin không
            if not (self.bot_instance.is_admin(message.author.id) or 
                   message.author.id in self.shop_config.get("order_handlers", [])):
                return False
            
            # Kiểm tra xem có phải reply không
            if not message.reference or not message.reference.message_id:
                return False
            
            # Lấy tin nhắn gốc
            try:
                original_message = await message.channel.fetch_message(message.reference.message_id)
            except:
                return False
            
            # Kiểm tra xem tin nhắn gốc có phải từ bot không
            if original_message.author.id != self.bot.user.id:
                return False
            
            # Kiểm tra xem có embed đơn hàng không
            if not original_message.embeds:
                return False
            
            embed = original_message.embeds[0]
            if "ĐƠN HÀNG MỚI - SHOP EXP RARE" not in embed.title:
                return False
            
            # Tìm order ID từ embed
            order_id = None
            for field in embed.fields:
                if field.name == "🆔 Mã đơn hàng:":
                    order_id = field.value.strip("*")
                    break
            
            if not order_id or order_id not in self.pending_orders:
                await message.reply("❌ Không tìm thấy đơn hàng hoặc đơn hàng đã được xử lý!")
                return True
            
            # Xử lý đơn hàng
            order_data = self.pending_orders[order_id]
            
            # Cấp EXP cho user (giả lập - cần tích hợp với hệ thống EXP thực tế)
            user_id = order_data["user_id"]
            exp_amount = order_data["exp_amount"]
            
            # Lưu vào lịch sử đơn hàng
            self.orders_data[order_id] = {
                **order_data,
                "status": "completed",
                "completed_by": message.author.id,
                "completed_by_name": message.author.display_name,
                "completion_time": datetime.now().isoformat(),
                "admin_note": message.content[:500] if message.content else "Đã xử lý"
            }
            
            # Xóa khỏi pending orders
            del self.pending_orders[order_id]
            
            # Lưu dữ liệu
            self.save_orders_data()
            self.save_pending_orders()
            
            # Thông báo hoàn thành cho admin
            success_embed = discord.Embed(
                title="✅ Đơn hàng đã hoàn thành!",
                description=f"Đơn hàng `{order_id}` đã được xử lý thành công!",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="👤 Khách hàng:",
                value=f"<@{user_id}> ({order_data['user_display_name']})",
                inline=True
            )
            
            success_embed.add_field(
                name="📦 Sản phẩm:",
                value=order_data["package_name"],
                inline=True
            )
            
            success_embed.add_field(
                name="⭐ EXP đã cấp:",
                value=f"{exp_amount:,} EXP Rare",
                inline=True
            )
            
            success_embed.add_field(
                name="💬 Ghi chú:",
                value=message.content[:100] + "..." if len(message.content) > 100 else message.content or "Không có ghi chú",
                inline=False
            )
            
            success_embed.set_footer(text="Khách hàng đã được thông báo!")
            
            await message.reply(embed=success_embed)
            
            # Thông báo cho khách hàng
            await self.notify_customer_completion(order_id, order_data, message.author)
            
            logger.info(f"Đơn hàng {order_id} đã được hoàn thành bởi {message.author.display_name} ({message.author.id})")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý admin reply: {e}")
            await message.reply("❌ Có lỗi xảy ra khi xử lý đơn hàng!")
            return True
    
    async def notify_customer_completion(self, order_id, order_data, admin):
        """Thông báo cho khách hàng khi đơn hàng hoàn thành"""
        try:
            user = self.bot.get_user(order_data["user_id"])
            if not user:
                return
            
            completion_embed = discord.Embed(
                title="🎉 Đơn hàng hoàn thành!",
                description=f"Đơn hàng `{order_id}` của bạn đã được xử lý thành công!",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            completion_embed.add_field(
                name="📦 Sản phẩm:",
                value=order_data["package_name"],
                inline=True
            )
            
            completion_embed.add_field(
                name="⭐ EXP nhận được:",
                value=f"**{order_data['exp_amount']:,} EXP Rare**",
                inline=True
            )
            
            completion_embed.add_field(
                name="👨‍💼 Xử lý bởi:",
                value=f"{admin.display_name}",
                inline=True
            )
            
            completion_embed.add_field(
                name="🕐 Thời gian hoàn thành:",
                value=f"<t:{int(datetime.now().timestamp())}:F>",
                inline=False
            )
            
            completion_embed.set_footer(text="Cảm ơn bạn đã sử dụng dịch vụ!")
            
            await user.send(embed=completion_embed)
            logger.info(f"Đã thông báo hoàn thành đơn hàng {order_id} cho user {order_data['user_id']}")
            
        except Exception as e:
            logger.error(f"Không thể thông báo hoàn thành cho user {order_data['user_id']}: {e}")
    
    async def give_exp_command(self, ctx, user: discord.Member, amount: int):
        """Trao EXP Rare cho user - Admin only"""
        if not self.bot_instance.is_admin(ctx.author.id):
            await ctx.reply("❌ Chỉ Admin mới có thể trao EXP!", mention_author=True)
            return
        
        if amount <= 0:
            await ctx.reply("❌ Số EXP phải lớn hơn 0!", mention_author=True)
            return
        
        # Trao EXP cho user
        self.add_user_exp(user.id, amount)
        
        # Tạo embed thông báo
        embed = discord.Embed(
            title="✅ Đã trao EXP Rare thành công",
            description=f"Đã trao {amount:,} EXP Rare cho {user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👤 Người nhận:",
            value=f"{user.mention} ({user.display_name})",
            inline=True
        )
        
        embed.add_field(
            name="⭐ EXP được trao:",
            value=f"{amount:,} EXP Rare",
            inline=True
        )
        
        embed.add_field(
            name="💎 Tổng EXP hiện có:",
            value=f"{self.get_user_exp(user.id):,} EXP Rare",
            inline=True
        )
        
        embed.add_field(
            name="👨‍💼 Được trao bởi:",
            value=ctx.author.mention,
            inline=False
        )
        
        embed.set_footer(
            text="Shop System • Manual EXP Grant",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed, mention_author=True)
        logger.info(f"Admin {ctx.author.id} đã trao {amount} EXP Rare cho user {user.id}")
        
        # Gửi DM cho user được trao
        try:
            dm_embed = discord.Embed(
                title="🎁 Bạn nhận được EXP Rare!",
                description=f"Admin đã trao cho bạn {amount:,} EXP Rare",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            dm_embed.add_field(
                name="⭐ EXP nhận được:",
                value=f"{amount:,} EXP Rare",
                inline=True
            )
            
            dm_embed.add_field(
                name="💎 Tổng EXP hiện có:",
                value=f"{self.get_user_exp(user.id):,} EXP Rare",
                inline=True
            )
            
            dm_embed.add_field(
                name="👨‍💼 Được trao bởi:",
                value=f"Admin {ctx.author.display_name}",
                inline=False
            )
            dm_embed.set_footer(text="Cảm ơn bạn đã tham gia!")
            
            await user.send(embed=dm_embed)
            
        except Exception as e:
            logger.warning(f"Không thể gửi DM cho user {user.id}: {e}")
    
    async def set_shop_channel(self, ctx, channel=None):
        """Cấu hình kênh shop chính thức"""
        try:
            if channel is None:
                # Nếu không có channel, sử dụng kênh hiện tại
                channel = ctx.channel
            
            # Lưu channel ID vào config
            self.shop_config["shop_channel_id"] = channel.id
            self.save_shop_config()
            
            # Tạo embed thông báo thành công
            embed = discord.Embed(
                title="✅ Đã cấu hình kênh shop thành công",
                description=f"Kênh {channel.mention} đã được đặt làm kênh shop chính thức",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🏪 Kênh shop:",
                value=f"{channel.mention} (`{channel.name}`)",
                inline=True
            )
            
            embed.add_field(
                name="🆔 Channel ID:",
                value=f"`{channel.id}`",
                inline=True
            )
            
            embed.add_field(
                name="👨‍💼 Được cấu hình bởi:",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.add_field(
                name="📋 Lưu ý:",
                value=(
                    "• User chỉ có thể mua hàng trong kênh này\n"
                    "• Lệnh `;shop` và `;buy` chỉ hoạt động ở đây\n"
                    "• Có thể thay đổi bằng `;setshop #kênh-khác`"
                ),
                inline=False
            )
            
            embed.set_footer(
                text="Shop System • Channel Configuration",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            logger.info(f"Admin {ctx.author.id} đã cấu hình kênh shop: {channel.name} ({channel.id})")
            
        except Exception as e:
            logger.error(f"Lỗi khi cấu hình kênh shop: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra khi cấu hình kênh shop: {str(e)}", mention_author=True)
    
    async def show_shop_config(self, ctx):
        """Hiển thị cấu hình shop hiện tại"""
        try:
            embed = discord.Embed(
                title="⚙️ Cấu hình Shop System",
                description="Thông tin cấu hình hiện tại của hệ thống shop",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Kênh shop
            shop_channel_id = self.shop_config.get("shop_channel_id")
            if shop_channel_id:
                shop_channel = ctx.guild.get_channel(shop_channel_id)
                if shop_channel:
                    embed.add_field(
                        name="🏪 Kênh shop chính thức:",
                        value=f"{shop_channel.mention} (`{shop_channel.name}`)",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🏪 Kênh shop chính thức:",
                        value=f"⚠️ Kênh không tồn tại (ID: `{shop_channel_id}`)",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="🏪 Kênh shop chính thức:",
                    value="❌ Chưa được cấu hình\n💡 Sử dụng `;setshop #kênh` để cấu hình",
                    inline=False
                )
            
            # Role được phép truy cập order
            allowed_roles = self.shop_config.get("allowed_roles", [])
            if allowed_roles:
                role_list = []
                for role_id in allowed_roles[:5]:  # Chỉ hiển thị 5 role đầu
                    role = ctx.guild.get_role(role_id)
                    if role:
                        role_list.append(f"• {role.mention}")
                    else:
                        role_list.append(f"• ⚠️ Role không tồn tại (ID: `{role_id}`)")
                
                if len(allowed_roles) > 5:
                    role_list.append(f"• ... và {len(allowed_roles) - 5} role khác")
                
                embed.add_field(
                    name="🎭 Role truy cập kênh order:",
                    value="\n".join(role_list) if role_list else "Không có role nào",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎭 Role truy cập kênh order:",
                    value="❌ Chưa có role nào\n💡 Sử dụng `;role add @Role` để thêm",
                    inline=False
                )
            
            # Order handlers
            order_handlers = self.shop_config.get("order_handlers", [])
            if order_handlers:
                handler_list = []
                for handler_id in order_handlers[:3]:  # Chỉ hiển thị 3 handler đầu
                    user = ctx.guild.get_member(handler_id)
                    if user:
                        handler_list.append(f"• {user.mention}")
                    else:
                        handler_list.append(f"• ⚠️ User không trong server (ID: `{handler_id}`)")
                
                if len(order_handlers) > 3:
                    handler_list.append(f"• ... và {len(order_handlers) - 3} handler khác")
                
                embed.add_field(
                    name="👥 Order handlers:",
                    value="\n".join(handler_list) if handler_list else "Không có handler nào",
                    inline=False
                )
            else:
                embed.add_field(
                    name="👥 Order handlers:",
                    value="❌ Chưa có handler nào\n💡 Sử dụng `;shop add <user_id>` để thêm",
                    inline=False
                )
            
            # Thống kê
            total_orders = len(self.orders_data)
            embed.add_field(
                name="📊 Thống kê:",
                value=f"• Tổng đơn hàng: **{total_orders}**\n• File config: `{self.shop_config_file}`",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Lệnh quản lý:",
                value=(
                    "• `;setshop #kênh` - Cấu hình kênh shop\n"
                    "• `;role add @Role` - Thêm role truy cập\n"
                    "• `;shop add <user_id>` - Thêm order handler\n"
                    "• `;checkshoppermissions` - Kiểm tra quyền bot"
                ),
                inline=False
            )
            
            embed.set_footer(
                text="Shop System Configuration",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.reply(embed=embed, mention_author=True)
            
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị config shop: {e}")
            await ctx.reply(f"❌ Có lỗi xảy ra: {str(e)}", mention_author=True)
