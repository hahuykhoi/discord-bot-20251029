"""
Script restore dữ liệu game và user từ backup
Chạy sau khi update code: python restore_data.py <backup_file.zip>
"""
import os
import shutil
import json
import zipfile
import sys
from datetime import datetime

def list_backups():
    """Liệt kê các backup có sẵn"""
    backup_dir = 'data_backups'
    
    if not os.path.exists(backup_dir):
        print("❌ Chưa có backup nào!")
        return []
    
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
    
    if not backups:
        print("❌ Chưa có backup nào!")
        return []
    
    backups.sort(reverse=True)  # Mới nhất trước
    return backups

def restore_backup(backup_file):
    """Restore dữ liệu từ backup"""
    backup_dir = 'data_backups'
    backup_path = os.path.join(backup_dir, backup_file)
    
    if not os.path.exists(backup_path):
        print(f"❌ Không tìm thấy file backup: {backup_path}")
        return False
    
    print(f"\n📦 Đang restore từ: {backup_file}")
    print("=" * 60)
    
    # Tạo thư mục temp để extract
    temp_dir = 'temp_restore'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Extract zip
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Copy files về root
        restored_files = []
        failed_files = []
        
        for file in os.listdir(temp_dir):
            source = os.path.join(temp_dir, file)
            dest = file
            
            try:
                shutil.copy2(source, dest)
                restored_files.append(file)
                
                size = os.path.getsize(dest)
                print(f"✅ {file:30s} ({size:,} bytes)")
            except Exception as e:
                failed_files.append((file, str(e)))
                print(f"❌ {file:30s} - Lỗi: {e}")
        
        # Xóa temp dir
        shutil.rmtree(temp_dir)
        
        print("=" * 60)
        print(f"\n📊 Thống kê:")
        print(f"  ✅ Restored: {len(restored_files)} files")
        print(f"  ❌ Failed:   {len(failed_files)} files")
        
        if failed_files:
            print(f"\n❌ Các file thất bại:")
            for file, error in failed_files:
                print(f"  - {file}: {error}")
        
        print(f"\n🎉 Restore hoàn tất!")
        print(f"\n💡 Khởi động lại bot để áp dụng dữ liệu mới")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Lỗi khi restore: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

def interactive_restore():
    """Restore tương tác - chọn backup từ danh sách"""
    backups = list_backups()
    
    if not backups:
        return
    
    print("\n📦 Các backup có sẵn:")
    print("=" * 60)
    
    for i, backup in enumerate(backups, 1):
        backup_path = os.path.join('data_backups', backup)
        size = os.path.getsize(backup_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(backup_path))
        
        print(f"{i}. {backup}")
        print(f"   📅 {mtime.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   📦 {size:,} bytes")
        print()
    
    print("=" * 60)
    
    try:
        choice = input(f"\n🔢 Chọn backup để restore (1-{len(backups)}) hoặc 'q' để thoát: ")
        
        if choice.lower() == 'q':
            print("❌ Đã hủy restore")
            return
        
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(backups):
            selected_backup = backups[choice_num - 1]
            
            confirm = input(f"\n⚠️  Xác nhận restore từ '{selected_backup}'? (y/n): ")
            
            if confirm.lower() == 'y':
                restore_backup(selected_backup)
            else:
                print("❌ Đã hủy restore")
        else:
            print("❌ Lựa chọn không hợp lệ!")
            
    except ValueError:
        print("❌ Vui lòng nhập số!")
    except KeyboardInterrupt:
        print("\n❌ Đã hủy restore")

if __name__ == '__main__':
    print("=" * 60)
    print("🔄 RESTORE SYSTEM - Discord Bot Data")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Restore từ file cụ thể
        backup_file = sys.argv[1]
        
        # Nếu không có .zip thì thêm vào
        if not backup_file.endswith('.zip'):
            backup_file += '.zip'
        
        restore_backup(backup_file)
    else:
        # Interactive mode
        interactive_restore()
    
    print("\n" + "=" * 60)
