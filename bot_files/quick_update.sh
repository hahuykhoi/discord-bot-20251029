#!/bin/bash
# Script update nhanh trên hosting
# Usage: ./quick_update.sh

echo "============================================================"
echo "🔄 QUICK UPDATE - Discord Bot"
echo "============================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kiểm tra nếu đang trong thư mục bot
if [ ! -f "bot_refactored.py" ]; then
    echo -e "${RED}❌ Không tìm thấy bot_refactored.py${NC}"
    echo "Vui lòng chạy script trong thư mục bot!"
    exit 1
fi

# Bước 1: Backup data
echo -e "${YELLOW}📦 Bước 1: Backup dữ liệu...${NC}"
python3 backup_data.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backup thất bại!${NC}"
    exit 1
fi
echo ""

# Bước 2: Pull code mới
echo -e "${YELLOW}📥 Bước 2: Pull code mới từ GitHub...${NC}"
git pull origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git pull thất bại!${NC}"
    echo "Có thể cần resolve conflicts hoặc kiểm tra Git config"
    exit 1
fi
echo ""

# Bước 3: Install/update dependencies (nếu có thay đổi)
if git diff HEAD@{1} HEAD -- requirements.txt | grep -q .; then
    echo -e "${YELLOW}📦 Bước 3: Cập nhật dependencies...${NC}"
    pip3 install -r requirements.txt --upgrade
    echo ""
fi

# Bước 4: Restart bot
echo -e "${YELLOW}🔄 Bước 4: Khởi động lại bot...${NC}"

# Kiểm tra xem đang dùng systemd không
if systemctl is-active --quiet discord-bot; then
    echo "Sử dụng systemd..."
    sudo systemctl restart discord-bot
    sleep 2
    
    if systemctl is-active --quiet discord-bot; then
        echo -e "${GREEN}✅ Bot đã khởi động thành công!${NC}"
    else
        echo -e "${RED}❌ Bot không khởi động được!${NC}"
        echo "Xem log: sudo journalctl -u discord-bot -n 50"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Không tìm thấy systemd service${NC}"
    echo "Vui lòng khởi động bot thủ công: python3 bot_refactored.py"
fi

echo ""
echo "============================================================"
echo -e "${GREEN}🎉 UPDATE HOÀN TẤT!${NC}"
echo "============================================================"
echo ""
echo "📋 Tiếp theo:"
echo "  1. Kiểm tra bot trong Discord"
echo "  2. Test các tính năng mới"
echo "  3. Nếu có lỗi: python3 restore_data.py"
echo ""
