#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo file resource chứa tất cả nội dung bot_files
Có thể extract lại thành folder bot_files nếu cần
"""

import os
import json
import base64
import zipfile
import shutil
from datetime import datetime
import tempfile

class BotResourceManager:
    """Quản lý resource file cho bot"""
    
    def __init__(self):
        self.resource_file = "bot_resource.json"
        self.bot_files_folder = "bot_files"
        
    def create_resource_file(self):
        """Tạo file resource từ folder bot_files"""
        print("🔄 Tạo bot resource file...")
        
        if not os.path.exists(self.bot_files_folder):
            print(f"❌ Không tìm thấy folder: {self.bot_files_folder}")
            return False
        
        # Tạo resource data
        resource_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "description": "Bot files resource package",
                "total_files": 0,
                "total_size": 0
            },
            "files": {}
        }
        
        total_files = 0
        total_size = 0
        
        # Duyệt qua tất cả files trong bot_files
        for root, dirs, files in os.walk(self.bot_files_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.bot_files_folder)
                
                try:
                    # Đọc file
                    if self._is_binary_file(file_path):
                        # File binary - encode base64
                        with open(file_path, 'rb') as f:
                            content = base64.b64encode(f.read()).decode('utf-8')
                        file_type = "binary"
                    else:
                        # File text - đọc trực tiếp
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        file_type = "text"
                    
                    # Thông tin file
                    file_info = {
                        "type": file_type,
                        "content": content,
                        "size": len(content),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    
                    resource_data["files"][relative_path] = file_info
                    total_files += 1
                    total_size += file_info["size"]
                    
                    print(f"   ✅ {relative_path} ({file_type})")
                    
                except Exception as e:
                    print(f"   ⚠️  Bỏ qua {relative_path}: {e}")
        
        # Cập nhật metadata
        resource_data["metadata"]["total_files"] = total_files
        resource_data["metadata"]["total_size"] = total_size
        
        # Ghi file resource
        try:
            with open(self.resource_file, 'w', encoding='utf-8') as f:
                json.dump(resource_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Tạo thành công: {self.resource_file}")
            print(f"📊 Thống kê:")
            print(f"   • Tổng files: {total_files}")
            print(f"   • Tổng kích thước: {total_size:,} bytes")
            print(f"   • Kích thước resource: {os.path.getsize(self.resource_file):,} bytes")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi ghi file resource: {e}")
            return False
    
    def extract_resource_file(self, force=False):
        """Extract file resource thành folder bot_files"""
        print("🔄 Extract bot resource file...")
        
        if not os.path.exists(self.resource_file):
            print(f"❌ Không tìm thấy file resource: {self.resource_file}")
            return False
        
        # Kiểm tra folder đích
        if os.path.exists(self.bot_files_folder):
            if not force:
                print(f"⚠️  Folder {self.bot_files_folder} đã tồn tại!")
                response = input("Ghi đè? (y/N): ").lower()
                if response != 'y':
                    print("❌ Hủy extract")
                    return False
            
            # Backup folder cũ
            backup_name = f"{self.bot_files_folder}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(self.bot_files_folder, backup_name)
            print(f"💾 Backup folder cũ: {backup_name}")
        
        # Đọc resource file
        try:
            with open(self.resource_file, 'r', encoding='utf-8') as f:
                resource_data = json.load(f)
        except Exception as e:
            print(f"❌ Lỗi đọc resource file: {e}")
            return False
        
        # Tạo folder đích
        os.makedirs(self.bot_files_folder, exist_ok=True)
        
        # Extract files
        extracted_files = 0
        for relative_path, file_info in resource_data["files"].items():
            try:
                full_path = os.path.join(self.bot_files_folder, relative_path)
                
                # Tạo thư mục cha nếu cần
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Ghi file
                if file_info["type"] == "binary":
                    # File binary - decode base64
                    content = base64.b64decode(file_info["content"])
                    with open(full_path, 'wb') as f:
                        f.write(content)
                else:
                    # File text
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(file_info["content"])
                
                extracted_files += 1
                print(f"   ✅ {relative_path}")
                
            except Exception as e:
                print(f"   ❌ Lỗi extract {relative_path}: {e}")
        
        print(f"\n✅ Extract thành công!")
        print(f"📊 Thống kê:")
        print(f"   • Files extracted: {extracted_files}/{len(resource_data['files'])}")
        print(f"   • Folder: {self.bot_files_folder}")
        
        return True
    
    def update_resource_file(self):
        """Update file resource từ folder bot_files hiện tại"""
        print("🔄 Update bot resource file...")
        
        # Backup resource cũ nếu có
        if os.path.exists(self.resource_file):
            backup_name = f"{self.resource_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.resource_file, backup_name)
            print(f"💾 Backup resource cũ: {backup_name}")
        
        # Tạo resource mới
        return self.create_resource_file()
    
    def _is_binary_file(self, file_path):
        """Kiểm tra file có phải binary không"""
        binary_extensions = {
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.mp3', '.mp4', '.avi', '.mkv', '.wav',
            '.exe', '.dll', '.so', '.dylib',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx'
        }
        
        _, ext = os.path.splitext(file_path.lower())
        if ext in binary_extensions:
            return True
        
        # Kiểm tra nội dung file
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True
    
    def info(self):
        """Hiển thị thông tin resource file"""
        if not os.path.exists(self.resource_file):
            print(f"❌ Không tìm thấy resource file: {self.resource_file}")
            return
        
        try:
            with open(self.resource_file, 'r', encoding='utf-8') as f:
                resource_data = json.load(f)
            
            metadata = resource_data["metadata"]
            
            print(f"📋 THÔNG TIN RESOURCE FILE")
            print(f"=" * 40)
            print(f"File: {self.resource_file}")
            print(f"Tạo lúc: {metadata['created_at']}")
            print(f"Version: {metadata['version']}")
            print(f"Mô tả: {metadata['description']}")
            print(f"Tổng files: {metadata['total_files']}")
            print(f"Tổng kích thước: {metadata['total_size']:,} bytes")
            print(f"Kích thước resource: {os.path.getsize(self.resource_file):,} bytes")
            
            # Top 10 files lớn nhất
            files_by_size = sorted(
                resource_data["files"].items(),
                key=lambda x: x[1]["size"],
                reverse=True
            )[:10]
            
            print(f"\n📊 TOP 10 FILES LỚN NHẤT:")
            for path, info in files_by_size:
                print(f"   {info['size']:>8,} bytes - {path}")
                
        except Exception as e:
            print(f"❌ Lỗi đọc resource file: {e}")

def main():
    """Main function"""
    print("🚀 BOT RESOURCE MANAGER")
    print("=" * 50)
    
    manager = BotResourceManager()
    
    while True:
        print(f"\n📋 MENU:")
        print("1. Tạo resource file từ bot_files/")
        print("2. Extract resource file thành bot_files/")
        print("3. Update resource file")
        print("4. Xem thông tin resource file")
        print("5. Thoát")
        
        choice = input("\nChọn (1-5): ").strip()
        
        if choice == "1":
            print("\n" + "="*50)
            manager.create_resource_file()
            
        elif choice == "2":
            print("\n" + "="*50)
            manager.extract_resource_file()
            
        elif choice == "3":
            print("\n" + "="*50)
            manager.update_resource_file()
            
        elif choice == "4":
            print("\n" + "="*50)
            manager.info()
            
        elif choice == "5":
            print("\n👋 Tạm biệt!")
            break
            
        else:
            print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()
