"""
DM Command - Gửi tin nhắn riêng đến user theo ID
Chức năng: Gửi Direct Message đến một user cụ thể
"""

import discord
import json
from pathlib import Path
from datetime import datetime
import logging

DM_LOG_PATH = Path("dm_log.json")

def ensure_dm_log():
    """Đảm bảo file dm_log.json tồn tại"""
    if not DM_LOG_PATH.exists():
        DM_LOG_PATH.write_text("[]", encoding="utf-8")

def append_dm_log(user_id: int, content: str):
    """Ghi log DM đã gửi"""
    ensure_dm_log()
    try:
        arr = json.loads(DM_LOG_PATH.read_text(encoding="utf-8") or "[]")
    except Exception:
        arr = []
    
    arr.append({
        "user_id": int(user_id), 
        "content": content, 
        "timestamp": datetime.utcnow().isoformat(),
        "type": "sent"  # Đánh dấu là tin nhắn đã gửi
    })
    
    DM_LOG_PATH.write_text(json.dumps(arr, ensure_ascii=False, indent=2), encoding="utf-8")

def append_action_log(text: str):
    """Ghi log hành động"""
    LOG_PATH = Path("actions.log")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} - {text}\n")
    except Exception:
        logging.exception("Failed to write actions.log")

async def dm_command(bot, args):
    """
    CLI Command: dm <user_id> <message...>
    Gửi DM đến user
    """
    if len(args) < 2:
        print("Usage: dm <user_id> <message...>")
        return
    
    try:
        uid = int(args[0])
        msg = " ".join(args[1:])
        
        # Lấy user
        user = await bot.fetch_user(uid)
        if not user:
            print(f"❌ Không tìm thấy user {uid}")
            return
        
        # Gửi DM
        await user.send(msg)
        print(f"✅ Đã gửi DM đến {user.name} ({uid})")
        
        # Ghi log
        append_dm_log(uid, msg)
        append_action_log(f"CLI sent DM to {uid}: {msg[:200]}")
        
    except ValueError:
        print("❌ User ID phải là số")
    except discord.Forbidden:
        print("❌ Không thể gửi DM đến user này (có thể đã chặn bot hoặc tắt DM)")
    except discord.NotFound:
        print("❌ Không tìm thấy user")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

# Discord Bot Command (cho sử dụng trong server)
async def discord_dm_command(ctx, user_id: int, *, message: str):
    """Discord command để gửi DM (chỉ admin)"""
    # Kiểm tra quyền admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Chỉ admin mới có thể sử dụng lệnh này!")
        return
    
    try:
        # Lấy user
        user = await ctx.bot.fetch_user(user_id)
        if not user:
            await ctx.send(f"❌ Không tìm thấy user với ID {user_id}")
            return
        
        # Gửi DM
        await user.send(message)
        
        # Tạo embed xác nhận
        embed = discord.Embed(
            title="✅ DM đã được gửi",
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Người nhận", value=f"{user.name}#{user.discriminator}", inline=True)
        embed.add_field(name="User ID", value=str(user_id), inline=True)
        embed.add_field(name="Tin nhắn", value=message[:100] + "..." if len(message) > 100 else message, inline=False)
        embed.set_footer(text="VIP Admin Bot")
        
        await ctx.send(embed=embed)
        
        # Ghi log
        append_dm_log(user_id, message)
        append_action_log(f"Discord DM command used by {ctx.author.id} to user {user_id}")
        
    except discord.Forbidden:
        await ctx.send("❌ Không thể gửi DM đến user này (có thể đã chặn bot hoặc tắt DM)")
    except discord.NotFound:
        await ctx.send("❌ Không tìm thấy user")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

async def dm_with_embed_command(bot, args):
    """
    CLI Command: dmembed <user_id> <title> <description>
    Gửi DM với embed đẹp hơn
    """
    if len(args) < 3:
        print("Usage: dmembed <user_id> <title> <description>")
        return
    
    try:
        uid = int(args[0])
        title = args[1]
        description = " ".join(args[2:])
        
        # Lấy user
        user = await bot.fetch_user(uid)
        if not user:
            print(f"❌ Không tìm thấy user {uid}")
            return
        
        # Tạo embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=0xFFD700,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="VIP Admin Bot")
        
        # Gửi DM với embed
        await user.send(embed=embed)
        print(f"✅ Đã gửi DM embed đến {user.name} ({uid})")
        
        # Ghi log
        append_dm_log(uid, f"[EMBED] {title}: {description}")
        append_action_log(f"CLI sent DM embed to {uid}: {title}")
        
    except ValueError:
        print("❌ User ID phải là số")
    except discord.Forbidden:
        print("❌ Không thể gửi DM đến user này")
    except discord.NotFound:
        print("❌ Không tìm thấy user")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

async def dm_file_command(bot, args):
    """
    CLI Command: dmfile <user_id> <filepath> [caption]
    Gửi file qua DM
    """
    if len(args) < 2:
        print("Usage: dmfile <user_id> <filepath> [caption]")
        return
    
    try:
        uid = int(args[0])
        filepath = args[1]
        caption = " ".join(args[2:]) if len(args) > 2 else None
        
        # Kiểm tra file
        p = Path(filepath)
        if not p.exists():
            print("❌ File không tồn tại")
            return
        
        # Lấy user
        user = await bot.fetch_user(uid)
        if not user:
            print(f"❌ Không tìm thấy user {uid}")
            return
        
        # Gửi file
        await user.send(content=caption, file=discord.File(str(p)))
        print(f"✅ Đã gửi file {filepath} đến {user.name} ({uid})")
        
        # Ghi log
        append_dm_log(uid, f"[FILE] {filepath} - {caption or 'No caption'}")
        append_action_log(f"CLI sent DM file to {uid}: {filepath}")
        
    except ValueError:
        print("❌ User ID phải là số")
    except discord.Forbidden:
        print("❌ Không thể gửi DM đến user này")
    except discord.NotFound:
        print("❌ Không tìm thấy user")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
