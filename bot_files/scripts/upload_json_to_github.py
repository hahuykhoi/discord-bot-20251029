#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để upload tất cả file JSON commands lên GitHub repository
"""

import os
import json
import base64
import asyncio
import aiohttp
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubUploader:
    def __init__(self):
        self.github_token = self._get_github_token()
        self.owner = "hahuykhoi"
        self.repo = "bot-data-backup"
        self.branch = "main"
        
    def _get_github_token(self):
        """Lấy GitHub token từ environment hoặc file"""
        # Ưu tiên environment variable
        token = os.getenv('GITHUB_TOKEN')
        if token:
            return token
            
        # Fallback to file
        try:
            with open('github_token.txt', 'r') as f:
                return f.read().strip()
        except:
            logger.error("Không tìm thấy GitHub token!")
            return None
    
    async def upload_file(self, local_path, github_path, content):
        """Upload một file lên GitHub"""
        if not self.github_token:
            raise Exception("GitHub token không được cấu hình!")
        
        # Encode content to base64
        content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # GitHub API URL
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{github_path}"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Discord-Bot-Uploader'
        }
        
        # Kiểm tra file đã tồn tại chưa để lấy SHA
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    sha = data.get('sha')
        
        # Payload để upload
        payload = {
            'message': f'Update {os.path.basename(github_path)} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'content': content_encoded,
            'branch': self.branch
        }
        
        if sha:
            payload['sha'] = sha
        
        # Upload file
        async with aiohttp.ClientSession() as session:
            async with session.put(api_url, headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Uploaded: {github_path}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to upload {github_path}: {response.status} - {error_text}")
                    return False
    
    async def upload_all_json_files(self):
        """Upload tất cả file JSON từ thư mục data"""
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        
        if not os.path.exists(data_dir):
            logger.error(f"Thư mục data không tồn tại: {data_dir}")
            return
        
        success_count = 0
        total_count = 0
        
        # Lấy danh sách tất cả file JSON
        json_files = []
        for file in os.listdir(data_dir):
            if file.endswith('.json'):
                json_files.append(file)
        
        logger.info(f"Tìm thấy {len(json_files)} file JSON để upload")
        
        # Upload từng file
        for filename in json_files:
            local_path = os.path.join(data_dir, filename)
            github_path = f"data/{filename}"
            
            try:
                # Đọc nội dung file
                with open(local_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Validate JSON
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️  File {filename} không phải JSON hợp lệ: {e}")
                    continue
                
                # Upload file
                total_count += 1
                if await self.upload_file(local_path, github_path, content):
                    success_count += 1
                
                # Delay để tránh rate limit
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi xử lý {filename}: {e}")
                total_count += 1
        
        logger.info(f"\n📊 KẾT QUẢ UPLOAD:")
        logger.info(f"✅ Thành công: {success_count}/{total_count}")
        logger.info(f"❌ Thất bại: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            logger.info("🎉 Tất cả file đã được upload thành công!")
        
        return success_count, total_count

async def main():
    """Main function"""
    print("🚀 Bắt đầu upload file JSON lên GitHub...")
    print(f"📁 Repository: hahuykhoi/bot-data-backup")
    print(f"🌿 Branch: main")
    print("-" * 50)
    
    uploader = GitHubUploader()
    
    if not uploader.github_token:
        print("❌ Không tìm thấy GitHub token!")
        print("\nVui lòng:")
        print("1. Tạo file 'github_token.txt' chứa GitHub token")
        print("2. Hoặc set environment variable GITHUB_TOKEN")
        return
    
    try:
        success, total = await uploader.upload_all_json_files()
        
        if success == total and total > 0:
            print("\n🎉 HOÀN THÀNH! Tất cả file JSON đã được upload lên GitHub.")
            print("📝 Bây giờ bạn có thể sửa bot để load từ GitHub thay vì local.")
        elif success > 0:
            print(f"\n⚠️  Upload một phần thành công: {success}/{total}")
        else:
            print("\n❌ Không có file nào được upload thành công!")
            
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn: {e}")

if __name__ == "__main__":
    asyncio.run(main())
