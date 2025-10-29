"""
Script kiểm tra hệ thống bot
Kiểm tra tất cả components đã sẵn sàng
"""
import os
import json
import sys
from datetime import datetime

def check_file_exists(filename, required=True):
    """Kiểm tra file có tồn tại không"""
    exists = os.path.exists(filename)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {filename:30s} {'EXISTS' if exists else 'MISSING'}")
    return exists

def check_gitignore():
    """Kiểm tra .gitignore"""
    print("\n📋 Kiểm tra .gitignore:")
    
    if not os.path.exists('.gitignore'):
        print("❌ .gitignore không tồn tại!")
        return False
    
    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_patterns = [
        'shared_wallet.json',
        'taixiu_data.json',
        'data_backups/',
        '*.json'
    ]
    
    all_good = True
    for pattern in required_patterns:
        if pattern in content:
            print(f"✅ {pattern:25s} PROTECTED")
        else:
            print(f"❌ {pattern:25s} NOT PROTECTED")
            all_good = False
    
    return all_good

def check_data_files():
    """Kiểm tra data files"""
    print("\n📋 Kiểm tra data files:")
    
    data_files = [
        'shared_wallet.json',
        'taixiu_data.json',
        'flip_coin_data.json',
        'rps_data.json',
        'slot_data.json',
        'maintenance_mode.json'
    ]
    
    existing_files = []
    for file in data_files:
        if check_file_exists(file, required=False):
            existing_files.append(file)
    
    print(f"\n📊 Có {len(existing_files)}/{len(data_files)} data files")
    return existing_files

def check_scripts():
    """Kiểm tra scripts"""
    print("\n📋 Kiểm tra backup/restore scripts:")
    
    scripts = [
        ('backup_data.py', True),
        ('restore_data.py', True),
        ('quick_update.sh', False),
        ('test_backup.py', False)
    ]
    
    all_good = True
    for script, required in scripts:
        if not check_file_exists(script, required):
            if required:
                all_good = False
    
    return all_good

def check_bot_files():
    """Kiểm tra bot files"""
    print("\n📋 Kiểm tra bot files:")
    
    bot_files = [
        ('bot_refactored.py', True),
        ('shared_wallet.py', True),
        ('commands/maintenance_commands.py', True),
        ('requirements.txt', True)
    ]
    
    all_good = True
    for file, required in bot_files:
        if not check_file_exists(file, required):
            if required:
                all_good = False
    
    return all_good

def check_maintenance_system():
    """Kiểm tra maintenance system"""
    print("\n📋 Kiểm tra maintenance system:")
    
    try:
        # Import maintenance commands
        sys.path.append('commands')
        from maintenance_commands import MaintenanceCommands
        print("✅ MaintenanceCommands        IMPORTABLE")
        
        # Kiểm tra maintenance_mode.json
        if os.path.exists('maintenance_mode.json'):
            with open('maintenance_mode.json', 'r') as f:
                data = json.load(f)
            
            required_keys = ['is_maintenance', 'closed_at', 'closed_by', 'reason']
            all_keys = all(key in data for key in required_keys)
            
            print(f"✅ maintenance_mode.json      {'VALID' if all_keys else 'INVALID'}")
            print(f"   Status: {'MAINTENANCE' if data.get('is_maintenance') else 'NORMAL'}")
        else:
            print("⚠️  maintenance_mode.json      MISSING")
        
        return True
        
    except Exception as e:
        print(f"❌ MaintenanceCommands        ERROR: {e}")
        return False

def run_system_check():
    """Chạy kiểm tra toàn bộ hệ thống"""
    print("=" * 60)
    print("🔍 SYSTEM CHECK - Discord Bot")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    checks = []
    
    # Kiểm tra các components
    checks.append(("GitIgnore", check_gitignore()))
    checks.append(("Scripts", check_scripts()))
    checks.append(("Bot Files", check_bot_files()))
    checks.append(("Maintenance", check_maintenance_system()))
    
    # Kiểm tra data files (không bắt buộc)
    existing_data = check_data_files()
    
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ KIỂM TRA")
    print("=" * 60)
    
    passed = 0
    total = len(checks)
    
    for name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:15s} {status}")
        if result:
            passed += 1
    
    print(f"\nData Files:     📁 {len(existing_data)} files found")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("🎉 TẤT CẢ KIỂM TRA THÀNH CÔNG!")
        print("✅ Hệ thống sẵn sàng hoạt động")
        
        print("\n💡 Tiếp theo:")
        print("  1. Test backup: python test_backup.py")
        print("  2. Khởi động bot: python bot_refactored.py")
        print("  3. Test maintenance: ;close và ;open")
        
    else:
        print("❌ CÓ LỖI CẦN SỬA!")
        print(f"📊 {passed}/{total} kiểm tra thành công")
        
        print("\n🔧 Cần sửa:")
        for name, result in checks:
            if not result:
                print(f"  - {name}")
    
    print("\n" + "=" * 60)
    
    return passed == total

if __name__ == '__main__':
    success = run_system_check()
    sys.exit(0 if success else 1)
