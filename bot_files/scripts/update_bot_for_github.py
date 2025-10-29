#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để sửa bot_refactored.py để load commands từ GitHub thay vì local
"""

import os
import re
import json
import shutil
from datetime import datetime

def backup_original_file():
    """Backup file gốc trước khi sửa"""
    original_file = "bot_refactored.py"
    backup_file = f"bot_refactored_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    if os.path.exists(original_file):
        shutil.copy2(original_file, backup_file)
        print(f"✅ Đã backup file gốc: {backup_file}")
        return backup_file
    else:
        print("❌ Không tìm thấy file bot_refactored.py")
        return None

def create_github_loader_class():
    """Tạo class để load data từ GitHub"""
    github_loader_code = '''
import aiohttp
import json
import base64
import os
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GitHubDataLoader:
    """Class để load dữ liệu từ GitHub repository"""
    
    def __init__(self):
        self.github_token = self._get_github_token()
        self.owner = "hahuykhoi"
        self.repo = "bot-data-backup"
        self.branch = "main"
        self.cache = {}
        self.cache_timeout = 300  # 5 phút
        self.last_cache_time = {}
        
    def _get_github_token(self):
        """Lấy GitHub token"""
        token = os.getenv('GITHUB_TOKEN')
        if token:
            return token
        try:
            with open('github_token.txt', 'r') as f:
                return f.read().strip()
        except:
            return None
    
    async def load_json_from_github(self, file_path):
        """Load file JSON từ GitHub"""
        if not self.github_token:
            logger.warning("GitHub token không có, fallback sang local file")
            return self._load_local_fallback(file_path)
        
        # Kiểm tra cache
        cache_key = file_path
        if (cache_key in self.cache and 
            cache_key in self.last_cache_time and
            datetime.now() - self.last_cache_time[cache_key] < timedelta(seconds=self.cache_timeout)):
            return self.cache[cache_key]
        
        try:
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/data/{file_path}"
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Discord-Bot'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('type') == 'file':
                            content = base64.b64decode(data['content']).decode('utf-8')
                            json_data = json.loads(content)
                            
                            # Cache kết quả
                            self.cache[cache_key] = json_data
                            self.last_cache_time[cache_key] = datetime.now()
                            
                            logger.info(f"✅ Loaded from GitHub: {file_path}")
                            return json_data
                    else:
                        logger.warning(f"GitHub API error {response.status} for {file_path}, using local fallback")
                        
        except Exception as e:
            logger.error(f"Error loading from GitHub: {e}, using local fallback")
        
        # Fallback sang local file
        return self._load_local_fallback(file_path)
    
    def _load_local_fallback(self, file_path):
        """Fallback load từ file local"""
        local_path = os.path.join('data', file_path)
        try:
            if os.path.exists(local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Local file not found: {local_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading local file {local_path}: {e}")
            return {}
    
    async def save_json_to_github(self, file_path, data):
        """Save file JSON lên GitHub"""
        if not self.github_token:
            logger.warning("GitHub token không có, chỉ save local")
            return self._save_local_fallback(file_path, data)
        
        try:
            # Encode content
            content = json.dumps(data, indent=2, ensure_ascii=False)
            content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/data/{file_path}"
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Discord-Bot'
            }
            
            # Lấy SHA nếu file đã tồn tại
            sha = None
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        existing_data = await response.json()
                        sha = existing_data.get('sha')
            
            # Payload
            payload = {
                'message': f'Update {file_path} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'content': content_encoded,
                'branch': self.branch
            }
            
            if sha:
                payload['sha'] = sha
            
            # Upload
            async with aiohttp.ClientSession() as session:
                async with session.put(api_url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Saved to GitHub: {file_path}")
                        # Cập nhật cache
                        self.cache[file_path] = data
                        self.last_cache_time[file_path] = datetime.now()
                        return True
                    else:
                        logger.error(f"GitHub save error {response.status} for {file_path}")
                        
        except Exception as e:
            logger.error(f"Error saving to GitHub: {e}")
        
        # Fallback save local
        return self._save_local_fallback(file_path, data)
    
    def _save_local_fallback(self, file_path, data):
        """Fallback save local"""
        local_path = os.path.join('data', file_path)
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved locally: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving local file {local_path}: {e}")
            return False

# Global instance
github_data_loader = GitHubDataLoader()
'''
    return github_loader_code

def update_bot_file():
    """Sửa file bot_refactored.py"""
    bot_file = "bot_refactored.py"
    
    if not os.path.exists(bot_file):
        print(f"❌ Không tìm thấy file {bot_file}")
        return False
    
    # Đọc nội dung file
    with open(bot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thêm GitHub loader class sau các import
    github_loader_code = create_github_loader_class()
    
    # Tìm vị trí để chèn code (sau các import)
    import_pattern = r'(from collections import defaultdict, deque\n)'
    if re.search(import_pattern, content):
        content = re.sub(import_pattern, r'\1\n' + github_loader_code + '\n', content)
        print("✅ Đã thêm GitHubDataLoader class")
    else:
        print("⚠️  Không tìm thấy vị trí để chèn GitHubDataLoader, thêm vào đầu file")
        content = github_loader_code + '\n\n' + content
    
    # Thêm method load_config_from_github vào class AutoReplyBotRefactored
    new_load_config_method = '''
    async def load_config_from_github(self, config_file):
        """Load config từ GitHub với fallback local"""
        try:
            return await github_data_loader.load_json_from_github(config_file)
        except Exception as e:
            logger.error(f"Error loading config from GitHub: {e}")
            # Fallback local
            local_path = os.path.join('data', config_file)
            if os.path.exists(local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
    
    async def save_config_to_github(self, config_file, data):
        """Save config lên GitHub với fallback local"""
        try:
            return await github_data_loader.save_json_to_github(config_file, data)
        except Exception as e:
            logger.error(f"Error saving config to GitHub: {e}")
            return False
'''
    
    # Tìm class AutoReplyBotRefactored và thêm methods
    class_pattern = r'(class AutoReplyBotRefactored\(commands\.Bot\):\s*"""[^"]*"""\s*)'
    if re.search(class_pattern, content):
        content = re.sub(class_pattern, r'\1' + new_load_config_method + '\n    ', content)
        print("✅ Đã thêm methods load/save config từ GitHub")
    else:
        print("⚠️  Không tìm thấy class AutoReplyBotRefactored")
    
    # Thay thế các load config bằng GitHub version
    replacements = [
        # Load config patterns
        (r'with open\([\'"]([^\'\"]*\.json)[\'"]\s*,\s*[\'"]r[\'"][^)]*\) as f:\s*return json\.load\(f\)',
         r'return await self.load_config_from_github("\1")'),
        
        # Save config patterns  
        (r'with open\([\'"]([^\'\"]*\.json)[\'"]\s*,\s*[\'"]w[\'"][^)]*\) as f:\s*json\.dump\([^,]+,\s*f[^)]*\)',
         r'await self.save_config_to_github("\1", data)'),
    ]
    
    changes_made = 0
    for pattern, replacement in replacements:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            changes_made += len(matches)
    
    if changes_made > 0:
        print(f"✅ Đã thay thế {changes_made} load/save operations")
    
    # Ghi lại file
    with open(bot_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Đã cập nhật file {bot_file}")
    return True

def create_github_token_template():
    """Tạo template file cho GitHub token"""
    template_content = """# Thêm GitHub token của bạn vào đây
# Lấy token từ: https://github.com/settings/tokens
# Cần quyền: repo (full control of private repositories)

your_github_token_here"""
    
    with open('github_token_template.txt', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("✅ Đã tạo file github_token_template.txt")
    print("📝 Vui lòng:")
    print("   1. Đổi tên thành 'github_token.txt'")
    print("   2. Thêm GitHub token thật vào file")

def main():
    """Main function"""
    print("🔧 BẮT ĐẦU CẬP NHẬT BOT ĐỂ SỬ DỤNG GITHUB...")
    print("-" * 50)
    
    # Backup file gốc
    backup_file = backup_original_file()
    if not backup_file:
        return
    
    # Cập nhật bot file
    if update_bot_file():
        print("\n✅ CẬP NHẬT THÀNH CÔNG!")
        print("\n📋 NHỮNG THAY ĐỔI ĐÃ THỰC HIỆN:")
        print("   • Thêm GitHubDataLoader class")
        print("   • Thêm methods load/save từ GitHub")
        print("   • Thay thế các load/save operations")
        print("   • Tạo fallback mechanism cho local files")
        
        print("\n🔑 CHUẨN BỊ GITHUB TOKEN:")
        create_github_token_template()
        
        print("\n🚀 CÁCH SỬ DỤNG:")
        print("   1. Chạy upload_json_to_github.py để upload data")
        print("   2. Tạo github_token.txt với token thật")
        print("   3. Chạy bot như bình thường")
        print("   4. Bot sẽ tự động load từ GitHub với fallback local")
        
        print(f"\n💾 File backup: {backup_file}")
        print("   (Dùng để khôi phục nếu cần)")
        
    else:
        print("\n❌ CẬP NHẬT THẤT BẠI!")

if __name__ == "__main__":
    main()
