# Discord Auto-Reply Bot

Bot tự động phản hồi tin nhắn riêng (DM) trên Discord với hệ thống cooldown thông minh và cấu hình linh hoạt.

## 🚀 Tính năng

- **Auto-Reply DM**: Tự động phản hồi khi có ai đó gửi tin nhắn riêng cho bạn
- **Cooldown Protection**: Hạn chế spam với cooldown có thể tùy chỉnh (mặc định 1 phút)
- **Cấu hình đơn giản**: Chỉ cần token account và có thể tùy chỉnh nội dung phản hồi
- **Logging**: Ghi log chi tiết để theo dõi hoạt động của bot
- **Quản lý thông minh**: Bật/tắt auto-reply, xóa cooldown, xem thống kê

## 📋 Yêu cầu

- Python 3.7+
- Discord account (không phải bot account)
- Các thư viện trong `requirements.txt`

## 🛠️ Cài đặt

1. **Clone hoặc tải về project**
   ```bash
   git clone <repository-url>
   cd auto-reply-discord
   ```

2. **Cài đặt dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Lấy token Discord của bạn**
   - Mở Discord trên web browser
   - Nhấn F12 để mở Developer Tools
   - Vào tab Network
   - Gửi một tin nhắn bất kỳ
   - Tìm request có chứa "authorization" trong header
   - Copy token (bỏ "Bearer " ở đầu nếu có)

4. **Cấu hình bot**
   - Chạy bot lần đầu để tạo file `config.json`
   - Mở `config.json` và thêm token của bạn
   - Tùy chỉnh tin nhắn auto-reply nếu muốn

## 🚀 Sử dụng

### Chạy bot
```bash
python auto.py
```

### Cấu hình trong config.json

```json
{
    "token": "YOUR_DISCORD_TOKEN_HERE",
    "auto_reply_message": "Xin chào! Tôi hiện tại không có mặt. Tôi sẽ phản hồi bạn sớm nhất có thể. Cảm ơn bạn đã liên hệ!",
    "cooldown_minutes": 1,
    "enabled": true,
    "custom_messages": {
        "default": "Xin chào! Tôi hiện tại không có mặt. Tôi sẽ phản hồi bạn sớm nhất có thể. Cảm ơn bạn đã liên hệ!",
        "busy": "Tôi hiện đang bận. Sẽ liên hệ lại với bạn sau.",
        "away": "Tôi hiện không có mặt. Vui lòng để lại tin nhắn."
    }
}
```

### Các tham số cấu hình

- `token`: Token Discord của bạn (bắt buộc)
- `auto_reply_message`: Tin nhắn tự động phản hồi
- `cooldown_minutes`: Thời gian cooldown tính bằng phút (mặc định: 1)
- `enabled`: Bật/tắt auto-reply (true/false)
- `custom_messages`: Các tin nhắn tùy chỉnh cho các tình huống khác nhau

## 📊 Tính năng nâng cao

### Quản lý bot trong code

```python
from auto import AutoReplyBot

# Tạo instance bot
bot = AutoReplyBot()

# Bật/tắt auto-reply
bot.toggle_auto_reply()

# Cập nhật cấu hình
bot.update_config(
    cooldown_minutes=5,
    auto_reply_message="Tin nhắn mới"
)

# Xóa tất cả cooldown
bot.clear_cooldowns()

# Xem thống kê
stats = bot.get_stats()
print(stats)
```

### Logging

Bot tự động ghi log vào:
- Console (hiển thị trực tiếp)
- File `auto_reply.log` (lưu trữ lâu dài)

Thông tin log bao gồm:
- Thời gian đăng nhập
- Tin nhắn được gửi/nhận
- Trạng thái cooldown
- Lỗi và cảnh báo

## 🔒 Bảo mật

- **Không chia sẻ token**: Token Discord của bạn rất quan trọng, không chia sẻ với ai
- **Sử dụng user token**: Bot này sử dụng user token, không phải bot token
- **Tuân thủ ToS**: Sử dụng có trách nhiệm và tuân thủ Terms of Service của Discord

## ⚠️ Lưu ý quan trọng

1. **User Token vs Bot Token**: Bot này sử dụng token của tài khoản user, không phải bot token
2. **Rate Limiting**: Discord có giới hạn về số lượng tin nhắn, bot đã tích hợp cooldown để tránh spam
3. **Tự động phản hồi**: Chỉ phản hồi tin nhắn riêng (DM), không phản hồi trong server
4. **Backup**: Nên backup file `config.json` và `auto_reply.log` định kỳ

## 🐛 Troubleshooting

### Bot không hoạt động
- Kiểm tra token có đúng không
- Đảm bảo tài khoản Discord đang online
- Xem log để tìm lỗi cụ thể

### Không nhận được tin nhắn auto-reply
- Kiểm tra `enabled` trong config có là `true` không
- Xem có đang trong thời gian cooldown không
- Kiểm tra log để xem bot có nhận tin nhắn không

### Lỗi token
- Token có thể hết hạn, lấy token mới
- Đảm bảo không có khoảng trắng thừa trong token
- Token phải là user token, không phải bot token

## 📝 Changelog

### v1.0.0
- Tính năng auto-reply DM cơ bản
- Hệ thống cooldown protection
- Cấu hình linh hoạt qua JSON
- Logging chi tiết
- Quản lý thống kê

## 📄 License

Dự án này được phát hành dưới MIT License. Xem file LICENSE để biết thêm chi tiết.

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng:
1. Fork project
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📞 Hỗ trợ

Nếu gặp vấn đề hoặc có câu hỏi, vui lòng tạo issue trên GitHub hoặc liên hệ trực tiếp.
