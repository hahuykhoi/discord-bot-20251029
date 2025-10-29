#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetKey Checker Tool - Standalone Key Validation
Công cụ kiểm tra key độc lập, không liên quan đến Discord bot
"""

import requests
import json
import hashlib
import time
from datetime import datetime

class GetKeyChecker:
    def __init__(self):
        # Cấu hình API
        self.API_BASE = "https://mttool.x10.mx"
        self.ORIGIN = "mtoolvip"
        self.USER_AGENT = "sieunhansiplord"
    
    def get_device_id(self, user_input):
        """Tạo device ID từ input của user"""
        hash_object = hashlib.sha256(str(user_input).encode())
        return int(hash_object.hexdigest(), 16) % (10**18)
    
    def send_ckey_request(self, key, device_id):
        """Gửi request check key"""
        try:
            url = f"{self.API_BASE}/ckey"
            
            payload = {
                'key': key,
                'device_id': str(device_id),
                'origin': self.ORIGIN
            }
            
            headers = {
                'User-Agent': self.USER_AGENT,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return result
                except json.JSONDecodeError:
                    return {'status': 'error', 'message': 'Invalid JSON response'}
            else:
                return {'status': 'error', 'message': f'HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            return {'status': 'error', 'message': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': f'Request error: {str(e)}'}
    
    def format_time_remaining(self, seconds):
        """Format thời gian còn lại"""
        if seconds <= 0:
            return "Đã hết hạn"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def check_key(self, key, device_id=None):
        """Check key và hiển thị kết quả"""
        print(f"\n🔍 Đang kiểm tra key: {key}")
        print("=" * 50)
        
        # Tạo device ID nếu không có
        if device_id is None:
            device_id = self.get_device_id(key)
        
        print(f"📱 Device ID: {device_id}")
        print(f"⏰ Thời gian check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🔄 Đang gửi request...")
        
        # Gửi request
        result = self.send_ckey_request(key, device_id)
        
        print("\n📊 KẾT QUẢ:")
        print("=" * 30)
        
        if result['status'] == 'success':
            print("✅ KEY HỢP LỆ!")
            print(f"🔑 Key: {key}")
            
            if 'expires_in_seconds' in result:
                expires_sec = result['expires_in_seconds']
                time_remaining = self.format_time_remaining(expires_sec)
                print(f"⏰ Thời hạn còn lại: {time_remaining}")
            
            if 'message' in result:
                print(f"💬 Thông báo: {result['message']}")
            
            print("\n🎉 Key này có thể sử dụng để nhận 500,000 xu trong Discord bot!")
            
        elif result['status'] == 'error':
            print("❌ KEY KHÔNG HỢP LỆ!")
            print(f"🔑 Key: {key}")
            
            if 'message' in result:
                print(f"💬 Lỗi: {result['message']}")
            
            print("\n💡 Gợi ý:")
            print("• Kiểm tra lại key có đúng không")
            print("• Key có thể đã hết hạn")
            print("• Thử tạo key mới bằng ;getkey")
        
        else:
            print("⚠️ KHÔNG XÁC ĐỊNH!")
            print(f"🔑 Key: {key}")
            print(f"📄 Response: {result}")
        
        print("\n" + "=" * 50)

def main():
    """Main function"""
    print("🔑 GETKEY CHECKER TOOL")
    print("=" * 50)
    print("Công cụ kiểm tra key độc lập")
    print("Không liên quan đến Discord bot")
    print("=" * 50)
    
    checker = GetKeyChecker()
    
    while True:
        print("\n📝 MENU:")
        print("1. Check key")
        print("2. Check key với device ID tùy chỉnh")
        print("3. Thoát")
        
        choice = input("\n👉 Chọn (1-3): ").strip()
        
        if choice == '1':
            key = input("\n🔑 Nhập key cần check: ").strip()
            if key:
                checker.check_key(key)
            else:
                print("❌ Key không được để trống!")
        
        elif choice == '2':
            key = input("\n🔑 Nhập key cần check: ").strip()
            device_input = input("📱 Nhập device ID (hoặc text để tạo): ").strip()
            
            if key and device_input:
                try:
                    # Thử convert sang int
                    device_id = int(device_input)
                except ValueError:
                    # Nếu không phải số, tạo device ID từ text
                    device_id = checker.get_device_id(device_input)
                
                checker.check_key(key, device_id)
            else:
                print("❌ Key và device ID không được để trống!")
        
        elif choice == '3':
            print("\n👋 Tạm biệt!")
            break
        
        else:
            print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng chương trình!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
