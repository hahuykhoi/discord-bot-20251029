# -*- coding: utf-8 -*-
"""
Data Migration Script - Tự động di chuyển dữ liệu vào folder data/
Chạy script này để tổ chức lại cấu trúc dữ liệu
"""
import os
import shutil
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data_to_folder():
    """Di chuyển tất cả dữ liệu vào folder data/"""
    
    # Tạo folder data
    data_folder = 'data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        logger.info(f"Đã tạo folder {data_folder}")
    
    # Danh sách files cần migrate
    files_to_migrate = [
        'shared_wallet.json',
        'taixiu_data.json', 
        'api-gemini.json',
        'config.json',
        'admin.json',
        'warnings.json',
        'priority.json',
        'supreme_admin.json',
        'auto_delete_config.json',
        'fire_delete_config.json',
        'afk_data.json',
        'banned_users.json'
    ]
    
    # Tạo backup trước khi migrate
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"migration_backup_{timestamp}"
    
    if not os.path.exists('data_backups'):
        os.makedirs('data_backups')
    
    backup_path = os.path.join('data_backups', backup_folder)
    os.makedirs(backup_path, exist_ok=True)
    
    migrated_files = []
    skipped_files = []
    
    for file in files_to_migrate:
        # Kiểm tra file tồn tại ở root
        if os.path.exists(file):
            data_file_path = os.path.join(data_folder, file)
            
            try:
                # Backup file gốc
                shutil.copy2(file, backup_path)
                logger.info(f"Đã backup {file}")
                
                # Di chuyển vào data folder (chỉ nếu chưa có)
                if not os.path.exists(data_file_path):
                    shutil.move(file, data_file_path)
                    migrated_files.append(file)
                    logger.info(f"Đã migrate {file} -> {data_folder}/{file}")
                else:
                    # Nếu đã có trong data, xóa file gốc
                    os.remove(file)
                    skipped_files.append(file)
                    logger.info(f"Đã xóa {file} (đã có trong data/)")
                    
            except Exception as e:
                logger.error(f"Lỗi migrate {file}: {e}")
        else:
            # Kiểm tra xem đã có trong data folder chưa
            data_file_path = os.path.join(data_folder, file)
            if os.path.exists(data_file_path):
                skipped_files.append(file)
    
    # Tạo migration report
    report = {
        'timestamp': datetime.now().isoformat(),
        'migrated_files': migrated_files,
        'skipped_files': skipped_files,
        'backup_location': backup_path if migrated_files else None,
        'total_migrated': len(migrated_files),
        'total_skipped': len(skipped_files)
    }
    
    report_file = os.path.join(data_folder, 'migration_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    # In kết quả
    print("\n" + "="*50)
    print("📁 DATA MIGRATION HOÀN TẤT")
    print("="*50)
    
    if migrated_files:
        print(f"✅ Đã migrate {len(migrated_files)} files:")
        for file in migrated_files:
            print(f"   • {file} → data/{file}")
    
    if skipped_files:
        print(f"⏭️ Đã bỏ qua {len(skipped_files)} files (đã có trong data/):")
        for file in skipped_files:
            print(f"   • {file}")
    
    if migrated_files:
        print(f"\n📦 Backup được lưu tại: {backup_path}")
    
    print(f"\n📋 Migration report: {report_file}")
    print("\n🎉 Tất cả dữ liệu giờ được quản lý trong folder data/")
    print("💡 Sử dụng ;backup migrate để migrate từ bot")
    
    return report

def check_data_structure():
    """Kiểm tra cấu trúc dữ liệu hiện tại"""
    
    print("\n" + "="*50)
    print("🔍 KIỂM TRA CẤU TRÚC DỮ LIỆU")
    print("="*50)
    
    # Files cần kiểm tra
    files_to_check = [
        'shared_wallet.json',
        'taixiu_data.json', 
        'api-gemini.json',
        'config.json',
        'admin.json',
        'warnings.json',
        'priority.json',
        'supreme_admin.json',
        'auto_delete_config.json',
        'fire_delete_config.json',
        'afk_data.json',
        'banned_users.json'
    ]
    
    root_files = []
    data_files = []
    missing_files = []
    
    for file in files_to_check:
        if os.path.exists(file):
            root_files.append(file)
        elif os.path.exists(f"data/{file}"):
            data_files.append(file)
        else:
            missing_files.append(file)
    
    print(f"📁 Files ở root: {len(root_files)}")
    for file in root_files:
        print(f"   • {file}")
    
    print(f"\n📂 Files trong data/: {len(data_files)}")
    for file in data_files:
        print(f"   • data/{file}")
    
    if missing_files:
        print(f"\n❓ Files chưa tồn tại: {len(missing_files)}")
        for file in missing_files:
            print(f"   • {file}")
    
    # Đề xuất hành động
    if root_files:
        print(f"\n💡 Đề xuất: Chạy migration để di chuyển {len(root_files)} files vào data/")
        return False
    elif data_files:
        print(f"\n✅ Cấu trúc dữ liệu đã được tổ chức tốt!")
        return True
    else:
        print(f"\n⚠️ Chưa có dữ liệu nào. Bot sẽ tạo files mới trong data/")
        return True

if __name__ == "__main__":
    print("🚀 Data Migration Tool")
    print("Công cụ tổ chức lại cấu trúc dữ liệu Discord Bot")
    
    # Kiểm tra cấu trúc hiện tại
    is_organized = check_data_structure()
    
    if not is_organized:
        print("\n" + "="*50)
        response = input("Bạn có muốn migrate dữ liệu vào data/ không? (y/n): ").lower().strip()
        
        if response in ['y', 'yes', 'có']:
            migrate_data_to_folder()
        else:
            print("❌ Hủy migration. Dữ liệu vẫn ở vị trí cũ.")
    
    print("\n🏁 Hoàn tất!")
