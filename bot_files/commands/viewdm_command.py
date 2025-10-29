"""
ViewDM Command - Xem tin nhắn DM từ user theo ID
Chức năng: Hiển thị lịch sử tin nhắn DM của một user cụ thể
"""

import json
from pathlib import Path
from datetime import datetime

DM_LOG_PATH = Path("data/dm_log.json")

def ensure_dm_log():
    """Đảm bảo file dm_log.json tồn tại"""
    if not DM_LOG_PATH.exists():
        DM_LOG_PATH.write_text("[]", encoding="utf-8")

def read_dm_log_for(user_id: int):
    """Đọc log DM cho một user cụ thể"""
    ensure_dm_log()
    try:
        arr = json.loads(DM_LOG_PATH.read_text(encoding="utf-8") or "[]")
    except Exception:
        return []
    return [e for e in arr if int(e.get("user_id", 0)) == int(user_id)]

def read_dm_log_last(n: int = 10):
    """Đọc n tin nhắn DM cuối cùng"""
    ensure_dm_log()
    try:
        arr = json.loads(DM_LOG_PATH.read_text(encoding="utf-8") or "[]")
    except Exception:
        return []
    return arr[-n:]

async def viewdm_command(args):
    """
    CLI Command: viewdm <user_id>
    Hiển thị lịch sử DM của user
    """
    if len(args) < 1:
        print("Usage: viewdm <user_id>")
        return
    
    uid = int(args[0])
    logs = read_dm_log_for(uid)
    
    if not logs:
        print("No DM logs for user")
        return
    
    print(f"\n=== DM History for User {uid} ===")
    for e in logs[-50:]:  # Hiển thị 50 tin nhắn cuối
        timestamp = e.get('timestamp', 'Unknown')
        content = e.get('content', '')
        print(f"{timestamp} - {uid}: {content}")
    print(f"=== End of DM History ===\n")

async def viewdmlast_command(args):
    """
    CLI Command: viewdmlast [n]
    Hiển thị n tin nhắn DM cuối cùng từ tất cả users
    """
    n = int(args[0]) if args else 10
    logs = read_dm_log_last(n)
    
    if not logs:
        print("No DM logs found")
        return
    
    print(f"\n=== Last {n} DM Messages ===")
    for e in logs:
        timestamp = e.get('timestamp', 'Unknown')
        user_id = e.get('user_id', 'Unknown')
        content = e.get('content', '')
        print(f"{timestamp} - {user_id}: {content}")
    print(f"=== End of Last DMs ===\n")

# Discord Bot Command (cho sử dụng trong server)
async def discord_viewdm_command(ctx, user_id: int):
    """Discord command để xem DM logs (chỉ admin)"""
    # Kiểm tra quyền admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Chỉ admin mới có thể sử dụng lệnh này!")
        return
    
    logs = read_dm_log_for(user_id)
    if not logs:
        await ctx.send(f"Không có DM logs cho user {user_id}")
        return
    
    # Tạo embed để hiển thị đẹp hơn
    import discord
    embed = discord.Embed(
        title=f"DM History - User {user_id}",
        color=0xFFD700,
        timestamp=datetime.utcnow()
    )
    
    recent_logs = logs[-10:]  # Chỉ hiển thị 10 tin nhắn gần nhất
    for i, log in enumerate(recent_logs, 1):
        timestamp = log.get('timestamp', 'Unknown')
        content = log.get('content', '')[:100]  # Giới hạn 100 ký tự
        embed.add_field(
            name=f"Message {i}",
            value=f"**Time:** {timestamp}\n**Content:** {content}",
            inline=False
        )
    
    embed.set_footer(text="VIP Admin Bot - DM Logs")
    await ctx.send(embed=embed)
