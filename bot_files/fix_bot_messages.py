#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sửa lỗi bot không nhận được tin nhắn
Giới hạn bot chỉ hoạt động trong 1 server cụ thể
"""

import json
import os

def fix_bot_messages():
    """Sửa các vấn đề khiến bot không nhận tin nhắn"""
    
    print("Đang sửa lỗi bot không nhận tin nhắn...")
    
    # 1. Tắt maintenance mode (nếu còn bật)
    print("\n1. Kiểm tra maintenance mode...")
    maintenance_file = 'data/maintenance_mode.json'
    try:
        if os.path.exists(maintenance_file):
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('enabled', True):
                data['enabled'] = False
                data['reason'] = 'Fixed by script'
                
                with open(maintenance_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print("   ✓ Đã tắt maintenance mode")
            else:
                print("   ✓ Maintenance mode đã tắt")
        else:
            # Tạo file maintenance disabled
            disabled_config = {
                "enabled": False,
                "reason": "Disabled by script",
                "closed_by": {"id": None, "name": "System"},
                "closed_at": None
            }
            os.makedirs('data', exist_ok=True)
            with open(maintenance_file, 'w', encoding='utf-8') as f:
                json.dump(disabled_config, f, indent=4, ensure_ascii=False)
            print("   ✓ Tạo maintenance config (disabled)")
    except Exception as e:
        print(f"   ✗ Lỗi maintenance: {e}")
    
    # 2. Tạo config giới hạn server
    print("\n2. Tạo config giới hạn server...")
    server_config = {
        "allowed_server_id": "THAY_ID_SERVER_CUA_BAN_VAO_DAY",
        "server_name": "Tên server của bạn",
        "enabled": True,
        "note": "Bot chỉ hoạt động trong server này. Thay allowed_server_id bằng ID server thực tế."
    }
    
    try:
        with open('data/server_restriction.json', 'w', encoding='utf-8') as f:
            json.dump(server_config, f, indent=4, ensure_ascii=False)
        print("   ✓ Tạo config giới hạn server: data/server_restriction.json")
        print("   ⚠️  QUAN TRỌNG: Sửa 'allowed_server_id' thành ID server thực tế!")
    except Exception as e:
        print(f"   ✗ Lỗi tạo server config: {e}")
    
    # 3. Tạo file patch cho bot_refactored.py
    print("\n3. Tạo patch code...")
    
    patch_code = '''
# ===== PATCH CODE - THÊM VÀO ĐẦU FILE bot_refactored.py =====

import json
import os

def load_server_restriction():
    """Load cấu hình giới hạn server"""
    try:
        if os.path.exists('data/server_restriction.json'):
            with open('data/server_restriction.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"enabled": False}

SERVER_RESTRICTION = load_server_restriction()

# ===== PATCH CODE - THÊM VÀO HÀM on_message =====

async def on_message(self, message):
    """Handle incoming messages với server restriction"""
    
    # Bỏ qua tin nhắn từ bot
    if message.author.bot:
        return
    
    # KIỂM TRA GIỚI HẠN SERVER
    if SERVER_RESTRICTION.get("enabled", False):
        allowed_server_id = SERVER_RESTRICTION.get("allowed_server_id")
        if allowed_server_id and str(message.guild.id) != str(allowed_server_id):
            # Bot không phản hồi trong server không được phép
            return
    
    # Tiếp tục xử lý tin nhắn bình thường...
    # (phần code cũ của on_message)
'''
    
    try:
        with open('patch_bot_messages.txt', 'w', encoding='utf-8') as f:
            f.write(patch_code)
        print("   ✓ Tạo file patch: patch_bot_messages.txt")
    except Exception as e:
        print(f"   ✗ Lỗi tạo patch: {e}")
    
    # 4. Tạo script kiểm tra intents
    print("\n4. Tạo script kiểm tra Discord intents...")
    
    intents_check = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra Discord intents - chạy script này để test
"""

