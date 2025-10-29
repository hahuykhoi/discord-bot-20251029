#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để sửa nút "Tất cả lệnh" thành hiển thị text thay vì buttons
"""

import re

def fix_all_commands_button():
    """Sửa nút all_commands_button để hiển thị text thay vì buttons"""
    
    file_path = "commands/game_menu_commands.py"
    
    try:
        # Đọc file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Import statement cần thêm
        import_statement = "from .all_commands_display import create_all_commands_embed"
        
        # Thêm import nếu chưa có
        if import_statement not in content:
            # Tìm vị trí import cuối cùng
            import_pattern = r'(from datetime import datetime\n)'
            content = re.sub(import_pattern, r'\1' + import_statement + '\n', content)
        
        # Pattern để tìm all_commands_button method
        pattern = r'(@discord\.ui\.button\(label=\'📋 Tất cả lệnh\'.*?\n    async def all_commands_button\(self, interaction: discord\.Interaction, button: discord\.ui\.Button\):\n        """Button hiển thị tất cả lệnh của bot \(chỉ riêng người dùng\)"""\n        try:\n            embed = discord\.Embed\(\n                title="📋 Tất cả lệnh của Bot",\n                description="Menu tổng hợp tất cả lệnh có sẵn \(chỉ bạn thấy được\)",\n                color=discord\.Color\.blue\(\),\n                timestamp=datetime\.now\(\)\n            \)\n            \n            embed\.set_footer\(\n                text=f"Yêu cầu bởi \{interaction\.user\.display_name\} • Nhấn button để xem chi tiết",\n                icon_url=interaction\.user\.display_avatar\.url\n            \)\n            \n            # Tạo view với các buttons cho từng danh mục lệnh\n            all_commands_view = AllCommandsView\(self\.bot_instance, interaction\.user\)\n            \n            await interaction\.response\.send_message\(embed=embed, view=all_commands_view, ephemeral=True\)\n            \n        except Exception as e:\n            logger\.error\(f"Lỗi trong all_commands_button: \{e\}"\)\n            try:\n                await interaction\.response\.send_message\(\n                    "❌ Có lỗi xảy ra khi hiển thị menu lệnh!",\n                    ephemeral=True\n                \)\n            except:\n                pass)'
        
        # Replacement text
        replacement = '''@discord.ui.button(label='📋 Tất cả lệnh', style=discord.ButtonStyle.success, custom_id='all_commands')
    async def all_commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button hiển thị tất cả lệnh của bot dạng text (chỉ riêng người dùng)"""
        try:
            # Tạo embed hiển thị tất cả lệnh
            embed = create_all_commands_embed(interaction.user)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Lỗi trong all_commands_button: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Có lỗi xảy ra khi hiển thị danh sách lệnh!",
                    ephemeral=True
                )
            except:
                pass'''
        
        # Thực hiện thay thế (sử dụng pattern đơn giản hơn)
        # Tìm và thay thế method all_commands_button
        start_marker = "@discord.ui.button(label='📋 Tất cả lệnh'"
        end_marker = "                pass"
        
        start_idx = content.find(start_marker)
        if start_idx != -1:
            # Tìm end của method
            temp_content = content[start_idx:]
            lines = temp_content.split('\n')
            
            method_lines = []
            indent_level = None
            found_method_start = False
            
            for i, line in enumerate(lines):
                if 'async def all_commands_button' in line:
                    found_method_start = True
                    indent_level = len(line) - len(line.lstrip())
                
                if found_method_start:
                    method_lines.append(line)
                    
                    # Kiểm tra xem có phải là kết thúc method không
                    if i > 0 and line.strip() == 'pass' and 'except:' in lines[i-1]:
                        break
            
            if method_lines:
                old_method = '\n'.join(method_lines)
                content = content.replace(old_method, replacement)
        
        # Xóa AllCommandsView class (không cần nữa)
        # Tìm và xóa class AllCommandsView
        class_pattern = r'\nclass AllCommandsView\(discord\.ui\.View\):.*?(?=\nclass|\Z)'
        content = re.sub(class_pattern, '', content, flags=re.DOTALL)
        
        # Ghi lại file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Đã sửa thành công nút 'Tất cả lệnh'")
        print("📋 Nút giờ sẽ hiển thị tất cả lệnh dạng text thay vì buttons")
        
    except Exception as e:
        print(f"❌ Lỗi khi sửa file: {e}")

if __name__ == "__main__":
    fix_all_commands_button()
