import json
import os
import logging
from datetime import datetime
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class SharedWallet:
    """Hệ thống ví tiền chung cho tất cả games"""
    
    def __init__(self):
        self.wallet_file = "data/shared_wallet.json"
        self.starting_balance = 1000  # Số dư ban đầu
        self.data = self.load_wallet_data()
        self._file_watch_task = None
        self._last_modified = None
        self._is_watching = False
    
    def load_wallet_data(self):
        """Load dữ liệu ví từ file"""
        try:
            if os.path.exists(self.wallet_file):
                with open(self.wallet_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Lỗi khi load wallet data: {e}")
            return {}
    
    def save_wallet_data(self):
        """Lưu dữ liệu ví vào file"""
        try:
            with open(self.wallet_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi save wallet data: {e}")
    
    def get_balance(self, user_id):
        """Lấy số dư của user"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            # Tạo tài khoản mới với số dư ban đầu
            self.data[user_id_str] = {
                'balance': self.starting_balance,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self.save_wallet_data()
        
        return self.data[user_id_str]['balance']
    
    def set_balance(self, user_id, amount):
        """Set số dư cho user"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            self.data[user_id_str] = {
                'balance': amount,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        else:
            self.data[user_id_str]['balance'] = amount
            self.data[user_id_str]['last_updated'] = datetime.now().isoformat()
        
        self.save_wallet_data()
    
    def add_balance(self, user_id, amount):
        """Thêm tiền vào ví"""
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount
        self.set_balance(user_id, new_balance)
        return new_balance
    
    def subtract_balance(self, user_id, amount):
        """Trừ tiền khỏi ví"""
        current_balance = self.get_balance(user_id)
        new_balance = current_balance - amount
        
        # Không cho phép số dư âm
        if new_balance < 0:
            logger.warning(f"Attempt to subtract {amount} from user {user_id} with balance {current_balance} would result in negative balance")
            new_balance = 0
        
        self.set_balance(user_id, new_balance)
        return new_balance
    
    def has_sufficient_balance(self, user_id, amount):
        """Kiểm tra có đủ tiền không"""
        return self.get_balance(user_id) >= amount
    
    def parse_bet_amount(self, user_id, amount_str):
        """
        Parse số tiền cược, hỗ trợ 'all' và auto-adjust
        
        Args:
            user_id: ID người dùng
            amount_str: Chuỗi số tiền ("100", "all", "999999")
            
        Returns:
            tuple: (bet_amount, is_adjusted, message)
                - bet_amount: Số tiền sau khi parse
                - is_adjusted: True nếu đã điều chỉnh
                - message: Thông báo (nếu có)
        """
        try:
            # Kiểm tra "all"
            if amount_str.lower() == 'all':
                balance = self.get_balance(user_id)
                if balance <= 0:
                    return 0, False, "❌ Bạn không có tiền để đặt cược!"
                return balance, False, f"✅ Đặt cược toàn bộ: {balance:,} xu"
            
            # Parse số
            bet_amount = int(amount_str.replace(',', '').replace('.', ''))
            
            if bet_amount <= 0:
                return 0, False, "❌ Số tiền phải lớn hơn 0!"
            
            # Kiểm tra số dư và auto-adjust
            balance = self.get_balance(user_id)
            if bet_amount > balance:
                if balance <= 0:
                    return 0, False, "❌ Bạn không có tiền để đặt cược!"
                return balance, True, f"⚠️ Đã điều chỉnh từ {bet_amount:,} xuống {balance:,} xu (số dư hiện tại)"
            
            return bet_amount, False, None
            
        except ValueError:
            return 0, False, "❌ Số tiền không hợp lệ! Sử dụng số hoặc 'all'"
    
    def transfer_money(self, from_user_id, to_user_id, amount):
        """Chuyển tiền giữa 2 user"""
        if not self.has_sufficient_balance(from_user_id, amount):
            return False, "Không đủ tiền"
        
        self.subtract_balance(from_user_id, amount)
        self.add_balance(to_user_id, amount)
        return True, "Chuyển tiền thành công"
    
    def reset_all_balances(self):
        """Reset tất cả số dư về 0 (dành cho admin)"""
        reset_count = 0
        for user_id in self.data:
            old_balance = self.data[user_id]['balance']
            if old_balance != 0:
                self.data[user_id]['balance'] = 0
                self.data[user_id]['last_updated'] = datetime.now().isoformat()
                reset_count += 1
        
        self.save_wallet_data()
        return reset_count
    
    def get_all_users_with_money(self):
        """Lấy danh sách tất cả user có tiền"""
        users_with_money = []
        for user_id, data in self.data.items():
            if data['balance'] > 0:
                users_with_money.append({
                    'user_id': int(user_id),
                    'balance': data['balance']
                })
        
        # Sort theo số dư giảm dần
        users_with_money.sort(key=lambda x: x['balance'], reverse=True)
        return users_with_money
    
    def get_total_money_in_system(self):
        """Tính tổng số tiền trong hệ thống"""
        total = 0
        for user_data in self.data.values():
            total += user_data['balance']
        return total
    
    def get_user_count(self):
        """Đếm số user trong hệ thống"""
        return len(self.data)
    
    def reload_data(self):
        """Reload dữ liệu từ file (manual refresh)"""
        try:
            old_count = len(self.data)
            old_total = self.get_total_money_in_system()
            
            self.data = self.load_wallet_data()
            
            new_count = len(self.data)
            new_total = self.get_total_money_in_system()
            
            logger.info(f"Reloaded wallet data: {old_count} -> {new_count} users, {old_total} -> {new_total} coins")
            return True, {
                'old_count': old_count,
                'new_count': new_count,
                'old_total': old_total,
                'new_total': new_total
            }
        except Exception as e:
            logger.error(f"Error reloading wallet data: {e}")
            return False, str(e)
    
    def get_file_modified_time(self):
        """Lấy thời gian file được sửa đổi lần cuối"""
        try:
            if os.path.exists(self.wallet_file):
                return os.path.getmtime(self.wallet_file)
            return None
        except Exception as e:
            logger.error(f"Error getting file modified time: {e}")
            return None
    
    async def start_file_watching(self, check_interval=5):
        """Bắt đầu theo dõi file thay đổi"""
        if self._is_watching:
            logger.warning("File watching already started")
            return
        
        self._is_watching = True
        self._last_modified = self.get_file_modified_time()
        
        logger.info(f"Started watching {self.wallet_file} for changes (check every {check_interval}s)")
        
        while self._is_watching:
            try:
                await asyncio.sleep(check_interval)
                
                current_modified = self.get_file_modified_time()
                
                if current_modified and self._last_modified and current_modified != self._last_modified:
                    logger.info(f"Detected change in {self.wallet_file}, reloading...")
                    success, result = self.reload_data()
                    
                    if success:
                        logger.info(f"Auto-reloaded: {result['new_count']} users, {result['new_total']} total coins")
                    else:
                        logger.error(f"Failed to auto-reload: {result}")
                    
                    self._last_modified = current_modified
                
            except asyncio.CancelledError:
                logger.info("File watching task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in file watching loop: {e}")
                await asyncio.sleep(check_interval)
        
        self._is_watching = False
    
    def stop_file_watching(self):
        """Dừng theo dõi file"""
        if self._file_watch_task and not self._file_watch_task.done():
            self._file_watch_task.cancel()
            self._is_watching = False
            logger.info("Stopped file watching")

# Global instance
shared_wallet = SharedWallet()