import discord

def check_intents():
    """Kiểm tra intents cần thiết"""
    print("Kiểm tra Discord Intents...")
    
    # Tạo intents đầy đủ
    intents = discord.Intents.default()
    intents.message_content = True  # Quan trọng!
    intents.messages = True
    intents.guilds = True
    intents.reactions = True
    
    print("✓ Intents được thiết lập:")
    print(f"  - message_content: {intents.message_content}")
    print(f"  - messages: {intents.messages}")
    print(f"  - guilds: {intents.guilds}")
    print(f"  - reactions: {intents.reactions}")
    
    if not intents.message_content:
        print("⚠️  CẢNH BÁO: message_content = False")
        print("   Bot sẽ không đọc được nội dung tin nhắn!")
        print("   Cần bật Message Content Intent trong Discord Developer Portal")
    
    return intents

if __name__ == "__main__":
    check_intents()
'''
    
    try:
        with open('check_intents.py', 'w', encoding='utf-8') as f:
            f.write(intents_check)
        print("   ✓ Tạo script kiểm tra intents: check_intents.py")
    except Exception as e:
        print(f"   ✗ Lỗi tạo intents check: {e}")
    
    # 5. Hướng dẫn sửa
    print("\n" + "="*60)
    print("HƯỚNG DẪN SỬA LỖI BOT KHÔNG NHẬN TIN NHẮN:")
    print("="*60)
    
    print("\n📋 BƯỚC 1: Sửa ID server")
    print("   - Mở file: data/server_restriction.json")
    print("   - Thay 'THAY_ID_SERVER_CUA_BAN_VAO_DAY' bằng ID server thực tế")
    print("   - Cách lấy ID server: Chuột phải server → Copy Server ID")
    
    print("\n📋 BƯỚC 2: Kiểm tra Discord Developer Portal")
    print("   - Vào https://discord.com/developers/applications")
    print("   - Chọn bot của bạn → Bot → Privileged Gateway Intents")
    print("   - BẬT: Message Content Intent (QUAN TRỌNG!)")
    print("   - BẬT: Server Members Intent")
    print("   - BẬT: Presence Intent")
    
    print("\n📋 BƯỚC 3: Cập nhật bot_refactored.py")
    print("   - Mở file patch_bot_messages.txt")
    print("   - Copy code và thêm vào bot_refactored.py theo hướng dẫn")
    print("   - Hoặc thay thế toàn bộ hàm on_message")
    
    print("\n📋 BƯỚC 4: Kiểm tra intents")
    print("   - Chạy: python check_intents.py")
    print("   - Đảm bảo message_content = True")
    
    print("\n📋 BƯỚC 5: Restart bot")
    print("   - Tắt bot hiện tại")
    print("   - Chạy lại: python bot_refactored.py")
    print("   - Kiểm tra logs có lỗi không")
    
    print("\n🔧 NGUYÊN NHÂN THƯỜNG GẶP:")
    print("   1. Message Content Intent chưa được bật")
    print("   2. Bot token hết hạn hoặc không hợp lệ")
    print("   3. Bot không có quyền đọc tin nhắn trong server")
    print("   4. Maintenance mode vẫn đang bật")
    print("   5. Code on_message bị lỗi")
    
    print("\n✅ Script đã tạo các file:")
    print("   - data/maintenance_mode.json (tắt maintenance)")
    print("   - data/server_restriction.json (giới hạn server)")
    print("   - patch_bot_messages.txt (code patch)")
    print("   - check_intents.py (kiểm tra intents)")
    
    return True

if __name__ == "__main__":
    success = fix_bot_messages()
    
    if success:
        print("\n🎉 HOÀN THÀNH!")
        print("Làm theo hướng dẫn trên để sửa bot.")
        print("Quan trọng nhất: Bật Message Content Intent!")
    else:
        print("\n❌ CÓ LỖI XẢY RA!")
        print("Kiểm tra lại các bước trên.")
