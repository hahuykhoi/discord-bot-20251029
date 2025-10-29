# 🤖 Multi-Bot System Guide

## Tổng quan
Multi-Bot System cho phép admin quản lý và sử dụng nhiều bot Discord cùng lúc để gửi tin nhắn, tạo hiệu ứng đặc biệt và quản lý server hiệu quả hơn.

## 🔧 Cài đặt

### 1. Cấu hình Token Bot
- File cấu hình: `tokens/bot_config.json`
- Chứa thông tin tất cả bot và settings
- Tự động tạo khi chạy lần đầu

### 2. Thêm Bot mới
```
;multibot add <tên_bot> <token> [mô_tả]
```
**Ví dụ:**
```
;multibot add backup BOT_TOKEN_HERE Bot dự phòng cho server
;multibot add utility ANOTHER_TOKEN Bot tiện ích
```

## 📋 Lệnh quản lý

### Xem danh sách bot
```
;multibot list
```
Hiển thị tất cả bot đã cấu hình với trạng thái active/inactive.

### Kích hoạt/Tắt bot
```
;multibot toggle <tên_bot>
```
**Ví dụ:**
```
;multibot toggle backup    # Bật bot backup
;multibot toggle utility   # Tắt bot utility
```

### Xóa bot
```
;multibot remove <tên_bot>
```

## 💬 Gửi tin nhắn

### Gửi qua 1 bot cụ thể
```
;multibot send <tên_bot> <channel_id> <nội_dung>
```
**Ví dụ:**
```
;multibot send backup 123456789 Xin chào từ bot backup!
```

### Broadcast qua tất cả bot active
```
;multibot broadcast <channel_id> <nội_dung>
```
**Ví dụ:**
```
;multibot broadcast 123456789 Thông báo quan trọng từ admin!
```

## 🔒 Bảo mật

### Token Protection
- Tin nhắn chứa token sẽ bị xóa tự động
- Token được lưu trữ mã hóa trong file config
- Chỉ admin mới có quyền truy cập

### Permissions
- Chỉ Admin và Supreme Admin mới sử dụng được
- Bot cần quyền "Send Messages" trong channel đích
- Tự động kiểm tra quyền trước khi gửi

## ⚙️ Settings

### Cấu hình trong bot_config.json
```json
{
  "settings": {
    "max_concurrent_bots": 5,      // Tối đa 5 bot cùng lúc
    "message_delay": 1.0,          // Delay 1s giữa các bot
    "retry_attempts": 3,           // Thử lại 3 lần nếu lỗi
    "timeout": 30                  // Timeout 30s
  }
}
```

## 🎯 Use Cases

### 1. Thông báo quan trọng
```
;multibot broadcast 123456789 🚨 Server sẽ maintenance trong 10 phút!
```

### 2. Tạo hiệu ứng đặc biệt
```
;multibot send bot1 123456789 🎉
;multibot send bot2 123456789 🎊
;multibot send bot3 123456789 🎈
```

### 3. Backup communication
```
;multibot send backup 123456789 Main bot đang offline, tôi sẽ thay thế!
```

### 4. Role-based messaging
```
;multibot send moderator 123456789 Tin nhắn từ bot moderator
;multibot send announcer 123456789 Thông báo chính thức
```

## ❌ Troubleshooting

### Bot không gửi được tin nhắn
1. Kiểm tra bot có trong server không
2. Kiểm tra bot có quyền "Send Messages" không
3. Kiểm tra channel ID có đúng không
4. Kiểm tra token có hợp lệ không

### Token bị từ chối
1. Đảm bảo token đúng format
2. Bot phải được invite vào server
3. Token không được expired

### Rate Limiting
- Hệ thống tự động delay giữa các bot
- Nếu vẫn bị rate limit, tăng `message_delay` trong settings

## 🔄 Best Practices

### 1. Đặt tên bot có ý nghĩa
```
;multibot add announcer TOKEN Bot thông báo chính thức
;multibot add moderator TOKEN Bot quản lý
;multibot add backup TOKEN Bot dự phòng
```

### 2. Chỉ kích hoạt bot cần thiết
- Tắt bot không sử dụng để tiết kiệm resources
- Chỉ bật khi cần broadcast hoặc backup

### 3. Sử dụng broadcast cho thông báo quan trọng
- Emergency announcements
- Server-wide notifications
- Event announcements

### 4. Sử dụng single bot cho tin nhắn thường
- Casual messages
- Specific role communications
- Testing purposes

## 📊 Monitoring

### Logs
- Tất cả hoạt động được log chi tiết
- Theo dõi success/failure rate
- Monitor bot performance

### Status Tracking
- Real-time bot status (active/inactive)
- Message delivery confirmation
- Error reporting với chi tiết

## 🚀 Advanced Features

### Scheduled Messages (Future)
```
;multibot schedule 2024-12-25 12:00 broadcast 123456789 Chúc mừng Giáng sinh!
```

### Message Templates (Future)
```
;multibot template create welcome Chào mừng {user} đến với server!
;multibot template use welcome broadcast 123456789
```

### Auto-failover (Future)
- Tự động chuyển sang bot backup khi main bot offline
- Health check cho tất cả bot
- Smart load balancing

---

## 📞 Support

Nếu gặp vấn đề, liên hệ admin hoặc sử dụng:
```
;multibot help
```

**Lưu ý:** Hệ thống này tuân thủ Discord ToS và không được sử dụng để spam hay vi phạm quy tắc cộng đồng.
