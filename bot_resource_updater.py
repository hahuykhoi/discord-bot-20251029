#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tự động update và quản lý bot resource
"""

import os
import sys
import shutil
from datetime import datetime

# Import class từ file chính
sys.path.insert(0, os.path.dirname(__file__))
from create_bot_resource import BotResourceManager

def print_header():
    """In header"""
    print("🚀 BOT RESOURCE UPDATER")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

def check_files():
    """Kiểm tra files cần thiết"""
    print("\n🔍 KIỂM TRA FILES...")
    
    resource_exists = os.path.exists("bot_resource.json")
    bot_files_exists = os.path.exists("bot_files")
    
    print(f"   📄 bot_resource.json: {'✅ Có' if resource_exists else '❌ Không có'}")
    print(f"   📁 bot_files/: {'✅ Có' if bot_files_exists else '❌ Không có'}")
    
    return resource_exists, bot_files_exists

def auto_setup():
    """Tự động setup resource file"""
    print("\n🔄 AUTO SETUP...")
    
    manager = BotResourceManager()
    resource_exists, bot_files_exists = check_files()
    
    if not resource_exists and not bot_files_exists:
        print("❌ Không có resource file và bot_files folder!")
        print("💡 Cần có ít nhất 1 trong 2 để bắt đầu")
        return False
    
    if not resource_exists and bot_files_exists:
        print("📦 Tạo resource file từ bot_files/...")
        return manager.create_resource_file()
    
    if resource_exists and not bot_files_exists:
        print("📂 Extract bot_files/ từ resource file...")
        return manager.extract_resource_file(force=True)
    
    if resource_exists and bot_files_exists:
        print("🔄 Cả 2 đều có, update resource file...")
        return manager.update_resource_file()
    
    return False

def create_deployment_package():
    """Tạo package để deploy"""
    print("\n📦 TẠO DEPLOYMENT PACKAGE...")
    
    # Kiểm tra files cần thiết
    required_files = ["bot_refactored.py", "bot_resource.json"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Thiếu files: {', '.join(missing_files)}")
        return False
    
    # Tạo thư mục deploy
    deploy_folder = f"bot_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(deploy_folder, exist_ok=True)
    
    # Copy files cần thiết
    files_to_copy = [
        "bot_refactored.py",
        "bot_resource.json", 
        "create_bot_resource.py",
        "run_bot.bat",
        "run_bot.py"
    ]
    
    copied_files = []
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, deploy_folder)
            copied_files.append(file)
            print(f"   ✅ {file}")
    
    # Tạo script setup cho deploy
    setup_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script cho bot deployment
"""

import os
import sys
from create_bot_resource import BotResourceManager

def main():
    print("🚀 BOT DEPLOYMENT SETUP")
    print("=" * 40)
    
    # Kiểm tra resource file
    if not os.path.exists("bot_resource.json"):
        print("❌ Không tìm thấy bot_resource.json!")
        return
    
    # Extract bot_files
    manager = BotResourceManager()
    print("📂 Đang extract bot_files...")
    
    if manager.extract_resource_file(force=True):
        print("\\n✅ SETUP THÀNH CÔNG!")
        print("🚀 Có thể chạy bot:")
        print("   • python bot_refactored.py")
        print("   • run_bot.bat")
    else:
        print("\\n❌ SETUP THẤT BẠI!")

if __name__ == "__main__":
    main()
'''
    
    with open(os.path.join(deploy_folder, "setup_deployment.py"), 'w', encoding='utf-8') as f:
        f.write(setup_script)
    
    # Tạo README cho deployment
    readme_content = f'''# Bot Deployment Package

## 📋 Nội dung package
- bot_refactored.py - File main chạy bot
- bot_resource.json - Resource chứa tất cả bot_files
- create_bot_resource.py - Tool quản lý resource
- setup_deployment.py - Script setup tự động
- run_bot.bat / run_bot.py - Scripts chạy bot

## 🚀 Cách deploy

### Bước 1: Setup
```bash
python setup_deployment.py
```

### Bước 2: Chạy bot
```bash
python bot_refactored.py
```

## 📊 Thông tin
- Tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Tổng files trong resource: 233
- Kích thước resource: ~28MB

## 💡 Lưu ý
- Resource file chứa tất cả bot_files được nén
- Setup sẽ tự động extract thành folder bot_files/
- Có thể chạy ngay sau khi setup
'''
    
    with open(os.path.join(deploy_folder, "README.md"), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n✅ Tạo deployment package: {deploy_folder}")
    print(f"📊 Files: {len(copied_files) + 2}")
    print(f"📁 Kích thước: {sum(os.path.getsize(os.path.join(deploy_folder, f)) for f in os.listdir(deploy_folder)):,} bytes")
    
    return True

def main():
    """Main function"""
    print_header()
    
    while True:
        print(f"\n📋 MENU:")
        print("1. 🔍 Kiểm tra trạng thái")
        print("2. 🔄 Auto setup (tạo/extract/update)")
        print("3. 📦 Tạo resource từ bot_files/")
        print("4. 📂 Extract resource thành bot_files/")
        print("5. 🔄 Update resource file")
        print("6. 📊 Xem thông tin resource")
        print("7. 📦 Tạo deployment package")
        print("8. 🚀 Chạy bot")
        print("9. ❌ Thoát")
        
        choice = input("\nChọn (1-9): ").strip()
        
        if choice == "1":
            print("\n" + "="*50)
            check_files()
            
        elif choice == "2":
            print("\n" + "="*50)
            if auto_setup():
                print("✅ Auto setup thành công!")
            else:
                print("❌ Auto setup thất bại!")
                
        elif choice == "3":
            print("\n" + "="*50)
            manager = BotResourceManager()
            manager.create_resource_file()
            
        elif choice == "4":
            print("\n" + "="*50)
            manager = BotResourceManager()
            manager.extract_resource_file()
            
        elif choice == "5":
            print("\n" + "="*50)
            manager = BotResourceManager()
            manager.update_resource_file()
            
        elif choice == "6":
            print("\n" + "="*50)
            manager = BotResourceManager()
            manager.info()
            
        elif choice == "7":
            print("\n" + "="*50)
            if create_deployment_package():
                print("✅ Tạo deployment package thành công!")
            else:
                print("❌ Tạo deployment package thất bại!")
                
        elif choice == "8":
            print("\n" + "="*50)
            if os.path.exists("bot_refactored.py"):
                print("🚀 Chạy bot...")
                os.system("python bot_refactored.py")
            else:
                print("❌ Không tìm thấy bot_refactored.py!")
                
        elif choice == "9":
            print("\n👋 Tạm biệt!")
            break
            
        else:
            print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()
