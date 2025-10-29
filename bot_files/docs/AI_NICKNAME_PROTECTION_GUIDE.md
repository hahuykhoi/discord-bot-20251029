# 🤖 AI-Powered Admin Nickname Protection System

## 📋 Tổng quan

Hệ thống bảo vệ nickname admin đã được nâng cấp với AI để tự động phát hiện các biến thể tinh vi của tên được bảo vệ, đặc biệt là "Claude" với các ký tự Unicode đặc biệt.

## ⚡ Tính năng chính

### 🔍 AI Detection
- **Gemini AI**: Phân tích nickname để phát hiện biến thể
- **Grok AI**: Backup AI provider
- **Smart Analysis**: Phát hiện Unicode, leet speak, diacritics
- **Fallback**: Phương pháp cơ bản nếu AI không khả dụng

### 🛡️ Unicode Normalization
- Chuẩn hóa 100+ ký tự Unicode đặc biệt
- Mapping ký tự giống nhau (C, Ç, Ć, Ċ, ℂ, 𝐂...)
- Loại bỏ diacritics và chuyển về ASCII
- Regex patterns cho biến thể cơ bản

### 🎯 Phát hiện thông minh
- **Direct Match**: Kiểm tra substring truyền thống
- **AI Analysis**: Phân tích ngữ cảnh và biến thể
- **Basic Detection**: Regex patterns và normalization
- **Multi-layer**: Kết hợp nhiều phương pháp

## 📝 Cách sử dụng

### Lệnh Admin

```bash
# Thêm nickname cần bảo vệ
;protectnick add Claude

# Xem danh sách được bảo vệ
;protectnick list

# Gỡ bỏ bảo vệ
;protectnick remove Claude

# Xem hướng dẫn
;protectnick
```

### Workflow tự động

1. **User đổi nickname** → `on_member_update` event
2. **Direct check** → Kiểm tra substring truyền thống
3. **AI Analysis** → Nếu không match, gọi AI phân tích
4. **Basic fallback** → Nếu AI fail, dùng regex patterns
5. **Auto restore** → Khôi phục về nickname trước đó
6. **Notification** → Thông báo DM cho user

## 🎯 Ví dụ phát hiện

### ✅ Sẽ bị chặn:

```
Claude Sonnet 4.5 Pro    → "Claude" với thêm text
𝐂𝐥𝐚𝐮𝐝𝐞              → Unicode Mathematical Bold
𝑪𝒍𝒂𝒖𝒅𝒆              → Unicode Mathematical Italic
Ċłαυđē                   → Mixed diacritics
C|@ud3                   → Leet speak
Cl4ude                   → Numbers replacement
C l a u d e              → Spacing tricks
CIaude                   → Similar characters (I vs l)
Clâudé                   → French diacritics
```

### ❌ Sẽ được cho phép:

```
John                     → Tên khác hoàn toàn
Alice                    → Tên khác hoàn toàn
Charlie                  → Tương tự nhưng không phải Claude
Claire                   → Tương tự nhưng không phải Claude
```

## 🔧 Cấu hình AI

### Gemini AI Prompt:
```
Phân tích nickname sau và cho biết có phải là biến thể của tên "Claude" không:
Nickname: "{nickname}"

Hãy kiểm tra:
1. Có phải là "Claude" được viết bằng ký tự đặc biệt, Unicode?
2. Có phải là "Claude" với thêm số, ký tự, hoặc từ khác?
3. Có phải là cách viết khác của "Claude"?
4. Có phải là "Claude" được ngụy trang bằng ký tự đặc biệt?

Chỉ trả lời "YES" hoặc "NO".
```

### Response Processing:
- **YES** → Nickname bị chặn và khôi phục
- **NO** → Nickname được cho phép
- **Error** → Fallback sang basic detection

## 📊 Logging & Monitoring

