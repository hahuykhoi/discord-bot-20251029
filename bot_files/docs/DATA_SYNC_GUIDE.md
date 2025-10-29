# 🔄 Hướng dẫn đồng bộ code và bảo vệ dữ liệu

## 📋 Vấn đề
- Bạn code ở **máy local** (Windows)
- Bot chạy trên **hosting** (Linux server)
- Khi update code, **dữ liệu người chơi** (tiền, stats) có thể bị mất

## ✅ Giải pháp
1. **Tách riêng data và code** - Data files không commit vào Git
2. **Backup/Restore** - Scripts tự động backup và restore data
3. **Workflow an toàn** - Quy trình chuẩn để update không mất data

---

## 🛠️ Các công cụ đã có sẵn

### 1. **`.gitignore`** - Bảo vệ data files
- Tất cả file `.json` chứa data người chơi đã được exclude
- Không bao giờ commit vào Git

### 2. **`backup_data.py`** - Backup dữ liệu
```bash
python backup_data.py          # Tạo backup mới
python backup_data.py list     # Xem danh sách backup
```

### 3. **`restore_data.py`** - Restore dữ liệu  
```bash
python restore_data.py                    # Chọn backup từ danh sách
python restore_data.py backup_xxx.zip     # Restore backup cụ thể
```

---

## 📝 WORKFLOW UPDATE CODE - KHÔNG MẤT DATA

### **Trên máy LOCAL (Windows):**

#### Bước 1: Code tính năng mới
```bash
# Code tính năng mới
# Test ở local
```

#### Bước 2: Commit và push lên GitHub
```bash
git add .
git commit -m "Thêm tính năng xyz"
git push origin main
```

✅ **Data files KHÔNG được push** (đã có trong `.gitignore`)

---

### **Trên HOSTING (Linux server):**

#### Bước 1: Đóng bot và backup data
```bash
# SSH vào hosting
ssh user@your-hosting.com

# Di chuyển vào thư mục bot
cd /path/to/bot/

# Đóng bot (để không ai chơi game)
python3 -c "from commands.maintenance_commands import *"
# Hoặc trong Discord: ;close Đang update tính năng mới

# Backup tất cả data
python3 backup_data.py
```

**Output:**
```
📦 Đang backup dữ liệu vào: data_backups/backup_20251002_164632/
============================================================
✅ shared_wallet.json          (622 bytes)
✅ taixiu_data.json            (3,670 bytes)
✅ flip_coin_data.json         (209 bytes)
...
============================================================
📊 Thống kê:
  ✅ Backed up: 15 files
  ⚠️  Missing:   3 files

📦 Đã tạo file zip: data_backups/backup_20251002_164632.zip (8,245 bytes)
📋 Backup info: data_backups/backup_20251002_164632_info.json
🎉 Backup hoàn tất!
```

#### Bước 2: Pull code mới từ GitHub
```bash
# Pull code mới
git pull origin main
```

✅ **Chỉ code được update**, data files không bị ghi đè

#### Bước 3: Restore data (nếu cần)
```bash
# Nếu data bị mất (không nên xảy ra nhưng để chắc chắn)
python3 restore_data.py

# Hoặc restore backup cụ thể
python3 restore_data.py backup_20251002_164632.zip
```

#### Bước 4: Khởi động lại bot
```bash
# Khởi động bot
python3 bot_refactored.py

# Hoặc nếu dùng systemd
sudo systemctl restart discord-bot

# Mở lại bot trong Discord
# ;open
```

---

## 🎯 WORKFLOW NHANH (Khi đã quen)

### Trên LOCAL:
```bash
git add .
git commit -m "Update features"
git push
```

### Trên HOSTING:
```bash
# Backup + Update + Restart
python3 backup_data.py && git pull && sudo systemctl restart discord-bot
```

**Một dòng lệnh, xong việc!** 🚀

---

## 📦 Quản lý Backups

### Xem danh sách backup
```bash
python3 backup_data.py list
```

**Output:**
```
📦 Các backup có sẵn:
============================================================
1. backup_20251002_164632.zip
   📅 02/10/2025 16:46:32
   📦 8,245 bytes

2. backup_20251002_120000.zip
   📅 02/10/2025 12:00:00
   📦 7,892 bytes
```

### Restore từ backup cụ thể
```bash
python3 restore_data.py backup_20251002_164632.zip
```

### Auto cleanup backups cũ (optional)
```bash
# Xóa backup cũ hơn 30 ngày
find data_backups/ -name "*.zip" -mtime +30 -delete
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### ✅ BẮT BUỘC:
1. **Backup TRƯỚC KHI pull code mới**
2. **Đóng bot** (|\1`) trước khi backup
3. **Kiểm tra** data files sau khi pull

### ❌ KHÔNG NÊN:
1. Commit file `.json` chứa data vào Git
2. Pull code khi bot đang chạy
3. Quên backup trước khi update

### 💾 Backup tự động (optional):
Tạo cron job backup hàng ngày:
```bash
# Crontab entry - backup mỗi ngày 3AM
0 3 * * * cd /path/to/bot && python3 backup_data.py >> backup.log 2>&1
```

---

## 🔍 Troubleshooting

### **Data bị mất sau khi pull?**
```bash
# Restore từ backup gần nhất
python3 restore_data.py

# Chọn backup từ danh sách
```

### **Không tìm thấy backup?**
```bash
# List tất cả backups
ls -lah data_backups/

# Nếu không có backup nào - RIP 😢
# Lần sau nhớ backup trước!
```

### **Bot không khởi động sau update?**
```bash
# Xem log lỗi
python3 bot_refactored.py

# Hoặc
journalctl -u discord-bot -n 50
```

---

## 📊 Data Files được backup

### 💰 Money & Wallet
- `shared_wallet.json` - Ví chung
- `wallet_data.json` - Data ví

### 🎮 Game Data  
- `taixiu_data.json` - Tài xỉu
- `flip_coin_data.json` - Flip coin
- `rps_data.json` - Kéo búa bao
- `slot_data.json` - Slot machine
- `blackjack_data.json` - Blackjack

### 👤 User Data
- `daily_data.json` - Daily rewards
- `warnings.json` - Cảnh cáo
- `priority.json` - Priority users

### ⚙️ Bot Config
- `maintenance_mode.json` - Trạng thái bảo trì
- `channel_permissions.json` - Quyền channel
- `command_permissions.json` - Quyền lệnh

---

## 🎉 Kết luận

### ✅ Với workflow này:
- ✅ Code được sync qua GitHub
- ✅ Data KHÔNG bao giờ mất
- ✅ Update nhanh, an toàn
- ✅ Rollback dễ dàng nếu có lỗi

### 📱 Quick Reference:
```bash
# LOCAL: Push code
git push

# HOSTING: Update bot
python3 backup_data.py && git pull && sudo systemctl restart discord-bot
```

**Đơn giản, nhanh, an toàn!** 🚀
