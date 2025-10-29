# 🚀 HƯỚNG DẪN NHANH - GITHUB INTEGRATION

## 📋 Tổng quan
Đã tạo hệ thống để bot load/save dữ liệu từ GitHub thay vì chỉ local files.

## 🔥 CÁCH THỰC HIỆN NHANH

### Bước 1: Chuẩn bị GitHub Token
1. Vào https://github.com/settings/tokens
2. Tạo token mới với quyền `repo` (full control)
3. Copy token

### Bước 2: Tạo file token
Tạo file `github_token.txt` và paste token vào:
```
your_actual_github_token_here
```

### Bước 3: Chạy setup tự động
```bash
python setup_github_integration.py
```

Script sẽ tự động:
- ✅ Upload tất cả file JSON lên GitHub
- ✅ Sửa bot_refactored.py để load từ GitHub
- ✅ Tạo fallback mechanism
- ✅ Tạo script chạy bot

### Bước 4: Chạy bot
```bash
python bot_refactored.py
```

## 📁 Files đã tạo

### Scripts chính:
- `setup_github_integration.py` - Setup tự động toàn bộ
- `upload_json_to_github.py` - Upload JSON files
- `update_bot_for_github.py` - Sửa bot code

### Files hỗ trợ:
- `run_bot_github.bat` - Script chạy bot
- `README_GITHUB_INTEGRATION.md` - Hướng dẫn chi tiết
- `github_token_template.txt` - Template token

### Backup:
- `bot_refactored_backup_*.py` - Backup bot gốc

## 🔄 Workflow mới

### Load Data:
1. Bot thử load từ GitHub trước
2. Nếu lỗi → fallback sang local files
3. Cache 5 phút để giảm API calls

### Save Data:
1. Bot save lên GitHub
2. Đồng thời save local làm backup
3. Nếu GitHub lỗi → chỉ save local

## 🛠️ Troubleshooting

### Lỗi GitHub token:
```
❌ GitHub token không được cấu hình!
```
**Giải pháp**: Tạo file `github_token.txt` với token thật

### Lỗi permissions:
```
❌ Không có quyền truy cập repository!
```
**Giải pháp**: Đảm bảo token có quyền `repo`

### Lỗi network:
```
⚠️ GitHub API error, using local fallback
```
**Không cần lo**: Bot tự động dùng local files

## 📊 Repository GitHub

- **Owner**: hahuykhoi
- **Repo**: bot-data-backup
- **Branch**: main
- **Structure**:
  ```
  bot-data-backup/
  └── data/
      ├── config.json
      ├── shared_wallet.json
      ├── taixiu_players.json
      └── ... (tất cả file JSON)
  ```

## 🎯 Lợi ích

### ✅ Ưu điểm:
- Dữ liệu được backup tự động lên GitHub
- Có thể sync giữa nhiều instance bot
- Fallback an toàn sang local files
- Cache giảm API calls

### 🔒 An toàn:
- Local files vẫn được giữ làm backup
- Có thể rollback bất cứ lúc nào
- Bot vẫn chạy nếu GitHub lỗi

## 🚨 Lưu ý quan trọng

1. **GitHub Token**: Giữ bí mật, không share
2. **Rate Limit**: GitHub API có limit 5000 requests/hour
3. **Cache**: Dữ liệu cache 5 phút, có thể delay update
4. **Backup**: File gốc được backup tự động

## 🔙 Rollback nếu cần

Nếu muốn quay lại version cũ:
1. Tìm file `bot_refactored_backup_*.py`
2. Đổi tên thành `bot_refactored.py`
3. Bot sẽ chỉ dùng local files như trước

---

## ⚡ TL;DR - Làm ngay

```bash
# 1. Tạo github_token.txt với token thật
echo "your_github_token_here" > github_token.txt

# 2. Chạy setup
python setup_github_integration.py

# 3. Chạy bot
python bot_refactored.py
```

**Xong!** Bot giờ sẽ load/save từ GitHub với fallback local. 🎉