### Log Messages:
```
INFO: Checking nickname 'Claude Sonnet 4.5 Pro' for 'Claude' variants using AI...
INFO: AI Gemini response for 'Claude Sonnet 4.5 Pro' vs 'Claude': YES
INFO: AI/Basic detection: 'Claude Sonnet 4.5 Pro' is a 'Claude' variant
INFO: Protected admin nickname: User tried to use 'Claude Sonnet 4.5 Pro' -> restored to 'OldNickname'
```

### Detection Methods:
- **"AI Detection"** → Phát hiện bằng AI
- **"Direct Match"** → Phát hiện bằng substring

## 🛠️ Technical Details

### Unicode Mapping:
```python
replacements = {
    # Ký tự giống C
    'Ç': 'C', 'ç': 'c', 'Ć': 'C', 'ć': 'c', 'ℂ': 'C', '𝐂': 'C',
    
    # Ký tự giống L  
    'Ł': 'L', 'ł': 'l', 'Ĺ': 'L', 'ĺ': 'l', 'ℒ': 'L', '𝐋': 'L',
    
    # ... và nhiều hơn nữa
}
```

### Regex Patterns:
```python
claude_patterns = [
    r'\bclaud[e]?\b',              # claude, claud
    r'\bc[l1][a@4][u][d][e3]?\b',  # c1aud3, cl@ude
    r'\bc.*l.*a.*u.*d.*e\b',       # c...l...a...u...d...e
]
```

## 🚨 Error Handling

### AI Failures:
- **Network Error** → Fallback sang basic detection
- **API Limit** → Fallback sang basic detection  
- **Invalid Response** → Fallback sang basic detection
- **No AI Available** → Chỉ dùng basic detection

### Permission Errors:
- **No Manage Nicknames** → Log warning, không thể restore
- **Role Hierarchy** → Log warning nếu bot role thấp hơn user
- **DM Blocked** → Không gửi được thông báo, chỉ log

## 📈 Performance

### Optimization:
- **Lazy AI Call** → Chỉ gọi AI khi cần thiết
- **Fast Normalization** → Dict mapping O(1)
- **Efficient Regex** → Compiled patterns
- **Early Return** → Stop ngay khi tìm thấy match

### Memory Usage:
- **Minimal Storage** → Chỉ lưu cần thiết
- **JSON Serialization** → Compact data format
- **History Limit** → Tối đa 10 entries/user

## 🔒 Security

### Access Control:
- **Admin Only** → Chỉ admin có thể quản lý
- **Role Check** → Verify permissions trước khi action
- **Input Validation** → Sanitize tất cả input

### Data Protection:
- **Safe File Operations** → Try-catch cho file I/O
- **Graceful Degradation** → Fallback khi lỗi
- **No Sensitive Data** → Không lưu thông tin nhạy cảm

## 📋 Troubleshooting

### Common Issues:

**AI không hoạt động:**
- Kiểm tra AI Commands có được khởi tạo không
- Verify API keys trong config
- Check network connectivity

**Không restore được nickname:**
- Kiểm tra bot có quyền Manage Nicknames
- Verify bot role cao hơn user role
- Check user có phải admin không (admin được bỏ qua)

**False positives:**
- Điều chỉnh regex patterns
- Cập nhật Unicode mapping
- Fine-tune AI prompt

## 🎯 Best Practices

### Setup:
1. Đảm bảo bot có quyền `Manage Nicknames`
2. Đặt bot role cao hơn user roles
3. Test với nickname thật trước khi deploy
4. Monitor logs để điều chỉnh

### Maintenance:
1. Định kỳ check AI API status
2. Update Unicode mapping khi cần
3. Review logs để tìm false positives/negatives
4. Backup protection data thường xuyên

---

## 🎉 Kết luận

Hệ thống AI-Powered Admin Nickname Protection cung cấp khả năng phát hiện biến thể nickname tinh vi và tự động, bảo vệ tên admin khỏi việc giả mạo bằng ký tự Unicode đặc biệt. Với sự kết hợp giữa AI analysis và basic detection, hệ thống đảm bảo độ chính xác cao và khả năng fallback an toàn.
