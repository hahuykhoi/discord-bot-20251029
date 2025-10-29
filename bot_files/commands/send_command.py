"""
Send Command - Gửi tin nhắn đến channel theo ID
Chức năng: Gửi tin nhắn hoặc file đến một channel cụ thể
"""

import discord
from pathlib import Path
from datetime import datetime
import logging

def append_action_log(text: str):
    """Ghi log hành động"""
    LOG_PATH = Path("actions.log")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} - {text}\n")
    except Exception:
        logging.exception("Failed to write actions.log")

async def send_command(bot, args):
    """
    CLI Command: send <channel_id> <message...>
    Gửi tin nhắn đến channel
    """
    if len(args) < 2:
        print("Usage: send <channel_id> <message...>")
        return
    
    try:
        cid = int(args[0])
        msg = " ".join(args[1:])
        
        # Lấy channel
        ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
        if not ch:
            print(f"❌ Không tìm thấy channel {cid}")
            return
        
        # Gửi tin nhắn
        await ch.send(msg)
        print(f"✅ Đã gửi tin nhắn đến channel {ch.name} ({cid})")
        append_action_log(f"CLI send to {cid}: {msg[:200]}")
        
    except ValueError:
        print("❌ Channel ID phải là số")
    except discord.Forbidden:
        print("❌ Bot không có quyền gửi tin nhắn trong channel này")
    except discord.NotFound:
        print("❌ Không tìm thấy channel")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

async def sendfile_command(bot, args):
    """
    CLI Command: sendfile <channel_id> <filepath> [caption]
    Gửi file đến channel
    """
    if len(args) < 2:
        print("Usage: sendfile <channel_id> <filepath> [caption]")
        return
    
    try:
        cid = int(args[0])
        filepath = args[1]
        caption = " ".join(args[2:]) if len(args) > 2 else None
        
        # Kiểm tra file tồn tại
        p = Path(filepath)
        if not p.exists():
            print("❌ File không tồn tại")
            return
        
        # Lấy channel
        ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
        if not ch:
            print(f"❌ Không tìm thấy channel {cid}")
            return
        
        # Gửi file
        await ch.send(content=caption or None, file=discord.File(str(p)))
        print(f"✅ Đã gửi file {filepath} đến channel {ch.name} ({cid})")
        append_action_log(f"CLI sendfile {filepath} -> {cid}")
        
    except ValueError:
        print("❌ Channel ID phải là số")
    except discord.Forbidden:
        print("❌ Bot không có quyền gửi file trong channel này")
    except discord.NotFound:
        print("❌ Không tìm thấy channel")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

# Discord Bot Command (cho sử dụng trong server)
async def discord_send_command(ctx, channel_id: int, *, message: str):
    """Discord command để gửi tin nhắn đến channel khác (chỉ admin)"""
    # Kiểm tra quyền admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Chỉ admin mới có thể sử dụng lệnh này!")
        return
    
    try:
        # Lấy channel
        target_channel = ctx.bot.get_channel(channel_id)
        if not target_channel:
            await ctx.send(f"❌ Không tìm thấy channel với ID {channel_id}")
            return
        
        # Gửi tin nhắn
        await target_channel.send(message)
        
        # Tạo embed xác nhận
        embed = discord.Embed(
            title="✅ Tin nhắn đã được gửi",
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Channel", value=f"{target_channel.mention}", inline=True)
        embed.add_field(name="Message", value=message[:100] + "..." if len(message) > 100 else message, inline=False)
        embed.set_footer(text="VIP Admin Bot")
        
        await ctx.send(embed=embed)
        append_action_log(f"Discord send command used by {ctx.author.id} to channel {channel_id}")
        
    except discord.Forbidden:
        await ctx.send("❌ Bot không có quyền gửi tin nhắn trong channel đó")
    except discord.NotFound:
        await ctx.send("❌ Không tìm thấy channel")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

async def delete_message_command(bot, args):
    """
    CLI Command: delete <channel_id> <message_id>
    Xóa tin nhắn cụ thể
    """
    if len(args) < 2:
        print("Usage: delete <channel_id> <message_id>")
        return
    
    try:
        cid = int(args[0])
        mid = int(args[1])
        
        # Lấy channel và message
        ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
        msg = await ch.fetch_message(mid)
        
        # Xóa tin nhắn
        await msg.delete()
        print(f"✅ Đã xóa tin nhắn {mid} trong channel {cid}")
        append_action_log(f"CLI deleted message {mid} in {cid}")
        
    except ValueError:
        print("❌ Channel ID và Message ID phải là số")
    except discord.Forbidden:
        print("❌ Bot không có quyền xóa tin nhắn")
    except discord.NotFound:
        print("❌ Không tìm thấy channel hoặc tin nhắn")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

async def purge_command(bot, args):
    """
    CLI Command: purge <channel_id> <limit>
    Xóa nhiều tin nhắn cùng lúc
    """
    if len(args) < 2:
        print("Usage: purge <channel_id> <limit>")
        return
    
    try:
        cid = int(args[0])
        limit = int(args[1])
        
        if limit > 100:
            print("❌ Giới hạn tối đa 100 tin nhắn")
            return
        
        # Lấy channel
        ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
        
        # Xóa tin nhắn
        deleted = await ch.purge(limit=limit)
        print(f"✅ Đã xóa {len(deleted)} tin nhắn trong channel {cid}")
        append_action_log(f"CLI purged {len(deleted)} messages in {cid}")
        
    except ValueError:
        print("❌ Channel ID và limit phải là số")
    except discord.Forbidden:
        print("❌ Bot không có quyền xóa tin nhắn")
    except discord.NotFound:
        print("❌ Không tìm thấy channel")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
