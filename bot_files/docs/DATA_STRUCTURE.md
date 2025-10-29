# 📁 Cấu trúc Data Folder

Hệ thống quản lý dữ liệu được tổ chức trong folder `data/` để dễ dàng backup và đồng bộ với GitHub.

## 🗂️ Cấu trúc thư mục

```
bot/
├── data/                          # Folder chứa tất cả dữ liệu
│   ├── shared_wallet.json         # Dữ liệu ví tiền chung
│   ├── taixiu_data.json          # Dữ liệu game tài xỉu
│   ├── api-gemini.json           # Cấu hình API Gemini
│   ├── config.json               # Cấu hình bot chính
│   ├── admin.json                # Danh sách admin IDs
│   ├── warnings.json             # Dữ liệu warnings
│   ├── priority.json             # Danh sách priority users
│   ├── supreme_admin.json        # Supreme Admin ID
│   ├── auto_delete_config.json   # Cấu hình Auto Delete
│   ├── fire_delete_config.json   # Cấu hình Fire Delete
│   ├── afk_data.json             # Dữ liệu AFK users
│   ├── banned_users.json         # Danh sách users bị ban
│   └── migration_report.json     # Báo cáo migration
├── data_backups/                 # Folder backup tự động
├── bot_refactored.py            # File bot chính
├── migrate_data.py              # Script migration
└── commands/                    # Folder commands
```

## 🚀 Migration (Di chuyển dữ liệu)

### Cách 1: Sử dụng script Python
```bash
python migrate_data.py
```

### Cách 2: Sử dụng lệnh bot
```
;backup migrate
```

### Cách 3: Tự động khi khởi động bot
Bot sẽ tự động tạo folder `data/` và di chuyển files khi cần thiết.

## 📦 Backup & Sync với GitHub

### Cấu hình GitHub
File `config_github.json` đã được cập nhật để backup folder `data/`:

```json
{
    "repository_url": "https://github.com/username/bot_discord.git",
    "branch": "main",
    "data_files": [
        "data/shared_wallet.json",
        "data/taixiu_data.json",
        "data/api-gemini.json",
        "data/config.json",
        "data/admin.json",
        "data/warnings.json",
        "data/priority.json",
        "data/supreme_admin.json",
        "data/auto_delete_config.json",
        "data/fire_delete_config.json",
        "data/afk_data.json",
        "data/banned_users.json"
    ],
    "data_folder": "data"
}
```

### Lệnh backup
```bash
;backup sync      # Đồng bộ với GitHub (backup trước)
;backup pull      # Tải code mới từ GitHub  
;backup restore   # Khôi phục hoàn toàn từ GitHub
;backup migrate   # Di chuyển dữ liệu vào data/
;backup status    # Kiểm tra trạng thái Git
;backup config    # Xem cấu hình GitHub
```

## 🔄 Tự động Migration

### Khi nào migration xảy ra?
1. **Khởi động bot lần đầu** - Tự động tạo folder `data/`
2. **Phát hiện files ở root** - Tự động di chuyển vào `data/`
3. **Chạy lệnh migrate** - Di chuyển thủ công
4. **Backup/Restore** - Tự động tổ chức dữ liệu

### Backup an toàn
- Mọi migration đều tạo backup trong `data_backups/`
- Backup có timestamp để dễ theo dõi
- Không mất dữ liệu trong quá trình migration

## 📋 Files trong Data Folder

| File | Mô tả | Được sử dụng bởi |
|------|-------|------------------|
| `shared_wallet.json` | Ví tiền chung của users | Wallet Commands |
| `taixiu_data.json` | Dữ liệu game tài xỉu | TaiXiu Commands |
| `api-gemini.json` | Cấu hình API Gemini AI | AI Commands |
| `config.json` | Cấu hình bot chính | Bot Core |
| `admin.json` | Danh sách admin IDs | Admin System |
| `warnings.json` | Dữ liệu warnings users | Warn Commands |
| `priority.json` | Priority users (bypass rate limit) | Rate Limiter |
| `supreme_admin.json` | Supreme Admin ID | Permission System |
| `auto_delete_config.json` | Cấu hình Auto Delete | Auto Delete Commands |
| `fire_delete_config.json` | Cấu hình Fire Delete | Fire Delete Commands |
| `afk_data.json` | Dữ liệu users AFK | AFK Commands |
| `banned_users.json` | Danh sách users bị ban | Ban Commands |

## 🛠️ Troubleshooting

### Lỗi thường gặp

**1. Permission denied khi migrate**
```bash
# Kiểm tra quyền ghi
ls -la data/
# Cấp quyền nếu cần
chmod 755 data/
```

**2. Files bị duplicate**
```bash
# Chạy migration để dọn dẹp
python migrate_data.py
```

**3. Mất dữ liệu sau migration**
```bash
# Kiểm tra backup
ls data_backups/
# Khôi phục từ backup nếu cần
```

### Kiểm tra cấu trúc
```python
# Chạy script kiểm tra
python migrate_data.py
```

## 🎯 Lợi ích của Data Folder

### ✅ Ưu điểm
- **Tổ chức tốt**: Tất cả dữ liệu ở một nơi
- **Backup dễ dàng**: Chỉ cần backup folder `data/`
- **Sync GitHub**: Tự động đồng bộ với repository
- **An toàn**: Backup tự động trước mọi thay đổi
- **Portable**: Dễ dàng di chuyển giữa các server

### 🔄 Tương thích ngược
- Bot vẫn hoạt động với files ở root (tự động migrate)
- Không cần thay đổi cấu hình hiện có
- Migration an toàn với backup tự động

## 📞 Hỗ trợ

Nếu gặp vấn đề với data migration:
1. Kiểm tra logs trong console
2. Chạy `python migrate_data.py` để kiểm tra
3. Sử dụng |\1 status` để xem trạng thái
4. Liên hệ Supreme Admin nếu cần hỗ trợ

---

**Lưu ý**: Hệ thống tự động backup trước mọi thay đổi, đảm bảo dữ liệu luôn an toàn! 🛡️
