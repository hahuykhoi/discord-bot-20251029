# 🎣 Hệ Thống Câu Cá - Fishing System

## Tổng Quan
Hệ thống câu cá là một game mini hoàn chỉnh với các tính năng:
- Câu cá với nhiều loại cá khác nhau
- Hệ thống level và EXP
- Bán cá để kiếm xu
- Bảng xếp hạng câu cá
- Cooldown và chi phí hợp lý

## 🎮 Lệnh Cơ Bản

### `;cauca` / `;fishing` / `;fish`
**Mô tả:** Lệnh câu cá chính
**Chi phí:** 1,000 xu/lần
**Cooldown:** 5 phút
**Cách dùng:** `;cauca`

**Quy trình:**
1. Kiểm tra cooldown (5 phút)
2. Kiểm tra số dư (cần 1,000 xu)
3. Trừ tiền thuê dụng cụ
4. Hiệu ứng câu cá (3 giây)
5. Random cá dựa trên level
6. Thêm cá vào kho
7. Tăng EXP và kiểm tra level up

### `;sell [loại_cá] [số_lượng]`
**Mô tả:** Bán cá để lấy xu
**Cách dùng:**
- `;sell` - Xem hướng dẫn và kho cá
- `;sell all` - Bán tất cả cá
- `;sell 🐟 5` - Bán 5 con cá nhỏ
- `;sell 🦈` - Bán 1 con cá mập

### `;kho` / `;inventory` / `;khocar`
**Mô tả:** Xem kho cá của bản thân hoặc người khác
**Cách dùng:**
- `;kho` - Xem kho của mình
- `;kho @user` - Xem kho của người khác

### `;topfish` / `;bangxephangca` / `;fishleaderboard`
**Mô tả:** Bảng xếp hạng top 10 cao thủ câu cá
**Hiển thị:** Tổng cá đã câu, level, tổng xu kiếm được

## 🐟 Hệ Thống Cá

### Cá Thường (70% tỷ lệ)
| Emoji | Tên | Giá Bán | Tỷ Lệ |
|-------|-----|---------|-------|
| 🐟 | Cá Nhỏ | 500 xu | 25% |
| 🐠 | Cá Nhiệt Đới | 800 xu | 20% |
| 🎣 | Cá Cần Câu | 1,200 xu | 15% |
| 🐡 | Cá Nóc | 1,500 xu | 10% |

### Cá Hiếm (25% tỷ lệ)
| Emoji | Tên | Giá Bán | Tỷ Lệ |
|-------|-----|---------|-------|
| 🦈 | Cá Mập | 3,000 xu | 8% |
| 🐙 | Bạch Tuộc | 2,500 xu | 7% |
| 🦞 | Tôm Hùm | 4,000 xu | 5% |
| 🐋 | Cá Voi | 5,000 xu | 5% |

### Cá Huyền Thoại (5% tỷ lệ)
| Emoji | Tên | Giá Bán | Tỷ Lệ |
|-------|-----|---------|-------|
| 🐉 | Rồng Biển | 15,000 xu | 2% |
| 🧜 | Nàng Tiên Cá | 20,000 xu | 2% |
| ⭐ | Cá Sao | 25,000 xu | 1% |

## 📈 Hệ Thống Level

### Cách Tăng Level
- **Cá Thường:** +10 EXP
- **Cá Hiếm:** +25 EXP  
- **Cá Huyền Thoại:** +50 EXP
- **EXP cần thiết:** Level × 100

### Lợi Ích Level Cao
- Tăng tỷ lệ câu được cá hiếm và huyền thoại
- Mỗi level tăng +2% tỷ lệ cá hiếm (tối đa +20%)
- Hiển thị đẳng cấp trong bảng xếp hạng

## 💰 Kinh Tế Game

### Chi Phí & Thu Nhập
- **Chi phí câu cá:** 1,000 xu/lần
- **Thu nhập trung bình:** 1,500-2,000 xu/lần
- **Lợi nhuận:** ~500-1,000 xu/lần
- **ROI:** 50-100% mỗi lần câu

