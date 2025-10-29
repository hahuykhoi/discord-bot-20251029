#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script chính để setup GitHub integration cho Discord bot
Thực hiện tất cả các bước: upload JSON, update bot code, setup token
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime

def print_header():
    """In header đẹp"""
    print("=" * 60)
    print("🚀 DISCORD BOT GITHUB INTEGRATION SETUP")
    print("=" * 60)
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Thư mục: {os.getcwd()}")
    print("=" * 60)

def check_requirements():
    """Kiểm tra các yêu cầu cần thiết"""
    print("\n🔍 KIỂM TRA YÊU CẦU...")
    
    required_files = [
        'bot_refactored.py',
        'data/',
        'upload_json_to_github.py',
        'update_bot_for_github.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Thiếu các file/thư mục sau:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    print("✅ Tất cả file cần thiết đã có")
    return True

def check_github_token():
    """Kiểm tra GitHub token"""
    print("\n🔑 KIỂM TRA GITHUB TOKEN...")
    
    # Kiểm tra environment variable
    if os.getenv('GITHUB_TOKEN'):
        print("✅ Tìm thấy GITHUB_TOKEN trong environment variables")
        return True
    
    # Kiểm tra file
    if os.path.exists('github_token.txt'):
        try:
            with open('github_token.txt', 'r') as f:
                token = f.read().strip()
                if token and not token.startswith('your_github_token'):
                    print("✅ Tìm thấy GitHub token trong file")
                    return True
        except:
            pass
    
    print("❌ Không tìm thấy GitHub token!")
    print("\n📝 VUI LÒNG SETUP GITHUB TOKEN:")
    print("   CÁCH 1: Environment Variable")
    print("   set GITHUB_TOKEN=your_token_here")
    print("\n   CÁCH 2: File github_token.txt")
    print("   1. Tạo file 'github_token.txt'")
    print("   2. Paste GitHub token vào file")
    print("\n🔗 Lấy token tại: https://github.com/settings/tokens")
    print("   Cần quyền: repo (full control of private repositories)")
    
    return False

async def run_upload_script():
    """Chạy script upload JSON files"""
    print("\n📤 UPLOAD FILE JSON LÊN GITHUB...")
    
    try:
        # Import và chạy upload script
        sys.path.insert(0, os.getcwd())
        from upload_json_to_github import GitHubUploader
        
        uploader = GitHubUploader()
        success, total = await uploader.upload_all_json_files()
        
        if success == total and total > 0:
            print(f"✅ Upload thành công tất cả {total} file JSON")
            return True
        elif success > 0:
            print(f"⚠️  Upload thành công {success}/{total} file")
            return True
        else:
            print("❌ Không upload được file nào")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi khi upload: {e}")
        return False

def run_update_bot_script():
    """Chạy script update bot code"""
    print("\n🔧 CẬP NHẬT BOT CODE...")
    
    try:
        # Import và chạy update script
        sys.path.insert(0, os.getcwd())
        from update_bot_for_github import main as update_main
        
        update_main()
        print("✅ Cập nhật bot code thành công")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật bot: {e}")
        return False

def create_run_script():
    """Tạo script để chạy bot với GitHub integration"""
    script_content = '''@echo off
echo Starting Discord Bot with GitHub Integration...
echo.

REM Kiểm tra GitHub token
if not exist "github_token.txt" (
    echo ERROR: github_token.txt not found!
    echo Please create this file with your GitHub token.
    echo.
    pause
    exit /b 1
)

REM Chạy bot
echo Loading bot...
python bot_refactored.py

pause
'''
    
    with open('run_bot_github.bat', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Đã tạo script chạy bot: run_bot_github.bat")

def create_readme():
    """Tạo README hướng dẫn sử dụng"""
    readme_content = '''# Discord Bot GitHub Integration

## 📋 Tổng quan
Bot Discord đã được cập nhật để load/save dữ liệu từ GitHub repository thay vì chỉ local files.

## 🔧 Cấu hình

### 1. GitHub Token
Tạo file `github_token.txt` chứa GitHub Personal Access Token:
```
your_github_token_here
```

Hoặc set environment variable:
```bash
set GITHUB_TOKEN=your_token_here
```

### 2. Repository
- Owner: `hahuykhoi`
- Repo: `bot-data-backup`
- Branch: `main`

## 🚀 Cách chạy

### Chạy với GitHub Integration:
```bash
python bot_refactored.py
```

Hoặc dùng script:
```bash
run_bot_github.bat
```

## 📁 Cấu trúc dữ liệu

### Local (Fallback):
```
data/
├── config.json
├── shared_wallet.json
├── taixiu_players.json
└── ...
```

### GitHub Repository:
```
bot-data-backup/
└── data/
    ├── config.json
    ├── shared_wallet.json
    ├── taixiu_players.json
    └── ...
```

## 🔄 Workflow

1. **Load Data**: Bot ưu tiên load từ GitHub, fallback local nếu lỗi
2. **Save Data**: Bot save lên GitHub và local đồng thời
3. **Cache**: Dữ liệu GitHub được cache 5 phút để giảm API calls
4. **Sync**: Dữ liệu được sync tự động khi có thay đổi

## 🛠️ Troubleshooting

### Bot không load được từ GitHub:
- Kiểm tra GitHub token
- Kiểm tra internet connection
- Bot sẽ tự động fallback sang local files

### Lỗi permissions:
- Đảm bảo token có quyền `repo` (full control)
- Kiểm tra repository `hahuykhoi/bot-data-backup` tồn tại

### Lỗi rate limit:
- GitHub API có limit 5000 requests/hour
- Bot có cache 5 phút để giảm requests
- Nếu vượt limit, bot sẽ dùng local files

## 📊 Monitoring

Bot sẽ log các hoạt động:
- `✅ Loaded from GitHub: filename.json`
- `✅ Saved to GitHub: filename.json`
- `⚠️ GitHub API error, using local fallback`

## 🔙 Rollback

Nếu cần quay lại version cũ:
1. Dùng file backup: `bot_refactored_backup_*.py`
2. Đổi tên thành `bot_refactored.py`
3. Bot sẽ chỉ dùng local files như trước

## 📝 Notes

- Tất cả file JSON trong thư mục `data/` đều được sync với GitHub
- Bot vẫn hoạt động bình thường nếu không có GitHub token
- Dữ liệu local luôn được giữ làm backup
'''
    
    with open('README_GITHUB_INTEGRATION.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Đã tạo README: README_GITHUB_INTEGRATION.md")

async def main():
    """Main function"""
    print_header()
    
    # Kiểm tra yêu cầu
    if not check_requirements():
        print("\n❌ SETUP THẤT BẠI - Thiếu file cần thiết")
        return
    
    # Kiểm tra GitHub token
    if not check_github_token():
        print("\n❌ SETUP THẤT BẠI - Cần GitHub token")
        return
    
    print("\n🎯 BẮT ĐẦU SETUP...")
    
    # Bước 1: Upload JSON files
    upload_success = await run_upload_script()
    if not upload_success:
        print("\n❌ SETUP THẤT BẠI - Không upload được files")
        return
    
    # Bước 2: Update bot code
    update_success = run_update_bot_script()
    if not update_success:
        print("\n❌ SETUP THẤT BẠI - Không update được bot code")
        return
    
    # Bước 3: Tạo các file hỗ trợ
    create_run_script()
    create_readme()
    
    # Hoàn thành
    print("\n" + "=" * 60)
    print("🎉 SETUP GITHUB INTEGRATION THÀNH CÔNG!")
    print("=" * 60)
    
    print("\n📋 ĐÃ HOÀN THÀNH:")
    print("   ✅ Upload tất cả file JSON lên GitHub")
    print("   ✅ Cập nhật bot code để load từ GitHub")
    print("   ✅ Tạo fallback mechanism cho local files")
    print("   ✅ Tạo script chạy bot: run_bot_github.bat")
    print("   ✅ Tạo README hướng dẫn")
    
    print("\n🚀 CÁCH SỬ DỤNG:")
    print("   1. Chạy: python bot_refactored.py")
    print("   2. Hoặc: run_bot_github.bat")
    print("   3. Bot sẽ tự động load từ GitHub với fallback local")
    
    print("\n📊 MONITORING:")
    print("   • Bot sẽ log khi load/save từ GitHub")
    print("   • Nếu GitHub lỗi, bot dùng local files")
    print("   • Cache 5 phút để giảm API calls")
    
    print("\n💾 BACKUP:")
    print("   • File gốc được backup với timestamp")
    print("   • Local files vẫn được giữ làm fallback")
    print("   • Có thể rollback bất cứ lúc nào")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup bị hủy bởi user")
    except Exception as e:
        print(f"\n\n❌ Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