### Chiến Lược Kiếm Tiền
1. **Newbie (Level 1-5):** Câu đều đặn, bán tất cả
2. **Intermediate (Level 6-15):** Tích trữ cá hiếm
3. **Expert (Level 16+):** Tập trung cá huyền thoại

## 🔧 Cấu Hình Hệ Thống

### File Cấu Hình
- **Đường dẫn:** `data/fishing_data.json`
- **Cấu trúc:** User ID → Data object
- **Backup:** Tự động lưu sau mỗi thao tác

### Tham Số Có Thể Điều Chỉnh
```python
FISHING_COOLDOWN = 300      # 5 phút
FISHING_COST = 1000         # 1,000 xu
MAX_LEVEL_BONUS = 20        # +20% tối đa
EXP_PER_LEVEL = 100         # 100 EXP/level
```

## 📊 Thống Kê Tracking

### Dữ Liệu User
- `fish_inventory`: Kho cá hiện tại
- `total_fished`: Tổng cá đã câu
- `total_sold`: Tổng cá đã bán
- `total_earned`: Tổng xu kiếm được
- `fishing_level`: Level hiện tại
- `fishing_exp`: EXP hiện tại
- `last_fishing_time`: Lần câu cuối

### Analytics
- Tỷ lệ cá theo độ hiếm
- Hiệu quả kinh tế theo level
- Thời gian chơi trung bình
- Top players theo nhiều tiêu chí

## 🎯 Tích Hợp Với Bot

### Menu Integration
- Thêm vào Game Menu (`;menu`)
- Section riêng "🎣 Fishing System"
- Quick access commands

### Shared Wallet Integration
- Sử dụng `SharedWallet` cho giao dịch
- Tương thích với tất cả games khác
- Tracking balance real-time

### Permission System
- Không cần quyền đặc biệt
- Tất cả user đều có thể chơi
- Admin có thể xem stats của mọi người

## 🚀 Tính Năng Nâng Cao

### Có Thể Thêm Sau
1. **Fishing Competitions:** Thi đấu theo tuần/tháng
2. **Fish Trading:** Trao đổi cá giữa users
3. **Fishing Gear:** Dụng cụ câu cá đặc biệt
4. **Seasonal Events:** Cá đặc biệt theo mùa
5. **Fishing Locations:** Địa điểm câu khác nhau
6. **Fish Recipes:** Chế biến cá thành món ăn
7. **Aquarium System:** Nuôi cá cảnh
8. **Fishing Achievements:** Hệ thống thành tựu

## 🐛 Troubleshooting

### Lỗi Thường Gặp
1. **"Không đủ tiền":** Cần ít nhất 1,000 xu
2. **"Cooldown":** Chờ 5 phút giữa các lần câu
3. **"Không có cá":** Kho trống, cần câu cá trước
4. **"Cá không tồn tại":** Sai tên cá khi bán

### Debug Commands
```python
# Xem raw data
fishing.fishing_data[str(user_id)]

# Reset user data
del fishing.fishing_data[str(user_id)]
fishing.save_fishing_data()

# Force level up
user_data['fishing_exp'] = 99
user_data['fishing_level'] = 10
```

## 📝 Changelog

### Version 1.0 (Initial Release)
- ✅ Basic fishing mechanics
- ✅ 11 types of fish with rarity system
- ✅ Level and EXP system
- ✅ Sell system with inventory management
- ✅ Leaderboard system
- ✅ Integration with SharedWallet
- ✅ Cooldown and cost balancing
- ✅ Full menu integration

### Planned Updates
- 🔄 Fishing competitions
- 🔄 More fish varieties
- 🔄 Fishing gear system
- 🔄 Achievement system

---

**Tác giả:** Bot Development Team  
**Ngày tạo:** 2025-10-11  
**Version:** 1.0  
**Status:** ✅ Production Ready
